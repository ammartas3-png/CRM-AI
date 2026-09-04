#!/usr/bin/env node
// Runs the n8n "Memory Match" node code outside n8n so its classification policy can be
// regression-tested against human-reviewed leads.
//
//   node scripts/mm_harness.js                      # run evals/wrong_review_cases.jsonl
//   node scripts/mm_harness.js --cases path.jsonl   # run another case file
//   node scripts/mm_harness.js --verbose            # print every case, not just failures
//
// The rules sheet snapshot lives in evals/rules_sheet.json (exported from the live
// Google Sheet). Memory Match reads leads and rules from the same input list.

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const WORKFLOW = path.join(ROOT, "n8n-import", "05-V2-smart-upgraded.workflow.json");
const RULES = path.join(ROOT, "evals", "rules_sheet.json");
const DEFAULT_CASES = path.join(ROOT, "evals", "wrong_review_cases.jsonl");

function nodeCode(name) {
  const wf = JSON.parse(fs.readFileSync(WORKFLOW, "utf8"));
  const node = wf.nodes.find((n) => n.name === name);
  if (!node) throw new Error(`node not found: ${name}`);
  return node.parameters.jsCode;
}

function runMemoryMatch(leads, rules) {
  const items = [...leads, ...rules].map((json) => ({ json }));
  const sandbox = {
    $input: { all: () => items },
    console,
    module: {},
  };
  const code = nodeCode("Memory Match");
  const out = vm.runInNewContext(`(function(){${code}})()`, sandbox, { timeout: 60000 });
  return out.map((o) => o.json);
}

function loadCases(file) {
  return fs
    .readFileSync(file, "utf8")
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l));
}

function main() {
  const argv = process.argv.slice(2);
  const verbose = argv.includes("--verbose");
  const casesIdx = argv.indexOf("--cases");
  const casesFile = casesIdx >= 0 ? argv[casesIdx + 1] : DEFAULT_CASES;

  const rules = JSON.parse(fs.readFileSync(RULES, "utf8"));
  const cases = loadCases(casesFile);
  const leads = cases.map((c) => ({
    "account no": c["account no"],
    "customer status": c["customer status"],
    "last 10 comments": c["last 10 comments"],
  }));

  const out = runMemoryMatch(leads, rules);
  const byAccount = new Map(out.map((o) => [o["account no"], o]));

  let pass = 0;
  const failures = [];
  for (const c of cases) {
    const got = byAccount.get(c["account no"]) || {};
    const status = String(got["Suggested Status"] || "");
    const want = String(c.expect_status || "");
    const ok = statusFamily(status) === statusFamily(want);
    if (ok) pass++;
    else failures.push({ c, status, reason: got.Reason || "" });
    if (verbose) {
      console.log(
        `${ok ? "PASS" : "FAIL"} ${c["account no"]} want=${want} got=${status}` +
          (ok ? "" : `\n      ${got.Reason || ""}`)
      );
    }
  }

  if (!verbose) {
    for (const f of failures) {
      console.log(
        `FAIL ${f.c["account no"]} want=${f.c.expect_status} got=${f.status}\n      ${f.reason}`
      );
    }
  }
  console.log(`\nmm_harness: ${pass}/${cases.length} pass, ${failures.length} fail`);
  process.exit(failures.length ? 1 : 0);
}

// "No Potential - no documents" and "No Potential" are the same decision family.
function statusFamily(s) {
  const x = String(s || "").trim().toLowerCase().replace(/\s+/g, " ");
  if (/no answer/.test(x) && /(5 ?up|five up)/.test(x)) return "no answer 5 up";
  if (/no answer/.test(x)) return "no answer 1-5";
  if (/no potential/.test(x)) return "no potential";
  if (/wrong number|wrong email/.test(x)) return "wrong number or email";
  if (/denied reg/.test(x)) return "denied registration";
  if (/no interest/.test(x)) return "no interest";
  if (/no language/.test(x)) return "no language";
  if (/manual/.test(x)) return "manual check";
  return x;
}

main();
