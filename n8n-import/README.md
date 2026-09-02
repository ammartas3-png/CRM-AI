# n8n Import Dosyalari

Bu klasordeki JSON dosyalarini n8n'e Import from File ile yukle.

## Dosyalar

1. `01-telegram-database-check.workflow.json`
   - Ana Telegram bot akisi (bunu mutlaka yukle)
2. `02-mcp-database-check-tool.workflow.json`
   - MCP tool (istege bagli)

## Import adimlari

1. n8n -> Workflows -> Import from File
2. Once `01-...` dosyasini sec
3. Telegram credential bagla
4. Publish / Activate et
5. Istersen `02-...` dosyasini da ayni sekilde import et

## Onemli

Eski published workflow:
`Telegram Database Validator Bot V2`

Yeni akisi yayina almadan once eskiyi unpublish et; ayni botta 2 trigger catisir.
