# n8n Import Dosyalari

Bu klasordeki JSON dosyalarini n8n'e Import from File ile yukle.

## Dosyalar

1. `03-telegram-database-check-self-contained.workflow.json`
   - **SIMDI BUNU YUKLE** (n8n Cloud icin, duzeltilmis surum)
   - CrewAI / Memory servisi gerektirmez
   - xlsx/xls/csv okur, validate eder, csv dondurur
   - Telegram download, Extract From File, hata mesajlari duzeltildi
2. `01-telegram-database-check.workflow.json`
   - CrewAI + Memory servisleri ayaktaysa
3. `02-mcp-database-check-tool.workflow.json`
   - MCP tool (istege bagli)

## Import adimlari

1. Onceki published workflow'lari **Unpublish** et
2. n8n -> Import from File
3. `03-telegram-database-check-self-contained.workflow.json` sec
4. Telegram credential bagla
5. Publish et
6. Telegram'da `/start` -> Database check -> `.xlsx` gonder
