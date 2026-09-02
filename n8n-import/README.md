# n8n Import Dosyalari

## SIMDI BUNU IMPORT ET

`04-Telegram_Database_Validator_Bot_V2_CSV_first_fixed.workflow.json`

Bu, senin V2 validator'inin duzeltilmis hali:
- CSV / XLSX / XLS / JSON okur (CSV tercih)
- Memory Match + AI Agent + Verifier ayni
- 3 XLSX Telegram ciktisi ayni (Report / Manual Entry / 5UP)

## Diger dosyalar

- `Telegram_Database_Validator_Bot_V2.original.json` — orijinal V2 yedek
- `03-...` — basit test akisi (V2 yerine kullanma)
- `01-...` / `02-...` — deneysel

## Import

1. Eski/simple published workflow'lari Unpublish et
2. `04-...` dosyasini Import from File ile yukle
3. Telegram + Google Sheets + OpenAI credential bagla
4. Publish et
5. Production webhook:
   `https://ammartd20.app.n8n.cloud/webhook/Database-check`

## V2'de duzeltilen kritik bug

Eski Extract node `fromJson` idi → Excel/CSV kiriliyordu.

Yeni:
`File Kind Switch -> Extract CSV/XLSX/XLS/JSON -> Normalize Leads -> Chunk Router -> Memory Match...`
