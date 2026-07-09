import { readFile } from "node:fs/promises";
import path from "node:path";
import { buildContextPromotionPacket } from "../bridge/context_promotion.js";
import { createFileContextLedgerStore } from "../stores/context_ledger_store.js";
import { createFileContextPacketStore } from "../stores/context_packet_store.js";
import { writeJsonArtifact, writeReceiptArtifact } from "./pilot_artifacts.js";

interface Cea012Report {
  readonly pilot?: {
    readonly ledger_task_id?: unknown;
  };
}

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const completedAt = new Date().toISOString();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const packetId = `cea-013-context-packet-${timestamp}`;
  const reportPath = path.join(projectRoot, "data", "reports", "cea-013_context_promotion_gate.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", "2026-07-07-cea-013-context-promotion-gate.receipt.md");
  const cea012 = JSON.parse(
    await readFile(path.join(projectRoot, "data", "reports", "cea-012_context_ledger_pilot.json"), "utf8"),
  ) as Cea012Report;
  const ledgerTaskId = typeof cea012.pilot?.ledger_task_id === "string" ? cea012.pilot.ledger_task_id : "";
  if (!ledgerTaskId) {
    throw new Error("CEA-012 ledger task id is missing");
  }

  const ledgerStore = createFileContextLedgerStore(path.join(projectRoot, "data", "context-ledger"));
  const packetStore = createFileContextPacketStore(path.join(projectRoot, "data", "context-packets"));
  const entries = await ledgerStore.read(ledgerTaskId);
  const packet = buildContextPromotionPacket({
    packetId,
    sourceLedgerTaskId: ledgerTaskId,
    entries,
    query: { taskId: ledgerTaskId },
  });
  const packetPath = await packetStore.write(packet);

  const pilot = {
    result: "PASS",
    task_id: "CEA-013",
    packet_id: packet.packetId,
    packet_path: packetPath,
    source_ledger_task_id: ledgerTaskId,
    entry_ref_count: packet.entryRefs.length,
    artifact_ref_count: packet.artifactRefs.length,
    snapshot_ids: packet.snapshotIds,
    status: packet.status,
    worker_prompt_use: packet.workerPromptUse,
    auto_injection: packet.boundary.autoInjection,
    approval_required: packet.boundary.approvalRequired,
    raw_content_included: packet.rawContentIncluded,
    phase8_direct_real_repo: packet.boundary.directRealRepo,
    managed_sessions_started: false,
    approval_applied: false,
  };
  const report = {
    task_id: "CEA-013",
    title: "Context Promotion Gate",
    result: pilot.result,
    completed_at: completedAt,
    pilot,
    boundary_flags: {
      auto_injection: pilot.auto_injection,
      approval_required: pilot.approval_required,
      raw_content_included: pilot.raw_content_included,
      phase8_direct_real_repo: pilot.phase8_direct_real_repo,
      managed_sessions_started: pilot.managed_sessions_started,
      commit_push_deploy_release_tag: "NOT_USED",
    },
    artifacts: {
      report: reportPath,
      receipt: receiptPath,
      packet: pilot.packet_path,
    },
  };
  await writeJsonArtifact(reportPath, report);
  await writeReceiptArtifact(receiptPath, "CEA-013 Context Promotion Gate Receipt", [
    `result: ${report.result}`,
    `packet_id: ${pilot.packet_id}`,
    `packet_path: ${pilot.packet_path}`,
    `source_ledger_task_id: ${pilot.source_ledger_task_id}`,
    `status: ${pilot.status}`,
    `approval_required: ${pilot.approval_required}`,
    `raw_content_included: ${pilot.raw_content_included}`,
    `phase8_direct_real_repo: ${pilot.phase8_direct_real_repo}`,
  ]);
  console.log(JSON.stringify(report, null, 2));
}

void main().catch((error) => {
  console.error(
    JSON.stringify(
      {
        result: "FAIL",
        reason: error instanceof Error ? error.message : "unknown context promotion pilot failure",
      },
      null,
      2,
    ),
  );
  process.exitCode = 1;
});
