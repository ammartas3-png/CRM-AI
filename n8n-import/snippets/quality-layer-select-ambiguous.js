/**
 * n8n Code node — after Memory Match / before report merge.
 *
 * Sends only ambiguous or family-flagged leads to Quality Layer, then merges
 * Suggested Status back. Safe no-op when QUALITY_LAYER_URL is unset / down.
 *
 * Pair with an HTTP Request node:
 *   Method: POST
 *   URL: {{$env.QUALITY_LAYER_URL}}/quality/enrich-leads
 *   Body: { "leads": <output of this code>, "only_ambiguous": true }
 */
const all = $input.all().map((i) => i.json);

function looksAmbiguous(j) {
  const vr = String(j["Validation Result"] || "").toLowerCase();
  const conf = String(j.Confidence || "").toLowerCase();
  const comments = String(j["last 10 comments"] || j.comments || "").toLowerCase();
  if (vr === "manual check" || vr === "wrong" || conf === "low") return true;
  if (j._needs_bot_qa) return true;
  if (/\b(no money|cant afford|cannot afford|no funds|cb\b|callback|call again|no english|not interest|dont want)\b/.test(comments)) {
    return true;
  }
  return false;
}

const ambiguous = all.filter(looksAmbiguous);
const passthrough = all.filter((j) => !looksAmbiguous(j));

return [
  {
    json: {
      _quality_batch: true,
      ambiguous_count: ambiguous.length,
      passthrough_count: passthrough.length,
      leads: ambiguous,
      passthrough,
    },
  },
];
