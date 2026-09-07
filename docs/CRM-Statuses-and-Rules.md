# Statuses and Rules
## CRM Lead Status Handbook (System Rules)

This handbook is the status rulebook for our classification system and for agents reviewing Telegram/Excel suggestions.  
Put the status that matches the **newest meaningful customer sentence**. Agent dial notes are not customer requests.

**Golden rule:** Right after the call, write a clear English comment and set the status from what the client actually said — not from a bare label.

---

## ---- COMMENTS

- Put a comment right after you finish the call.
- Comments **only in English** (ask TL / use translate if needed).
- Include meaningful details: why this status, money/time/language/identity signals, appointment time (IST or local).
- Do **not** write empty comments like “We talk”, “No interest”, “NA” with no detail.
- If ringing is wrong, write **how it sounds** (beeping / no route / no ring / DVM) — not only `NA`.
- Official tone only — no slang, curses, or insults about the client.
- If you only mail the client, paste received/sent mails translated to English into comments.
- Do **not** leave the status name as the only comment. Explain the conversation.
- Do not add a TASK if you did not talk to the client.
- Check previous comments; if something looks wrong, tell TL/CRM.

---

## ---- NO ANSWER 1-5 / 5 UP

### No Answer 1-5
Use when the phone is alive but there is **no real conversation**:
- Client did not pick up
- Pick up but no talk / hung up immediately during or right after intro
- Dialer-only: `na`, `vm`, `dvm`, `ring`, `ndt`, `db`, `cnbr`, `currently busy` (no pickup talk)

**Not Call Again** if they hung up with no conversation.

### No Answer 5 UP
Use when there are **5+ distinct days** of dialer-only NA/VM (same-day `navm` twice ≠ 5 UP). Verifier cannot invent 5 UP without those days. of no-answer / no real conversation.

### Important (system)
- **Invalid email** + newest line is ring/NA/VM/DVM → keep **No Answer**, do **not** use Wrong Number (phone is alive).
- `CB REJS` / `cb reject` alone is **not** a customer callback → usually stay **No Answer**.
- Agent notes like `cb:vm`, `cb na`, `call again rej` are **your** redial logs — they do **not** upgrade the lead to Call Again.

---

## ---- CALL AGAIN

Use Call Again when there was a **real conversation** (or a clear customer ask to be called) and the lead is still workable.

### Put Call Again when
- You spoke, client was busy / in a rush / “call me later / tomorrow / at 6pm”
- Someone picked up and said client is not available now — with a real short talk
- Client interested but **no money yet**, and there is a **near-term plan**:
  - salary soon / until salary / in a few days
  - will arrange funds / ask friends / will get help and deposit
  - give me time to source funds
- **DIY self-serve:** `dont need your help` / `i will do it by myself` (still wants to invest; does not want agent help) → **Call Again**
- **Arabic desk transfer:** client speaks Arabic and we have Arabic speakers/markets → transfer → **Call Again** (not No Language)
- Concrete customer callback / appointment (date and better with exact time; note IST vs local)

### Do NOT put Call Again when
- Hung up with **no conversation** → **No Answer**
- Only agent dial noise (`cb:vm`, `cb na`, `call again rej`) → keep NA / previous outcome
- `next month` / `by October` / `in 4 months` / `dont know when` + no near plan → **No Potential**
- `dont think I’m interested` / clear soft refuse (first day) → **Recall**
- Hard refuse + curse / “never call again” path → see No Interest

### Follow-up habit
- If no exact appointment time: follow up the same day and across days while the lead stays Call Again.
- If exact date/time: call at that time (see Appointment).
- After appointment + **5 different days** still NA → you may move to **No Answer 5 UP**.

**Rule:** If you truly spoke with the client and no harder junk/final status fits, prefer **Call Again** — it must not be No Answer.

---

## ---- APPOINTMENT

- Call exactly when the client asked (clients usually cannot call us back).
- Date only, no clock time → call that day at different hours.
- Exact time → call no later than ~15 minutes after, several tries in that hour.
- “I’ll text when ready” / vague → still try within about a week; status is usually **Call Again**, not Potential (unless FTD+KYC rules met).
- After the call, add appointment info in the task/comment (day/time + IST/local).

---

## ---- POTENTIAL

