/**
 * n8n Code node — merge Quality Layer enrich-leads response back into the row stream.
 *
 * Expects:
 *  - HTTP response JSON: { leads: [...] }
 *  - Prior node that kept `passthrough` rows (from quality-layer-select-ambiguous.js)
 *
 * Usage: put after HTTP Request to /quality/enrich-leads
 */
const http = $input.first().json;
const enriched = Array.isArray(http.leads) ? http.leads : Array.isArray(http) ? http : [];

// Prefer passthrough from the select node if available in the run
let passthrough = [];
try {
  const sel = $("Quality Select Ambiguous").first().json;
  passthrough = Array.isArray(sel.passthrough) ? sel.passthrough : [];
} catch (e) {
  passthrough = [];
}

const byAccount = new Map();
for (const row of [...passthrough, ...enriched]) {
  const key = String(row["account no"] || row.account_no || "");
  if (!key) continue;
  byAccount.set(key, row);
}

return [...byAccount.values()].map((json) => ({ json }));
