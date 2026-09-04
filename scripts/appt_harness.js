#!/usr/bin/env node
// Checks the "Apply Appointment" guards outside n8n: a stale callback, a bogus appointment time
// or a refusal-locked decision must never turn a lead back into Call Again.
//
//   node scripts/appt_harness.js
//
// Cases come from evals/appointment_cases.jsonl: each row is a lead the appointment AI flagged
// as an appointment, plus the status Memory Match had already decided.

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const WORKFLOW = path.join(ROOT, "n8n-import", "05-V2-smart-upgraded.workflow.json");
const CASES = path.join(ROOT, "evals", "appointment_cases.jsonl");

function applyAppointment(rows, apptResults) {
  const wf = JSON.parse(fs.readFileSync(WORKFLOW, "utf8"));
  const code = wf.nodes.find((n) => n.name === "Apply Appointment").parameters.jsCode;
  const sandbox = {
    $input: { all: () => [{ json: { output: JSON.stringify(apptResults) } }] },
    $: (name) => {
      if (name !== "Code in JavaScript1") throw new Error(`unexpected node ref: ${name}`);
      return { all: () => rows.map((json) => ({ json })) };
    },
    console,
  };
  return vm.runInNewContext(`(function(){${code}})()`, sandbox, { timeout: 30000 }).map((o) => o.json);
}

const cases = fs.readFileSync(CASES, "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
const rows = cases.map((c) => ({
  "account no": c["account no"],
  "customer status": c["customer status"],
  "last 10 comments": c["last 10 comments"],
  "Suggested Status": c.memory_match_status,
  "Decision Source": c.memory_match_source || "",
  Reason: c.memory_match_reason || "",
}));
const appt = cases.map((c) => ({
  id: c["account no"],
  appointment_detected: "yes",
  status: "Scheduled",
  when: c.ai_when,
  detail: c.ai_when,
}));

const out = applyAppointment(rows, appt);
let pass = 0;
const failures = [];
for (const c of cases) {
  const got = out.find((o) => o["account no"] === c["account no"]);
  const status = String(got["Suggested Status"] || "");
  if (status === c.expect_status) pass++;
  else failures.push(`FAIL ${c["account no"]} want=${c.expect_status} got=${status} (${got["Appointment Status"]})`);
}
failures.forEach((f) => console.log(f));
console.log(`\nappt_harness: ${pass}/${cases.length} pass, ${failures.length} fail`);
process.exit(failures.length ? 1 : 0);
