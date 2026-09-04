# Kural değiştirme sistemi (repo + golden + n8n)

Bu proje için **Obsidian zorunlu değil**. Tek sistem:

```text
Wrong lead / yeni karar
        │
        ▼
GitHub Issue (şablon: Rule change)
        │
        ▼
vault/rules/<id>.md     ← kısa kural metni
evals/golden_leads.jsonl ← örnek lead + beklenen sonuç
crm_classify.py          ← zero-token kod
        │
        ▼
pytest / CI yeşil
        │
        ▼
n8n Memory Match güncelle (canlı Telegram)
```

## Sizin günlük işiniz

1. Telegram raporunda yanlış bir lead görünce **Issue açın** (şablon hazır).
2. Ya da Cursor’a şunu yapıştırın:
   - `account no`
   - CRM status
   - `last 10 comments`
   - olması gereken status
   - kısa gerekçe
3. PR gelince checklist’i işaretleyin; merge sonrası aynı dosyayı Telegram’dan tekrar atıp o account’u kontrol edin.

## Komutlar

Yeni kural iskeleti:

```bash
python3 scripts/new_rule.py \
  --id wrong-number-first \
  --title "First wrong number → Denied Registration" \
  --status "Denied Registration" \
  --crm "Wrong Number or Email" \
  --comments "2026-09-02 10:00 | X | client said wrong number;"
```

Doğrulama:

```bash
python3 scripts/validate_rule_system.py
python3 -m pytest -q services/tests/test_golden_classify.py
node scripts/mm_harness.js     # n8n Memory Match, insan onaylı 59 lead
node scripts/appt_harness.js   # randevu düğümü koruma kuralları
```

n8n düğüm kodunu dosya olarak düzenlemek için:

```bash
python3 scripts/node_code.py extract "Memory Match" /tmp/mm.js
# /tmp/mm.js üzerinde düzenle
python3 scripts/node_code.py inject "Memory Match" /tmp/mm.js
```

## Dosya haritası

| Dosya | Rol |
|-------|-----|
| `vault/rules/*.md` | İnsan okur kural |
| `vault/MEMORY.md` | Kural indeksi |
| `evals/golden_leads.jsonl` | Regresyon kilidi (Python motoru) |
| `evals/wrong_review_cases.jsonl` | İnsan onaylı 59 lead (n8n Memory Match) |
| `evals/appointment_cases.jsonl` | Randevu düğümü koruma kuralları |
| `evals/rules_sheet.json` | Canlı Google Sheet kural satırlarının kopyası |
| `scripts/mm_harness.js` | Memory Match'i n8n dışında koşturur |
| `scripts/node_code.py` | Düğüm kodunu çıkar / geri yaz |
| `services/rule-engine/crm_classify.py` | Canonical kod |
| n8n **Memory Match** | Canlı Telegram motoru |
| Google Sheet | Sadece `human_approved=true` tetikleyiciler |

## Telegram Rules brain (live)

On `/start` type **`2`** (or Rules brain).

**Google Sheet mode** — primary job is inspecting `CRM_AI_Rules` / Sheet1:

| You send | Bot does |
|----------|----------|
| a comment / phrase | lists matching **sheet rows** (row, trigger, status, group) |
| `liste` | active rule counts by keyword_group |
| `ara no money` | search sheet triggers |
| change request | drafts a sheet edit; `CONFIRM` → Decision_Memory |
| `exit` | leave mode |

Canonical policies are only footnotes (e.g. Call Again &lt;5 NA days). Sheet matches are shown first.

After each run summary, V2 may send up to **12** uncertain leads as normal Telegram messages with status buttons (Call Again, No Answer, Recall, …). No n8n links.

- Selected when: `Confidence=Low`, or `Manual Check`, or AI-path `Wrong` with Medium confidence
- You tap a button → Front Door saves the vote and confirms in chat
- Votes append to Google Sheet `Decision_Memory` as `type=human_survey` (best-effort)

Reports still send as usual; the survey does not block XLSX files.

## After a large run (Correct-bucket HITL)

Do not only triage Wrong rows. Also sample Correct:

```bash
python3 scripts/quality_tools.py hitl-routine --input leads.json --limit 30
```

See [`QUALITY-LAYER.md`](QUALITY-LAYER.md). Top conflict families to watch: Call Again↔Recall, Call Again↔No Potential.
