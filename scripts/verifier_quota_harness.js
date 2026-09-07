#!/usr/bin/env node
// Conflict J — Verifier quota: all Wrong + all fragile skipAI Correct must survive the cap.
//
//   node scripts/verifier_quota_harness.js

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const WORKFLOW = path.join(ROOT, "n8n-import", "05-V2-smart-upgraded.workflow.json");

function loadFns() {
  const wf = JSON.parse(fs.readFileSync(WORKFLOW, "utf8"));
  const node = wf.nodes.find((n) => n.name === "Build Verify Batches");
  const code = node.parameters.jsCode;
  const start = code.indexOf("function fragileBlob");
  const end = code.indexOf("function priorityScore");
  if (start < 0) throw new Error("fragileBlob missing");
  // Grab fragileBlob + isFragileSkipAI + priorityScore
  const end2 = code.indexOf("\nconst candidates");
  const prelude = code.slice(start, end2) + "\nmodule.exports = { fragileBlob, isFragileSkipAI, priorityScore };\n";
  const sandbox = { module: { exports: {} }, exports: {} };
  vm.runInNewContext(prelude, sandbox, { timeout: 3000 });
  return sandbox.module.exports;
}

function selectTargets(rows, fns) {
  // Mirror Build Verify Batches quota merge
  const candidates = rows.map((r) => ({
    row: r,
    score: fns.priorityScore(r),
    payload: { id: r["account no"] },
  }));
  candidates.sort((a, b) => b.score - a.score);
  const isWrong = (c) => String(c.row["Validation Result"] || "").trim().toLowerCase() === "wrong";
  const wrongs = candidates.filter(isWrong);
  const others = candidates.filter((c) => !isWrong(c));
  const fragiles = others.filter((c) => fns.isFragileSkipAI(c.row));
  const rest = others.filter((c) => !fns.isFragileSkipAI(c.row));
  const MAX_OTHER = 80;
  return {
    targets: wrongs.concat(fragiles).concat(rest.slice(0, MAX_OTHER)).map((c) => c.payload.id),
    wrongs: wrongs.length,
    fragiles: fragiles.length,
    restKept: Math.min(rest.length, MAX_OTHER),
    restDropped: Math.max(0, rest.length - MAX_OTHER),
  };
}

function main() {
  const fns = loadFns();
  // Build a crowded batch: 30 Wrong no_money + 25 fragile Correct + 120 plain Correct
  const rows = [];
  for (let i = 0; i < 30; i++) {
    rows.push({
      "account no": `W${i}`,
      "Validation Result": "Wrong",
      "Decision Source": "Policy: no_money",
      Reason: "policy no_money => No Potential",
      "Matched Keyword": "no money",
      "Suggested Status": "No Potential",
    });
  }
  for (let i = 0; i < 25; i++) {
    rows.push({
      "account no": `F${i}`,
      "Validation Result": "Correct",
      "Decision Source": "Policy: money_with_funding_plan",
      Reason: "policy money_with_funding_plan => Call Again",
      "Matched Keyword": "salary",
      "Suggested Status": "Call Again",
      skipAI: true,
    });
  }
  for (let i = 0; i < 120; i++) {
    rows.push({
      "account no": `C${i}`,
      "Validation Result": "Correct",
      "Decision Source": "Sheet rule (row 400)",
      Reason: "Sheet row 400 trigger 'dvm' => No Answer 1-5",
      "Matched Keyword": "dvm",
      "Suggested Status": "No Answer 1-5",
      skipAI: true,
    });
  }

  const out = selectTargets(rows, fns);
  const ids = new Set(out.targets);
  const missingWrong = rows.filter((r) => r["Validation Result"] === "Wrong" && !ids.has(r["account no"]));
  const missingFragile = rows.filter(
    (r) => String(r["account no"]).startsWith("F") && !ids.has(r["account no"])
  );
  const plainKept = rows.filter((r) => String(r["account no"]).startsWith("C") && ids.has(r["account no"])).length;

  let fail = 0;
  if (missingWrong.length) {
    console.log("FAIL Wrong dropped", missingWrong.map((r) => r["account no"]).slice(0, 5));
    fail++;
  } else console.log("PASS all Wrong kept", out.wrongs);
  if (missingFragile.length) {
    console.log("FAIL fragile Correct dropped", missingFragile.map((r) => r["account no"]).slice(0, 5));
    fail++;
  } else console.log("PASS all fragile skipAI Correct kept", out.fragiles);
  if (plainKept !== 80) {
    console.log("FAIL plain Correct kept expected 80 got", plainKept, "dropped", out.restDropped);
    fail++;
  } else console.log("PASS plain Correct capped at 80 (dropped", out.restDropped + ")");

  // Sanity: fragile detector
  if (!fns.isFragileSkipAI(rows[30])) {
    console.log("FAIL isFragileSkipAI false on funding plan");
    fail++;
  } else console.log("PASS isFragileSkipAI on money_with_funding_plan");

  console.log(`\nverifier_quota_harness: ${fail ? "FAIL" : "PASS"} (targets=${out.targets.length})`);
  process.exit(fail ? 1 : 0);
}

main();
