## Rule change checklist

- [ ] `vault/rules/<id>.md` eklendi/güncellendi
- [ ] `vault/MEMORY.md` indeksine eklendi
- [ ] `evals/golden_leads.jsonl` örnek lead eklendi
- [ ] `services/rule-engine/crm_classify.py` güncellendi (gerekirse)
- [ ] `python3 scripts/validate_rule_system.py` geçti
- [ ] `python3 -m pytest -q services/tests` geçti
- [ ] Canlı n8n **Memory Match** sync edildi (Telegram etkisi için)
- [ ] Google Sheet’e satır eklendiyse `human_approved=true`

## Örnek lead

- Account:
- CRM status:
- Expected status:
- Notes:

## Test plan

- [ ] Golden test yeşil
- [ ] Telegram’dan dosya tekrar atılınca örnek account doğru