Our classifier treats bare CRM **Potential** carefully (often Manual Check). Agents may use Potential only when:
- Agreement to make an FTD with a date (better with time), **and**
- Full or partial KYC

If interested but money is **not** short-term → usually **No Potential** or keep working as **Call Again** only when a near funding plan exists (see money rules).  
If Potential later says not interested → **Recall**, then **No Interest** if still refuses.

---

## ---- RECALL

First soft / clear refusal day — still try again soon.

### Put Recall when
- `not interested` / doesn’t want to proceed (first day)
- Soft refuse / cold close without two-day NI rule yet
- `dont think I’m interested` (negated interest)
- Bare `didnt register` / `I didn’t register` **without** identity denial (“I am not that person”)
- Cancel / afraid / trust issues without hard final junk (case-by-case; often Recall)

### Comment example
`Client not interested — follow-up next day.` (+ reason)

### Do not use Recall for
- DIY `i will do it by myself` / `dont need your help` with no refuse → **Call Again**
- Two distinct refusal days → **No Interest**
- Identity denial → **Denied Registration**

---

## ---- NO INTEREST

Push first. No Interest is for **lasting** refusal.

### Allowed paths
1. Refusal / not interested on **two different days**, or  
2. Curse / scream / abusive + clear “I don’t want”, or  
3. After Recall, **3 distinct days** no pickup → No Interest, or  
4. Very strong “never call me again” after proper Recall follow-up

### Always
- Write the **full reason** in the comment why they are not interested.
- Registration already shows some interest — push before jumping to NI on day one (unless abusive).

### Not No Interest
- First “not interested” only → **Recall**
- Bare hang-up → not a refusal by itself

---

## ---- NO POTENTIAL

Use when money/capacity path is **closed** (not a short follow-up).

### Put No Potential when
- No money / can’t afford / no capital **and** timing is dead or distant:
  - `next month`, `by October`, `in 4 months`, months to save
  - don’t know when / reply when ready / not sure when
  - not serious / didn’t mean to invest
  - discontinue / will not proceed + no funding plan
  - capital affordable? no + hung up
- Phone unreachable and client wants **email only** / cannot take calls

### Do NOT put No Potential when
- Soft money + near plan (salary soon, arrange, friends, will deposit soon) → **Call Again**
- DIY self-serve without hard refuse → **Call Again**

---

## ---- NO POTENTIAL - NO DOCUMENTS

More specific than general No Potential:
- `no id` / `no documents` / `no bank` / `no POR`

Bare `didnt register` alone is **not** this → **Recall**.

---

## ---- DECLINE

- Client tried to deposit / payment declined path; keep calling per ops rules.
- If you are on the call when decline happens, set status from the **conversation** (Call Again if they ask later; Manual/ops if needed).
- Comment the full decline reason.
- CRM Decline/Duplicate/DNC are often **Manual Check** for the bot — humans apply ops rules.

---

## ---- DENIED REGISTRATION

### Put Denied Registration when
- Client denies **identity**: `I’m not Ahmad`, `wrong person`, `this is not me`, someone else registered on my number **with identity denial**

### Escalation
- **1st day** identity denial → **Denied Registration**
- **Same claim on a later day** → **Wrong Number or Email**

### Do NOT use Denied for
- Bare `didnt register` (no “not me”) → **Recall**
- `no id` / no bank → **No Potential - no documents**
- Language only → see No Language / Arabic transfer

**Priority:** identity denial **beats** language in the same sentence  
(`I’m not Ahmad, speak Arabic` → **Denied Registration**).

---

## ---- NO LANGUAGE (pool / junk family)

### Put No Language when
- Client does **not** speak a language we have desk speakers for (e.g. Mandarin / unsupported), hard time in English/MY, needs translator and **no transfer desk**

### Do NOT put No Language when
- **Arabic** (we have Arabic speakers / Arabic markets in the report) → transfer → **Call Again**
- Explicit `arabic not available` / no Arabic agent → then **No Language** is OK
- You only heard a language on voicemail / background / country code / NA → not enough
- You couldn’t hear properly — don’t guess

Comment **which language** they speak.

---

## ---- UNDER 18

- Client is under 18 — write exact age if known.
- Do not guess from voice/details; if unsure, ask again.

