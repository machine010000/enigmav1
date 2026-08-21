import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  clientName,
  messagesForProject,
  operationLabel,
  projectCandidates,
  projectSnapshot,
  verificationFrom,
} from "../app/components/freelancer-chat-model.ts";
import { parseApiErrorPayload } from "../app/lib/api.ts";

const messages = [
  { message_id: "a-user", role: "user", project_id: "a", content: "Project A" },
  { message_id: "a-analysis", role: "assistant", project_id: "a", content: "Analysis", created_at: "2026-01-01T00:00:00Z", result: { suitability_score: 0.84, recommendation: "apply", product_verification: { recommendation: "review", confidence: 0.8, risks: ["timeline"], missing_information: [] } } },
  { message_id: "b-proposal", role: "assistant", project_id: "b", content: "B proposal", result: { proposal_version: 4, proposal_text: "Private B" } },
  { message_id: "a-proposal", role: "assistant", project_id: "a", content: "A proposal", created_at: "2026-01-02T00:00:00Z", result: { proposal_version: 2, proposal_text: "Private A", proposal_readiness: true, verification: { recommendation: "pass", confidence: 0.92, risks: [], missing_information: [] } } },
];

test("project switching never keeps another project's messages", () => {
  assert.deepEqual(messagesForProject(messages, "a").map((item) => item.message_id), ["a-user", "a-analysis", "a-proposal"]);
  assert.deepEqual(messagesForProject(messages, "b").map((item) => item.message_id), ["b-proposal"]);
  assert.equal(messagesForProject(messages, "").length, 4);
});

test("current project context is derived from durable backend results", () => {
  const snapshot = projectSnapshot("a", messages);
  assert.equal(snapshot.suitabilityScore, 0.84);
  assert.equal(snapshot.recommendation, "apply");
  assert.equal(snapshot.proposalVersions, 2);
  assert.equal(snapshot.proposalReady, true);
  assert.equal(snapshot.verification?.recommendation, "pass");
  assert.equal(snapshot.lastActivity, "2026-01-02T00:00:00Z");
});

test("verification and ambiguity remain structured", () => {
  assert.deepEqual(verificationFrom(messages[1].result), { recommendation: "review", confidence: 0.8, risks: ["timeline"], missingInformation: [], allowed: undefined });
  assert.deepEqual(projectCandidates({ project_resolution: { ambiguity: true, candidate_projects: [{ project_id: "a", title: "Alpha", platform: "upwork", confidence: 0.9 }] } }), [{ project_id: "a", title: "Alpha", platform: "upwork", confidence: 0.9 }]);
});

test("TASK-066 duplicate responses remain structured for Chat", () => {
  assert.deepEqual(
    parseApiErrorPayload({ detail: { code: "duplicate_opportunity", existing_job_id: "job-existing" } }, "Conflict"),
    { message: "Conflict", code: "duplicate_opportunity", existingJobId: "job-existing" },
  );
  assert.deepEqual(parseApiErrorPayload({ detail: [{ loc: ["body"] }] }, "Invalid"), { message: "Some submitted fields are invalid." });
});

test("client names and loading labels are truthful", () => {
  assert.equal(clientName({ project_id: "a", title: "A", platform: "upwork", lifecycle_status: "new", client: { name: "Client A" } }), "Client A");
  assert.equal(operationLabel("Generate a proposal"), "Generating a proposal draft…");
  assert.equal(operationLabel("Client said hello"), "Reviewing the client message…");
  assert.equal(operationLabel("x".repeat(181)), "Analyzing the opportunity…");
});

test("chat UI contains manual controls and no marketplace submit control", async () => {
  const source = await readFile(new URL("../app/components/freelancer-chat.tsx", import.meta.url), "utf8");
  assert.match(source, /Copy proposal/);
  assert.match(source, /Request revision/);
  assert.match(source, /No automatic submission/);
  assert.match(source, /Academy learning/);
  assert.match(source, /Creativity:/);
  assert.match(source, /Product verification/);
  assert.match(source, /Choose the intended project/);
  assert.doesNotMatch(source, />Submit to (Freelancer|Upwork)</);
});
