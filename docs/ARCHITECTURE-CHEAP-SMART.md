# Architecture: Cheap + Smart Database Check

## Goal

Telegram Excel upload -> **CSV** -> **rule engine (0 token)** -> Obsidian-like vault memory -> AI only if needed -> corrected XLSX/CSV back.

GodMode3 / 50-model racing is **not** used. Too expensive, wrong for CRM validation.

## Pipeline

```text
Telegram (.xlsx)
   │
   ▼
Convert to CSV                 ← cheaper, smaller, deterministic
   │
   ▼
Rule Engine (Pandera)          ← 0 token, finds/fixes most errors
   │
   ├─ known pattern? ─────────► recall from Obsidian vault (0 token)
   │
   ├─ ambiguous? ─────────────► small model (Gemini Flash / GPT-4o-mini)
   │
   ▼
Write result notes into vault  ← markdown memory like Obsidian
   │
   ▼
Return corrected file + report to Telegram
```

## Why CSV?

- Less bytes than xlsx for AI/context
- Easier for n8n Code / pandas / Pandera
- Faster chunking
- Lower token cost when AI is required

User still uploads `.xlsx`. Conversion is automatic.

## Obsidian-like vault

Folder of markdown notes (human readable, git-friendly):

```text
vault/
  rules/           # validation rules as .md
  customers/       # known customer quirks
  patterns/        # recurring error fixes
  runs/            # each validation run log
  MEMORY.md        # index
```

Tools/projects:
- https://github.com/YuNaga224/obsidian-memory-mcp
- https://github.com/honam867/obsidian-memory-layer-mcp
- https://github.com/jodfie/Obsidian-Memory

## Zero-token validation stack

| Layer | Tool | Tokens |
|------|------|--------|
| Schema / columns / dtypes | Pandera | 0 |
| Expectations / reports | Great Expectations (optional) | 0 |
| Known fix patterns | Vault markdown lookup | 0 |
| Ambiguous text cleanup | Small LLM only | low |

Pandera: https://github.com/unionai-oss/pandera  
Great Expectations: https://github.com/great-expectations/great_expectations

## What replaces GodMode3

| Need | Use instead |
|------|-------------|
| Multi-model race | No — expensive |
| Better accuracy | Rule engine + vault patterns |
| Memory | Obsidian markdown vault |
| Cheap AI fallback | One small model, only on hard rows |

## Integration with existing V2

Keep `Telegram Database Validator Bot V2` as orchestrator, but change order:

1. Convert upload to CSV first
2. Run rule-engine service (`POST /rules/validate`)
3. Only send remaining hard rows to Appointment/Verifier AI
4. Save run summary into `vault/runs/`
5. Return corrected XLSX + report

Expected effect:
- fewer wrong AI guesses
- much lower token spend
- many files finish with **0 LLM calls**