---

## ---- WRONG NUMBER OR EMAIL

### Put Wrong Number or Email when
- Number not in service / incorrect / invalid — preferably after tries and/or **support confirmed**
- Identity denial repeated on a **second day**
- Number is public/company and confirmed wrong ownership pattern

### Do NOT put Wrong Number when
- **Invalid email** but phone rings / NA / VM → **No Answer**
- Fresh weird tone / beeping on day one only — note it; don’t junk immediately
- Client says “it’s my name but I didn’t register” → **Recall** / NI path — not Wrong Number on that alone
- Bare word `CRM` in a comment is not proof of wrong contact

Send email for alternative number when useful.

---

## ---- DUPLICATE / DNC / INVALID COUNTRY

- **Duplicate:** another live workable account (CA/Potential/Decline on another agent, etc.) — follow TL/CRM; don’t keep all regs on you.
- **DNC:** support-terminated / do-not-call — support-driven.
- **Invalid Country:** illegally in registered country / cannot close FTD for country docs — only with clear signal.

These are mostly **manual / support** in our pipeline (Manual Check when CRM already carries them).

---

## ---- PRIORITY TREE (what to check first)

1. Identity denial → **Denied Registration** (then Wrong Number on repeat day)  
2. Language — Arabic desk → **Call Again**; unsupported / no desk → **No Language**  
3. Under 18 / Invalid Country  
4. Hard / distant money → **No Potential**  
5. Soft money + near plan → **Call Again**  
6. No id / no bank / no POR → **No Potential - no documents**  
7. Newest refuse → **Recall** (day 1) / **No Interest** (day 2 or abuse path)  
8. Real customer callback / busy-with-talk → **Call Again**  
9. Dialer-only / HU no talk → **No Answer 1-5** (5+ days → **5 UP**)  
10. Unclear mix → **Manual Check**

---

## ---- SHORT RULES

**Call Again**  
- Real talk + still workable, or customer CB/appointment, or soft money with near plan, or DIY self-serve, or Arabic transfer.

**No Potential**  
- Money/capacity dead or distant (`next month`, don’t know when, not serious, quit with no plan).

**Recall**  
- First refusal day / soft cold close / bare didn’t register (no identity denial).

**No Interest**  
- Two refusal days, or abuse+refuse, or Recall then 3 NA days.

**No Answer 1-5 / 5 UP**  
- No real conversation; phone alive. Not for real CB talks.

**Denied Registration**  
- “Not me / wrong person” day 1 → Denied; repeat later → Wrong Number.

**No Language**  
- No desk speaker for that language. Arabic with desk → Call Again.

**Wrong Number or Email**  
- Truly dead/invalid number (support when possible). Not invalid-email-only while phone lives.

**Potential**  
- FTD agreement + time/date + KYC only.

**Manual Check**  
- Mixed/unclear intent — don’t invent a status.

---

## ---- STATUSES WE DO NOT AUTO-USE / UNUSED

Chargeback · Compliant · Deposited with me · Fraud · Payment Fraud · PCA · Reassign · No Answer 10 UP · FTD – No Answer

---

## ---- AGENT DIAL NOTES (read this)

These are **your** logs, not customer callbacks:
`cb : vm` · `cb na` · `cb rej` · `call again rej` · `CALLED BACK PUHU` · `when I tried to cb she rejected`

Strip them mentally; decide from the remaining **customer** words.

---

## ---- MINI EXAMPLES

| Comment signal | Status |
|---|---|
| pu said to call him later | Call Again |
| no money until salary then will start | Call Again |
| dont need your help / i will do it by myself | Call Again |
| arabic speaker / fluent in arabic | Call Again |
| does not have the money next month | No Potential |
| not interested (first day) | Recall |
| not interested on two days | No Interest |
| im not Ahmad speak Arabic | Denied Registration |
| said i didnt register | Recall |
| no id / no bank | No Potential - no documents |
| mandarin / hard time English (no desk) | No Language |
| dvm in arabic not available | No Language |
| Invalid email + ring/dvm newest | No Answer 1-5 |
| HU with no conversation | No Answer 1-5 |
| CB REJS only | No Answer 1-5 |

---

*Handbook aligned to Memory Match / Verifier system rules — September 2026.*
