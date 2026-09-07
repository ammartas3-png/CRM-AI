#!/usr/bin/env node
// Regression-tests Apply Verifier Columns deterministic guards (Conflict H).
//
//   node scripts/verifier_guard_harness.js
//   node scripts/verifier_guard_harness.js --verbose

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const WORKFLOW = path.join(ROOT, "n8n-import", "05-V2-smart-upgraded.workflow.json");
const CASES = path.join(ROOT, "evals", "verifier_guard_cases.jsonl");

function loadGuards() {
  const wf = JSON.parse(fs.readFileSync(WORKFLOW, "utf8"));
  const node = wf.nodes.find((n) => n.name === "Apply Verifier Columns");
  if (!node) throw new Error("Apply Verifier Columns not found");
  const code = node.parameters.jsCode;
  const cut = code.indexOf("const verdicts");
  if (cut < 0) throw new Error("could not locate guard prelude");
  const prelude =
    code.slice(0, cut) +
    `
module.exports = {
  deterministicContextFix,
  verifierOverrideBlocked,
  canonStatus,
  isSoftMoneyCallAgain,
  isHardMoneyNoPotential,
  foldComments,
};
`;
  const sandbox = { module: { exports: {} }, exports: {} };
  vm.runInNewContext(prelude, sandbox, { timeout: 5000 });
  return sandbox.module.exports;
}

function normFam(s) {
  const x = String(s || "").toLowerCase();
  if (/no potential/.test(x)) return "np";
  if (/call again/.test(x)) return "ca";
  if (/recall/.test(x)) return "recall";
  if (/no answer/.test(x)) return "na";
  return x.trim();
}

function main() {
  const verbose = process.argv.includes("--verbose");
  const g = loadGuards();
  const cases = fs
    .readFileSync(CASES, "utf8")
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l));

  let pass = 0;
  const failures = [];

  for (const c of cases) {
    const row = {
      "Suggested Status": c.engine_status,
      "Matched Keyword": c.keyword || "",
      "Decision Source": c.source || "policy:callback",
      Reason: c.reason || "",
      "customer status": c.crm_status || c.engine_status,
      "last 10 comments": c.comments,
    };
    const fix = g.deterministicContextFix(row);
    const gotStatus = fix ? fix.status : c.engine_status;
    const gotTag = fix ? fix.tag : "";
    const folded = g.foldComments(row);
    const blocked = c.llm_correct_status
      ? g.verifierOverrideBlocked(c.engine_status, c.llm_correct_status, folded)
      : null;

    const statusOk = normFam(gotStatus) === normFam(c.expect_status);
    const tagOk = !c.expect_tag || gotTag === c.expect_tag;
    const blockOk = c.expect_block == null || blocked === c.expect_block;
    const ok = statusOk && tagOk && blockOk;

    if (ok) pass++;
    else failures.push({ c, gotStatus, gotTag, blocked });
    if (verbose || !ok) {
      console.log(
        `${ok ? "PASS" : "FAIL"} ${c.id} want=${c.expect_status}` +
          (c.expect_tag ? "/" + c.expect_tag : "") +
          (c.expect_block ? " block=" + c.expect_block : "") +
          ` got=${gotStatus}` +
          (gotTag ? "/" + gotTag : "") +
          (blocked ? " block=" + blocked : "")
      );
    }
  }

  console.log(`\nverifier_guard_harness: ${pass}/${cases.length} pass, ${failures.length} fail`);
  process.exit(failures.length ? 1 : 0);
}

main();
