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

## Yapmayın

- Onaysız AI sheet satırı eklemeyin
- CrewAI / semantic cache’i ana motor yapmayın
- Kuralı sadece n8n Code’da bırakıp golden’sız bırakmayın
