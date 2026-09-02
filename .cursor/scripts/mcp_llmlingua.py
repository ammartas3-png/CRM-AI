"""
mcp_llmlingua.py
================
A production-ready MCP server that exposes LLMLingua-2 prompt compression
as a tool Cursor (or any MCP client) can call automatically.
"""

from __future__ import annotations

import logging
import sys
import os
from typing import Optional

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ---------------------------------------------------------------------------
# Logging — file-based to avoid Cursor misreading stderr as errors
# ---------------------------------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "mcp_llmlingua.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)
log = logging.getLogger("mcp-llmlingua")

# ---------------------------------------------------------------------------
# FastMCP import
# ---------------------------------------------------------------------------
try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    log.critical("FastMCP not found. Run: pip install 'mcp[cli]'  (mcp >= 1.0)")
    raise SystemExit(1) from exc

# ---------------------------------------------------------------------------
# Server bootstrap
# ---------------------------------------------------------------------------
mcp = FastMCP(name="llmlingua-compressor")

# ---------------------------------------------------------------------------
# Eager compressor initialisation
# Loaded ONCE at startup — before mcp.run() — so no lazy-load race condition
# can occur when Cursor sends ListToolsRequest during the first CallToolRequest.
# ---------------------------------------------------------------------------
_COMPRESSOR = None


def _init_compressor() -> None:
    """
    Initialise PromptCompressor at server startup.
    Must be called before mcp.run().
    """
    global _COMPRESSOR

    try:
        from llmlingua import PromptCompressor
    except ImportError as exc:
        log.critical("llmlingua not found. Run: pip install llmlingua")
        raise SystemExit(1) from exc

    import torch

    if torch.cuda.is_available():
        device_map = "cuda"
        log.info("LLMLingua-2 — using CUDA GPU.")
    elif torch.backends.mps.is_available():
        device_map = "cpu"
        log.info("LLMLingua-2 — MPS detected but falling back to CPU for stability.")
    else:
        device_map = "cpu"
        log.info("LLMLingua-2 — no GPU found, running on CPU.")

    log.info("Loading microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank …")
    log.info("First load downloads ~700 MB; subsequent starts use the local cache.")

    _COMPRESSOR = PromptCompressor(
        model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
        use_llmlingua2=True,
        device_map=device_map,
    )

    log.info("LLMLingua-2 compressor ready.")


def _get_compressor():
    """Return the already-initialised compressor, or raise clearly if missing."""
    if _COMPRESSOR is None:
        raise RuntimeError(
            "Compressor was not initialised at startup. "
            "This is a bug — _init_compressor() must be called before mcp.run()."
        )
    return _COMPRESSOR


# ---------------------------------------------------------------------------
# MCP Tool
# ---------------------------------------------------------------------------
@mcp.tool()
def optimize_context(
    context: str,
    target_rate: float = 0.5,
    additional_tokens_to_keep: Optional[list[str]] = None,
) -> str:
    """
    Compress *context* to approximately *target_rate* of its original token
    length using LLMLingua-2, while preserving code-critical tokens.

    Parameters
    ----------
    context : str
        The raw text / code / documentation to compress.
    target_rate : float
        Fraction of tokens to keep (0.0 – 1.0).  Default 0.5 keeps ~50 %.
        Use 0.3 for aggressive compression, 0.7 for light compression.
    additional_tokens_to_keep : list[str] | None
        Extra tokens that must never be dropped. Added on top of the
        built-in code-safety list.

    Returns
    -------
    str
        The compressed context, ready to be used as-is.
    """
    if not context or not context.strip():
        return context

    # Clamp target_rate to a safe range
    target_rate = max(0.1, min(0.95, target_rate))

    # Tokens that are structurally critical for code / JSON / YAML
    force_keep = [
        "\n", "\t",
        "{", "}", "[", "]", "(", ")", ":",
        ";", ",", ".",
        "->", "=>",
        "def ", "class ", "import ", "from ",
        "return", "async ", "await ",
        "function", "const ", "let ", "var ",
        "if ", "else", "for ", "while ",
        "try", "except", "finally", "raise",
        "and", "or", "not", "True", "False", "None",
        "=", "==", "!=", "<", ">", "<=", ">=",
        "+", "-", "*", "/", "%", "**",
        "#", "//", "/*", "*/", '"""', "'''",
        "dict", "list", "set", "tuple",
    ]

    if additional_tokens_to_keep:
        force_keep.extend(additional_tokens_to_keep)

    compressor = _get_compressor()

    log.info(
        "Compressing context: %d chars → target_rate=%.2f",
        len(context),
        target_rate,
    )

    try:
        result = compressor.compress_prompt(
            context,
            rate=target_rate,
            force_tokens=force_keep,
            drop_consecutive=False,
        )

        compressed: str = result.get("compressed_prompt", context)

        original_tokens = result.get("origin_tokens", "?")
        compressed_tokens = result.get("compressed_tokens", "?")
        log.info(
            "Compression done: %s → %s tokens (saved %.1f %%)",
            original_tokens,
            compressed_tokens,
            (1 - target_rate) * 100,
        )

        return compressed

    except Exception as exc:  # noqa: BLE001
        # Never crash Cursor — return the original context on failure
        log.error("Compression failed (%s); returning original context.", exc)
        return context


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    log.info("Starting LLMLingua MCP server …")

    # -----------------------------------------------------------------------
    # CRITICAL: Initialise the compressor BEFORE handing off to FastMCP.
    # Lazy loading inside the tool handler races with Cursor's ListToolsRequest
    # bursts, causing anyio.BrokenResourceError → server crash.
    # -----------------------------------------------------------------------
    _init_compressor()

    log.info("Server ready. Handing off to FastMCP …")

    try:
        mcp.run()
    except Exception as exc:
        exc_type = type(exc).__name__
        # ExceptionGroup (Python 3.11+): unwrap and inspect each child
        if exc_type == "ExceptionGroup":
            for child in exc.exceptions:  # type: ignore[attr-defined]
                if type(child).__name__ == "BrokenResourceError":
                    log.info("Client disconnected (BrokenResourceError) — shutting down cleanly.")
                else:
                    log.error("Unhandled server error: %s", child, exc_info=child)
        # Plain BrokenResourceError (older anyio / single exception)
        elif exc_type == "BrokenResourceError":
            log.info("Client disconnected — shutting down cleanly.")
        else:
            log.error("Unhandled server error: %s", exc, exc_info=True)
            raise