# Decision Memory

Learned status corrections are stored here (Obsidian-style).

Each note:
- old status -> new status
- keyword / decision source
- confidence
- example comment snippet

Linked rules: [[required-columns]] [[phone-normalize]] [[email-normalize]] [[duplicate-phone]]

n8n writes runtime memories to:
1. workflow staticData (`decisionMemory`)
2. Google Sheet tab `Decision_Memory` (auto-append)
3. optional local files under `vault/decisions/` when rule-engine runs
