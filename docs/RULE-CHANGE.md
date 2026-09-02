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
```

## Dosya haritası

| Dosya | Rol |
|-------|-----|
| `vault/rules/*.md` | İnsan okur kural |
| `vault/MEMORY.md` | Kural indeksi |
| `evals/golden_leads.jsonl` | Regresyon kilidi |
| `services/rule-engine/crm_classify.py` | Canonical kod |
| n8n **Memory Match** | Canlı Telegram motoru |
| Google Sheet | Sadece `human_approved=true` tetikleyiciler |

## Telegram Rules brain (live)

On `/start` choose **Rules brain** (next to Database check).

```text
You chat in Telegram
        │
        ▼
Front Door loads Google Sheet triggers + canonical rules
        │
        ▼
OpenAI replies: which rule applies / why Wrong / draft a change
        │
        ▼
You reply CONFIRM → draft saved to Decision_Memory (rule_draft)
        │
        ▼
Then vault + golden + Memory Match (Cursor / rule-change flow)
```

- Paste a comment → “bu hangi kural?”
- “Şunu değiştirelim…” → draft; `CONFIRM` saves
- `/exit` leaves chat mode
- Does **not** auto-edit Memory Match; that stays the rule-change checklist

After each run summary, V2 may send up to **12** uncertain leads as normal Telegram messages with status buttons (Call Again, No Answer, Recall, …). No n8n links.

- Selected when: `Confidence=Low`, or `Manual Check`, or AI-path `Wrong` with Medium confidence
- You tap a button → Front Door saves the vote and confirms in chat
- Votes append to Google Sheet `Decision_Memory` as `type=human_survey` (best-effort)

Reports still send as usual; the survey does not block XLSX files.