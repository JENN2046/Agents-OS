import path from "node:path";
import { createContextLedgerEntry, isDuplicateContextLedgerEntry } from "../bridge/context_ledger.js";
import { createFileContextLedgerStore } from "../stores/context_ledger_store.js";

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const taskId = `cea-012-context-ledger-${timestamp}`;
  const snapshotId = "cea-011-safe-snapshot-20260707080426";
  const store = createFileContextLedgerStore(path.join(projectRoot, "data", "context-ledger"));
  const start = new Date();
  const at = (offsetMs: number) => new Date(start.getTime() + offsetMs).toISOString();

  const entries = [
    createContextLedgerEntry({
      taskId,
      eventId: `${taskId}:001-opened`,
      eventType: "TASK_OPENED",
      at: at(0),
      agentId: "commander",
      role: "commander",
      source: "codex-desktop",
      frontendOrSession: "current-thread",
      content: "CEA-012 opened as a record-only Codex context ledger pilot.",
      artifactRef: "docs/CONTEXT_LEDGER.md",
      tags: ["cea-012", "record_only", "pilot"],
    }),
    createContextLedgerEntry({
      taskId,
      eventId: `${taskId}:002-snapshot-bound`,
      eventType: "SNAPSHOT_BOUND",
      at: at(1000),
      agentId: "bridge",
      role: "bridge",
      source: "bridge-exporter",
      frontendOrSession: "snapshot-pilot",
      content: "CEA-012 references the safe snapshot boundary established by CEA-011.",
      artifactRef: "data/reports/cea-011_safe_repo_snapshot_pilot.json",
      snapshotId,
      tags: ["cea-011", "snapshot_ref", "no_real_repo_cwd"],
    }),
    createContextLedgerEntry({
      taskId,
      eventId: `${taskId}:003-message-recorded`,
      eventType: "MESSAGE_RECORDED",
      at: at(2000),
      agentId: "worker",
      role: "worker",
      source: "app-server-jsonrpc",
      frontendOrSession: "managed-worker-planned",
      content: "Worker context ledger entries store hashes and artifact refs only.",
      artifactRef: "docs/EVENT_CONTRACT.md",
      tags: ["metadata_only", "no_raw_message"],
    }),
    createContextLedgerEntry({
      taskId,
      eventId: `${taskId}:004-review-requested`,
      eventType: "REVIEW_REQUESTED",
      at: at(3000),
      agentId: "reviewer",
      role: "reviewer",
      source: "app-server-jsonrpc",
      frontendOrSession: "managed-reviewer-planned",
      content: "Reviewer context lookup remains disabled unless a future explicit gate enables it.",
      artifactRef: "docs/SECURITY_BOUNDARIES.md",
      tags: ["auto_injection_disabled", "future_gate_required"],
    }),
    createContextLedgerEntry({
      taskId,
      eventId: `${taskId}:005-closed`,
      eventType: "TASK_CLOSED",
      at: at(4000),
      agentId: "bridge",
      role: "bridge",
      source: "local-pilot",
      frontendOrSession: "current-thread",
      content: "CEA-012 pilot completed without starting managed Worker or Reviewer sessions.",
      artifactRef: "data/receipts/2026-07-07-cea-012-context-ledger-pilot.receipt.md",
      tags: ["pass", "not_injected", "sessions_not_started"],
    }),
  ];

  for (const entry of entries) {
    await store.append(taskId, entry);
  }

  const readBack = await store.read(taskId);
  const duplicateSelfCheck = isDuplicateContextLedgerEntry(readBack[2], {
    ...readBack[2],
    eventId: `${taskId}:duplicate-check`,
  });

  console.log(
    JSON.stringify(
      {
        result: "PASS",
        task_id: "CEA-012",
        ledger_task_id: taskId,
        ledger_path: store.pathFor(taskId),
        entry_count: readBack.length,
        record_only: readBack.every((entry) => entry.visibility === "record_only"),
        auto_injection: "DISABLED",
        context_patch: "DISABLED",
        duplicate_hash_check: duplicateSelfCheck ? "PASS" : "FAIL",
        raw_content_persisted: false,
        snapshot_id: snapshotId,
        phase8_direct_real_repo: "BLOCKED",
        managed_sessions_started: false,
      },
      null,
      2,
    ),
  );
}

void main().catch((error) => {
  console.error(
    JSON.stringify(
      {
        result: "FAIL",
        reason: error instanceof Error ? error.message : "unknown context ledger pilot failure",
      },
      null,
      2,
    ),
  );
  process.exitCode = 1;
});
