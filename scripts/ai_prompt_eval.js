#!/usr/bin/env node
/**
 * promptfoo-inspired offline eval for AI Agent + Verifier AI system prompts.
 *
 *   node scripts/ai_prompt_eval.js
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const WORKFLOW = path.join(ROOT, "n8n-import", "05-V2-smart-upgraded.workflow.json");
const FIXTURES = path.join(ROOT, "evals", "ai_prompt_fixtures.jsonl");

const CORE_STATUSES = [
  "Call Again",
  "Recall",
  "No Potential",
  "No Interest",
  "No Answer 1-5",
  "No Language",
  "Denied Registration",
  "Wrong Number or Email",
];

const ALLOWED = new Set([
  ...CORE_STATUSES,
  "No Answer 5 UP",
  "Under 18",
  "Invalid Country",
  "Keep CRM",
  "Manual Check",
  "Decline",
  "Duplicate",
  "DNC",
]);

const REQUIRED_AI = [
  /CANONICAL MONEY\s*\/\s*CALLBACK\s*\/\s*REFUSAL TREE/i,
  /Hard money|hard money/i,
  /Soft money|soft money/i,
  /Agent dial notes alone|NOT customer callbacks|are NOT customer callbacks/i,
  /UNTRUSTED/i,
  /OUTPUT FORMAT/i,
  /ALLOWED SUGGESTED STATUS VALUES/i,
  /Suggested Status/,
  /account no/,
];

const REQUIRED_VERIFIER = [
  /MATCH CONTEXT AUDITOR/i,
  /FULL SENTENCE/i,
  /agree|disagree/i,
  /JSON array/i,
  /ALLOWED correct_status VALUES/i,
];

function loadPrompt(nodeName) {
  const wf = JSON.parse(fs.readFileSync(WORKFLOW, "utf8"));
  const node = wf.nodes.find((n) => n.name === nodeName);
  if (!node) throw new Error("missing node: " + nodeName);
  const sm = (node.parameters && node.parameters.options && node.parameters.options.systemMessage) || "";
  if (!sm) throw new Error("empty systemMessage: " + nodeName);
  return sm;
}

function checkClauses(label, text, clauses) {
  const fails = [];
  for (const re of clauses) {
    if (!re.test(text)) fails.push(String(re));
  }
  return { label, ok: fails.length === 0, fails, length: text.length };
}

function validateFixture(fx, i) {
  const errors = [];
  const batch = fx.expect_batch;
  if (!Array.isArray(batch)) return { ok: false, id: fx.id || i, errors: ["expect_batch not array"] };
  for (let j = 0; j < batch.length; j++) {
    const o = batch[j];
    if (!o || typeof o !== "object") {
      errors.push(`item ${j}: not object`);
      continue;
    }
    if (!o["account no"]) errors.push(`item ${j}: missing account no`);
    const vr = o["Validation Result"];
    if (!["Correct", "Wrong", "Manual Check"].includes(vr)) {
      errors.push(`item ${j}: bad Validation Result ${vr}`);
    }
    if (!ALLOWED.has(o["Suggested Status"])) {
      errors.push(`item ${j}: bad Suggested Status ${o["Suggested Status"]}`);
    }
  }
  if (fx.expect_count != null && batch.length !== fx.expect_count) {
    errors.push(`count ${batch.length} != ${fx.expect_count}`);
  }
  if (fx.rule === "soft_money_not_np") {
    for (const o of batch) {
      if (o["Suggested Status"] === "No Potential") errors.push("soft_money_not_np violated");
    }
  }
  if (fx.rule === "agent_dial_not_callback") {
    for (const o of batch) {
      if (o["Suggested Status"] === "Call Again") {
        errors.push("agent_dial_not_callback: unexpected Call Again");
      }
    }
  }
  return { ok: errors.length === 0, id: fx.id || `fx${i}`, errors };
}

function main() {
  const ai = loadPrompt("AI Agent");
  const ver = loadPrompt("Verifier AI");
  const checks = [
    checkClauses("AI Agent", ai, REQUIRED_AI),
    checkClauses("Verifier AI", ver, REQUIRED_VERIFIER),
  ];
  const vocabOk = CORE_STATUSES.every((s) => ai.includes(s));
  const fixtures = fs.existsSync(FIXTURES)
    ? fs.readFileSync(FIXTURES, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l))
    : [];
  const fixtureResults = fixtures.map(validateFixture);
  const fixtureFails = fixtureResults.filter((r) => !r.ok);

  let failed = 0;
  for (const c of checks) {
    if (!c.ok) {
      failed++;
      console.log(`FAIL ${c.label} missing:\n  - ${c.fails.join("\n  - ")}`);
    } else console.log(`PASS ${c.label} gantry clauses (${c.length} chars)`);
  }
  if (!vocabOk) {
    failed++;
    console.log(
      "FAIL AI core status vocabulary missing: " +
        CORE_STATUSES.filter((s) => !ai.includes(s)).join(", ")
    );
  } else console.log("PASS AI core status vocabulary present");

  console.log(`fixtures: ${fixtureResults.length - fixtureFails.length}/${fixtureResults.length} pass`);
  for (const f of fixtureFails) {
    failed++;
    console.log(`FAIL fixture ${f.id}: ${f.errors.join("; ")}`);
  }
  console.log(`\nai_prompt_eval: ${failed ? "FAIL" : "PASS"} (promptfoo-style)`);
  process.exit(failed ? 1 : 0);
}

main();
