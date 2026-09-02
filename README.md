# CRM-AI — Telegram Database Check Platform

Telegram üzerinden Excel/CSV yükleyip database check yapan sistem.

## Mimari

```text
Telegram (n8n Trigger)
  -> CrewAI Service (/validate)
      -> xlsx otomatik csv'ye çevrilir
      -> Validator + Reporter ajanları
  -> Memory Service (/memory/validation)
      -> MCP uyumlu kalıcı hafıza (JSONL graph)
  -> Telegram cevabı (metin + csv dosyası)
```

## Neden xlsx yerine işlemde CSV?

Evet — **xlsx yükleyip içeride CSV'ye çevirmek daha uygun**:

| | xlsx | csv (işlem formatı) |
|---|------|---------------------|
| n8n node uyumu | Orta | Yüksek |
| CrewAI / pandas analizi | Daha zor | Kolay |
| Token/maliyet | Daha yüksek | Daha düşük |
| Hata ayıklama | Zor | Kolay |

Kullanıcı yine `.xlsx` gönderir; servis otomatik `.csv`'ye çevirip öyle işler.

---

## 1) Servisleri çalıştır

```bash
cp .env.example .env
docker compose up --build -d
```

Health check:

- CrewAI: `http://localhost:8080/health`
- Memory: `http://localhost:8090/health`

## 2) n8n workflow import

Import files:

- `n8n/telegram-database-check.workflow.json` (ana Telegram akışı)
- `n8n/mcp-database-check-tool.workflow.json` (MCP tool expose)

Gerekli n8n env:

- `CREWAI_SERVICE_URL`
- `MEMORY_SERVICE_URL`

Telegram credential: `@BotFather` token.

## 3) MCP hafıza

REST API (n8n HTTP node):

- `POST /memory/validation`
- `GET /memory/user/{user_id}/history`
- `GET /memory/graph`

Claude/Cursor MCP config örneği:

- `mcp/claude-desktop.config.example.json`

Resmi MCP memory server da kullanılabilir:

```bash
npx -y @modelcontextprotocol/server-memory
```

## 4) CrewAI microservice

Endpoint:

- `POST /validate` (multipart file upload)

Davranış:

1. `.xlsx` -> `.csv` dönüşümü
2. Rule-based validation (duplicate, header, column mismatch)
3. `OPENAI_API_KEY` varsa Validator + Reporter crew
4. Key yoksa rule-based fallback (ücretsiz mod)

---

## API örnekleri

### Validate file

```bash
curl -X POST "http://localhost:8080/validate" \
  -F "file=@sample.xlsx" \
  -F "user_id=123" \
  -F "chat_id=456"
```

### Save memory

```bash
curl -X POST "http://localhost:8090/memory/validation" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"123",
    "chat_id":"456",
    "file_name":"sample.xlsx",
    "valid":false,
    "issues":["duplicate rows"],
    "converted_to":"csv",
    "message":"2 duplicate row found"
  }'
```

---

## Vercel bot (legacy)

`api/telegram.py` hâlâ mevcut (fallback). Ana önerilen yol artık **n8n-native** akış.

---

## Test

```bash
python3 -m pip install openpyxl fastapi pydantic
python3 services/tests/smoke_test.py
```

---

## Önerilen rollout

1. Docker servisleri ayağa kaldır
2. n8n Telegram workflow import + activate
3. `/start` -> Database check -> `.xlsx` gönder
4. Memory history kontrol: `/memory/user/{id}/history`
5. İsteğe bağlı MCP tool workflow publish
