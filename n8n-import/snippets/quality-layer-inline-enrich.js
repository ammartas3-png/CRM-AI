// Quality Layer enrich (ambiguous only). No-op when QUALITY_LAYER_URL unset/down.
const all = $input.all().map((i) => i.json);

function looksAmbiguous(j) {
  const vr = String(j["Validation Result"] || "").toLowerCase();
  const conf = String(j.Confidence || "").toLowerCase();
  const comments = String(j["last 10 comments"] || j.comments || "").toLowerCase();
  if (vr === "manual check" || vr === "wrong" || conf === "low") return true;
  if (j._needs_bot_qa) return true;
  if (/\b(no money|cant afford|cannot afford|no funds|no capital|cb\b|callback|call again|no english|not interest|dont want|discontinue)\b/.test(comments)) return true;
  return false;
}

const base = String($env.QUALITY_LAYER_URL || "").replace(/\/$/, "");
if (!base) {
  return all.map((json) => ({ json: { ...json, _quality_skipped: "no_QUALITY_LAYER_URL" } }));
}

const ambiguous = all.filter(looksAmbiguous);
if (!ambiguous.length) {
  return all.map((json) => ({ json: { ...json, _quality_skipped: "none_ambiguous" } }));
}

let enriched = [];
try {
  const resp = await this.helpers.httpRequest({
    method: "POST",
    url: base + "/quality/enrich-leads",
    body: { leads: ambiguous, only_ambiguous: true },
    json: true,
    timeout: 15000,
  });
  enriched = Array.isArray(resp?.leads) ? resp.leads : Array.isArray(resp) ? resp : [];
} catch (e) {
  return all.map((json) => ({
    json: { ...json, _quality_skipped: "http_error", _quality_error: String(e.message || e) },
  }));
}

const byAcc = new Map();
for (const row of enriched) {
  const key = String(row["account no"] || row.account_no || "");
  if (key) byAcc.set(key, row);
}

return all.map((json) => {
  const key = String(json["account no"] || json.account_no || "");
  const hit = key && byAcc.get(key);
  if (!hit) return { json: { ...json, _quality_skipped: "passthrough" } };
  return { json: { ...json, ...hit, _quality_enriched: true } };
});
