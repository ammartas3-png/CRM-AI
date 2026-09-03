"""
CRM lead status classifier — zero-token rules approved by business owner.

Approved decisions:
1. currently busy (no real talk) → No Answer 1-5
2. invalid mail + phone NA → keep No Answer (mail does not change status)
3. first-time wrong number → Denied Registration
4. Call Again → No Answer only after 5 distinct NA days
5. no money + concrete callback → Call Again
6. CRM Potential → Manual Check
7. Decline → Manual Check (never auto-change)
8. Recall + newer concrete callback → Call Again
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NA_WORDS = {
    "na", "n", "a", "vm", "voice", "mail", "fw", "fwd", "forwarded", "to",
    "ringing", "ring", "rings", "rang", "rng", "long", "only", "short", "busy",
    "line", "number", "is", "unavailable", "switched", "off", "call", "called",
    "failed", "network", "error", "rej", "reject", "rejected", "rejecting",
    "the", "no", "nr", "dvm", "dnd", "disconnected", "unreachable", "then",
    "pu", "hu", "db", "navm", "nadb", "drej", "fvm", "cnbr", "ndt", "currently",
}


def fold(text: str) -> str:
    t = str(text or "").lower()
    for a, b in (("ı", "i"), ("ş", "s"), ("ğ", "g"), ("ç", "c"), ("ö", "o"), ("ü", "u")):
        t = t.replace(a, b)
    t = re.sub(r"[''`\"]", "", t)
    t = re.sub(r"[;,.\|]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def status_canon(s: str) -> str:
    x = fold(s)
    if not x:
        return ""
    if "no answer" in x and ("5 up" in x or "5up" in x):
        return "no answer 5 up"
    if "no answer" in x:
        return "no answer 1-5"
    if "no potential" in x:
        return "no potential"
    if "wrong number" in x or "wrong email" in x:
        return "wrong number or email"
    if "denied reg" in x:
        return "denied registration"
    if "no interest" in x:
        return "no interest"
    if "no language" in x:
        return "no language"
    if "call again" in x:
        return "call again"
    if "recall" in x:
        return "recall"
    if "decline" in x:
        return "decline"
    if x in {"duplicate", "dnc", "potential", "new", "in progress"}:
        return x
    return x


def is_system_comment(text: str) -> bool:
    return bool(re.match(r"^(email |email\b|missed call email|in progress|new$|duplicate)", str(text or "").strip(), re.I))


def is_na_only_line(text: str) -> bool:
    t = fold(text)
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\b\d+(st|nd|rd|th)\b", " ", t)
    t = re.sub(r"\b[a-z]\d+\b", " ", t)
    t = re.sub(r"\b(x\d+|\d+x|xx\d+|v\d+|\d+)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return False
    return all(tok in NA_WORDS for tok in t.split())


def extract_parts(raw: str) -> list[dict[str, str]]:
    raw = str(raw or "")
    rough = raw.split("||") if "||" in raw else raw.splitlines()
    segments: list[str] = []
    for piece in rough:
        p = piece.strip()
        if not p:
            continue
        if segments and not re.search(r"\d{4}-\d{2}-\d{2}", p) and not re.match(r"^(email\b|in progress)", p, re.I):
            segments[-1] = segments[-1] + " " + p
        else:
            segments.append(p)

    out: list[dict[str, str]] = []
    for part in segments:
        dm = re.search(r"(\d{4}-\d{2}-\d{2})", part)
        if part.count("|") >= 2:
            pieces = [x.strip() for x in part.split("|") if x.strip()]
            body = " ".join(pieces[2:]) if len(pieces) >= 3 else part
        else:
            body = re.sub(r"^\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}\s*[-–—]?\s*", "", part).strip() or part
        out.append({"raw": part, "date": dm.group(1) if dm else "", "text": body, "norm": fold(body)})

    def ts(p: dict[str, str]) -> float:
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})", p["raw"])
        if m:
            return datetime(int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), tzinfo=timezone.utc).timestamp()
        if p["date"]:
            return datetime.fromisoformat(p["date"] + "T12:00:00+00:00").timestamp()
        return 0.0

    return sorted(out, key=ts, reverse=True)


def na_streak_days(parts: list[dict[str, str]]) -> int:
    non_sys = [p for p in parts if not is_system_comment(p["text"])]
    streak: set[str] = set()
    for p in non_sys:
        if is_na_only_line(p["text"]):
            if p["date"]:
                streak.add(p["date"])
        else:
            break
    return len(streak)


CALLBACK_RE = re.compile(
    r"\b(cb\b|cbk\b|clbk\b|cback|callback|cb tmrw|cb tomorrow|call me (back|after|later|on|tomorrow)|"
    r"call (back|after|again)|will call|asked? (me )?to call|call after|after \d+\s?(am|pm|hour)|"
    r"tomorrow|tmrw|2moro|today|tonight|next week|\b(mon|tue|wed|thu|fri|sat|sun)(day)?\b)",
    re.I,
)
# Agent notes like "didn't give me time to talk" / mockery must NOT count as customer callback.
CALLBACK_FALSE_RE = re.compile(
    r"\b(didnt give (me |us |him |her )?(any |some )?(time|a chance)|"
    r"did not give (me |us |him |her )?(any |some )?(time|a chance)|"
    r"no time to talk|didnt let (me |us )?(speak|talk)|did not let (me |us )?(speak|talk)|"
    r"playing around|laughing|mumbling|uneducated|wasting (my |our )?time|"
    r"making fun|just joking|cut (me off|the call))\b",
    re.I,
)
CONCRETE_TIME_RE = re.compile(
    r"\b(tomorrow|tmrw|2moro|today|tonight|next week|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"after \d+\s?(am|pm|hour|hours)|at \d{1,2}|"
    r"\d{1,2}\s?(am|pm))\b",
    re.I,
)


def has_callback(text: str) -> bool:
    """True when text has a real callback signal (not 'didn't give me time to talk')."""
    t = fold(text)
    if not t or not CALLBACK_RE.search(t):
        return False
    if CALLBACK_FALSE_RE.search(t) and not CONCRETE_TIME_RE.search(t):
        return False
    return True
MONEY_RE = re.compile(r"\b(no money|dont have money|do not have money|no funds|cannot afford|cant afford|no income)\b", re.I)
WRONG_NUM_RE = re.compile(
    r"\b(wrong number|wrong no\b|wrong num\b|not my number|not the (right )?(person|number)|"
    r"number (is )?incorrect|number not in service|invalid number)\b",
    re.I,
)
BUSY_ONLY_RE = re.compile(r"\b(currently busy|line (is )?busy|number (is )?busy|busy/rejection|busy rejection)\b", re.I)
INVALID_MAIL_RE = re.compile(r"\b(invalid mail|invalid email|mail invalid|email invalid|wrong email|bad email)\b", re.I)
PICKUP_BUSY_RE = re.compile(r"\b(pu|picked up|pick up)\b.*\b(busy|lm\b|left (a )?message|call (me )?(later|back)|not now|cb\b)\b", re.I)


@dataclass
class ClassifyResult:
    account_no: str
    suggested_status: str
    validation_result: str
    decision_source: str
    reason: str
    match_detail: str = ""
    skip_ai: bool = True
    confidence: str = "High"
    extras: dict[str, Any] = field(default_factory=dict)


def _vr(crm: str, sug: str) -> str:
    if status_canon(crm) == status_canon(sug) and status_canon(crm):
        return "Correct"
    return "Wrong"


def classify_lead(lead: dict[str, Any]) -> ClassifyResult:
    acc = str(lead.get("account no") or lead.get("account_no") or "")
    crm = str(lead.get("customer status") or lead.get("Customer Status") or "").strip()
    comments = str(lead.get("last 10 comments") or lead.get("comments") or "")
    crm_c = status_canon(crm)
    parts = extract_parts(comments)
    non_sys = [p for p in parts if not is_system_comment(p["text"])]
    newest = non_sys[0] if non_sys else None
    newest_text = newest["text"] if newest else ""
    newest_norm = newest["norm"] if newest else ""
    full = fold(comments)
    streak = na_streak_days(parts)

    def done(status: str, source: str, reason: str, skip: bool = True, detail: str = "", conf: str = "High", manual: bool = False) -> ClassifyResult:
        vr = "Manual Check" if manual or "manual check" in source.lower() else _vr(crm, status)
        return ClassifyResult(
            account_no=acc,
            suggested_status=status,
            validation_result=vr,
            decision_source=source,
            reason=reason,
            match_detail=detail or reason[:120],
            skip_ai=skip,
            confidence=conf,
        )

    # 7) Decline / Duplicate / DNC → Manual Check
    if crm_c in {"decline", "duplicate", "dnc"}:
        label = crm or crm_c.title()
        return done(
            label,
            f"{label} (manual check)",
            f"Customer status is {label} - flagged for MANUAL CHECK (not auto-classified).",
            skip=True,
            detail=f"customer status = {label}",
            manual=True,
        )

    # 6) Potential → Manual Check
    if crm_c == "potential":
        return done(
            crm or "Potential",
            "Potential (manual check)",
            "Customer status is Potential - flagged for MANUAL CHECK (not a final CRM status).",
            skip=True,
            detail="customer status = Potential",
            manual=True,
        )

    # New / In progress → Manual Check (pipeline statuses)
    if crm_c in {"new", "in progress"}:
        return done(
            crm,
            f"{crm} (manual check)",
            f"Pipeline status '{crm}' should not be auto-classified.",
            skip=True,
            manual=True,
        )

    # 2) invalid mail alone must NOT become Denied Registration / Wrong Number
    # If newest meaningful signal is only invalid mail + NA history → No Answer
    if INVALID_MAIL_RE.search(full) and not WRONG_NUM_RE.search(full):
        if streak >= 1 or (newest and is_na_only_line(newest_text)) or crm_c.startswith("no answer"):
            status = "No Answer 5 UP" if streak >= 5 else "No Answer 1-5"
            # If CRM already Call Again family and streak < 5 → keep CA (rule 4)
            if crm_c in {"call again", "recall"} and streak < 5:
                keep = "Recall" if crm_c == "recall" else "Call Again"
                return done(keep, "rule-engine:call_again_kept_under_5na", f"invalid mail ignored for status; streak={streak} (<5) keep {keep}", detail=f"streak days={streak}")
            return done(status, "rule-engine:invalid_mail_ignored", f"invalid mail does not change status; phone NA => {status}", detail="invalid mail (status ignored)")

    # 1) currently busy / telecom busy without pickup talk → No Answer
    if BUSY_ONLY_RE.search(full) or (newest and re.search(r"\bcurrently busy\b", newest_norm)):
        if not PICKUP_BUSY_RE.search(full) and not has_callback(newest_norm):
            if crm_c in {"call again", "recall"} and streak < 5 and streak > 0:
                keep = "Recall" if crm_c == "recall" else "Call Again"
                return done(keep, "rule-engine:call_again_kept_under_5na", f"busy/NA streak={streak} (<5) keep {keep}")
            status = "No Answer 5 UP" if streak >= 5 else "No Answer 1-5"
            return done(status, "rule-engine:currently_busy_is_na", f"telecom busy without real talk => {status}", detail="currently busy")

    # pickup + busy = Call Again (real contact)
    if newest and PICKUP_BUSY_RE.search(newest_norm):
        if crm_c in {"call again", "recall"} and streak < 5:
            keep = "Recall" if crm_c == "recall" else "Call Again"
            return done(keep, "rule-engine:busy_after_pickup", f"pu+busy contact => {keep}")
        return done("Call Again", "rule-engine:busy_after_pickup", "pu+busy contact => Call Again")

    # 5) no money + concrete callback in newest / full → Call Again
    if MONEY_RE.search(full) and has_callback(full):
        if has_callback(newest_norm) or has_callback(full):
            return done("Call Again", "rule-engine:money_plus_callback", "no money + concrete callback => Call Again (callback wins)")

    # 8) Recall + newer callback → Call Again
    if crm_c == "recall" and has_callback(newest_norm):
        return done("Call Again", "rule-engine:recall_to_call_again", "Recall CRM but newest comment has concrete callback => Call Again")

    # Mockery / "didn't give me time to talk" — not a callback request
    if newest and CALLBACK_FALSE_RE.search(newest_norm) and not has_callback(newest_norm):
        return done(
            "No Interest",
            "rule-engine:noncoop_in_newest",
            "Newest comment is non-cooperative / no time to talk (not a customer callback request).",
            detail="noncoop / didnt give time",
        )

    # 4) Call Again kept until 5 distinct NA days
    if crm_c in {"call again", "recall"}:
        if streak >= 5:
            return done("No Answer 5 UP", "rule-engine:call_again_5na_days", f"Call Again/Recall wiped after 5 distinct NA days (streak={streak})")
        if newest and is_na_only_line(newest_text):
            keep = "Recall" if crm_c == "recall" else "Call Again"
            return done(keep, "rule-engine:call_again_kept_under_5na", f"streak days={streak} (<5) keep {keep}", detail=f"streak days={streak}")
        # CRM already CA/Recall and no hard override → Correct keep
        if not MONEY_RE.search(newest_norm) or has_callback(newest_norm):
            keep = crm if crm else ("Recall" if crm_c == "recall" else "Call Again")
            # If callback in comments, still Call Again
            if has_callback(full):
                return done("Call Again" if crm_c != "recall" or has_callback(newest_norm) else keep,
                            "rule-engine:keep_crm_call_again", f"CRM {keep} kept (no 5-day NA streak)")
            return done(keep, "rule-engine:keep_crm_call_again", f"CRM {keep} kept", skip=True, conf="Medium")

    # 3) first-time wrong number → Denied Registration
    if WRONG_NUM_RE.search(full):
        # count distinct days with wrong-number utterance
        days = {p["date"] for p in non_sys if p["date"] and WRONG_NUM_RE.search(p["norm"])}
        if len(days) <= 1:
            return done("Denied Registration", "rule-engine:denied_registration_1x", "First-day wrong-number claim => Denied Registration", detail="wrong number (1x)")
        return done("Wrong Number or Email", "rule-engine:wrong_number_repeat", "Wrong-number claim on 2+ days => Wrong Number or Email")

    # Mechanical NA
    if newest and is_na_only_line(newest_text) and not any(not is_na_only_line(p["text"]) and not is_system_comment(p["text"]) for p in non_sys[:3]):
        # only NA-like recent lines
        if all(is_na_only_line(p["text"]) or is_system_comment(p["text"]) for p in non_sys[:5]):
            status = "No Answer 5 UP" if streak >= 5 else "No Answer 1-5"
            return done(status, "rule-engine:no_real_conversation", f"no real conversation streak={streak} => {status}", detail=f"streak days={streak}")

    # Already No Potential (incl. subtypes like "No Potential - no documents"):
    # keep CRM Correct unless a callback-driven rule above already fired.
    if crm_c == "no potential":
        return done(
            crm,
            "rule-engine:keep_no_potential",
            "CRM No Potential (subtype kept) — no competing callback override.",
            skip=True,
            detail="no potential family",
            conf="High",
        )

    # Ambiguous → hand to V2 AI / Memory Match
    return ClassifyResult(
        account_no=acc,
        suggested_status=crm,
        validation_result="Correct" if crm else "Manual Check",
        decision_source="rule-engine:passthrough",
        reason="No zero-token rule matched — hand off to V2 Memory Match / AI.",
        match_detail="",
        skip_ai=False,
        confidence="Low",
    )


def _result_to_dict(r: ClassifyResult, *, cache_hit: bool = False) -> dict[str, Any]:
    d: dict[str, Any] = {
        "account no": r.account_no,
        "Suggested Status": r.suggested_status,
        "Validation Result": r.validation_result,
        "Decision Source": r.decision_source,
        "Reason": r.reason,
        "Match Detail": r.match_detail,
        "skipAI": r.skip_ai,
        "Confidence": r.confidence,
        "Engine Shadow": True,
    }
    if cache_hit:
        d["cache_hit"] = True
        d["Decision Source"] = f"{r.decision_source} (exact-cache)"
    return d


def classify_leads(
    leads: list[dict[str, Any]],
    *,
    use_cache: bool = True,
    gate: bool = True,
) -> dict[str, Any]:
    from exact_cache import ExactClassifyCache
    from lead_gate import gate_leads

    gate_issues: list[str] = []
    work = leads
    if gate:
        work, gate_issues = gate_leads(leads)

    cache = ExactClassifyCache() if use_cache else None
    results: list[dict[str, Any]] = []
    cache_hits = 0

    for lead in work:
        if cache is not None:
            hit = cache.get(lead)
            if hit and hit.get("skipAI") is True:
                # Only reuse zero-token decisions
                payload = {
                    "account no": hit.get("account no") or lead.get("account no"),
                    "Suggested Status": hit.get("Suggested Status"),
                    "Validation Result": hit.get("Validation Result"),
                    "Decision Source": str(hit.get("Decision Source") or "") + " (exact-cache)",
                    "Reason": hit.get("Reason"),
                    "Match Detail": hit.get("Match Detail"),
                    "skipAI": True,
                    "Confidence": hit.get("Confidence") or "High",
                    "Engine Shadow": True,
                    "cache_hit": True,
                }
                results.append(payload)
                cache_hits += 1
                continue

        r = classify_lead(lead)
        row = _result_to_dict(r)
        if cache is not None and r.skip_ai:
            cache.set(lead, {k: v for k, v in row.items() if k != "cache_hit"})
        results.append(row)

    skip = sum(1 for r in results if r.get("skipAI"))
    return {
        "ok": True,
        "token_cost": 0,
        "total": len(results),
        "skip_ai_count": skip,
        "ai_needed_count": len(results) - skip,
        "cache_hits": cache_hits,
        "gate_issues": gate_issues,
        "leads": results,
    }


def write_classify_run_note(vault_runs_dir: Path, payload: dict[str, Any], source: str = "classify") -> Path:
    vault_runs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = vault_runs_dir / f"classify-{stamp}.md"
    leads = payload.get("leads") or []
    wrong = [l for l in leads if str(l.get("Validation Result")).lower() == "wrong"]
    manual = [l for l in leads if "manual" in str(l.get("Validation Result")).lower()]
    content = f"""---
type: classify_run
source: {source}
token_cost: 0
total: {payload.get('total', 0)}
skip_ai: {payload.get('skip_ai_count', 0)}
ai_needed: {payload.get('ai_needed_count', 0)}
---

# Classify Run {stamp}

## Summary
- Total: {payload.get('total', 0)}
- Zero-token decisions (skipAI): {payload.get('skip_ai_count', 0)}
- Needs V2 AI: {payload.get('ai_needed_count', 0)}
- Wrong: {len(wrong)}
- Manual: {len(manual)}

## Linked policies
- [[currently-busy-is-na]]
- [[invalid-mail-ignored]]
- [[call-again-5-na-days]]
- [[money-plus-callback]]
- [[potential-manual-check]]
"""
    path.write_text(content, encoding="utf-8")

    # decision snippets for wrong/manual
    decisions = vault_runs_dir.parent / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    for l in (wrong + manual)[:50]:
        acc = re.sub(r"[^A-Za-z0-9_-]+", "_", str(l.get("account no") or "unknown"))
        dp = decisions / f"{stamp}_{acc}.md"
        dp.write_text(
            f"""---
account: {l.get('account no')}
suggested: {l.get('Suggested Status')}
validation: {l.get('Validation Result')}
source: {l.get('Decision Source')}
---

# Decision {l.get('account no')}

{l.get('Reason')}
""",
            encoding="utf-8",
        )
    return path
