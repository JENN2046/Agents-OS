import { readFile } from "node:fs/promises";
import path from "node:path";
import { compilePromptAnnex } from "../bridge/prompt_annex.js";
import { createFileContextPacketStore } from "../stores/context_packet_store.js";
import { createFilePromotionApprovalStore } from "../stores/promotion_approval_store.js";
import { createFilePromptAnnexStore } from "../stores/prompt_annex_store.js";
import { writeJsonArtifact, writeReceiptArtifact } from "./pilot_artifacts.js";

interface Cea013Report {
  readonly pilot?: {
    readonly packet_id?: unknown;
  };
}

interface Cea014Report {
  readonly pilot?: {
    readonly approval_receipt_id?: unknown;
  };
}

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const completedAt = new Date().toISOString();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const annexId = `cea-015-prompt-annex-${timestamp}`;
  const reportPath = path.join(projectRoot, "data", "reports", "cea-015_prompt_packet_compiler.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", "2026-07-07-cea-015-prompt-packet-compiler.receipt.md");
  const cea013 = JSON.parse(
    await readFile(path.join(projectRoot, "data", "reports", "cea-013_context_promotion_gate.json"), "utf8"),
  ) as Cea013Report;
  const cea014 = JSON.parse(
    await readFile(path.join(projectRoot, "data", "reports", "cea-014_promotion_approval_receipt.json"), "utf8"),
  ) as Cea014Report;
  const packetId = typeof cea013.pilot?.packet_id === "string" ? cea013.pilot.packet_id : "";
  const approvalReceiptId = typeof cea014.pilot?.approval_receipt_id === "string" ? cea014.pilot.approval_receipt_id : "";
  if (!packetId || !approvalReceiptId) {
    throw new Error("CEA-013 packet id or CEA-014 approval receipt id is missing");
  }

  const packetStore = createFileContextPacketStore(path.join(projectRoot, "data", "context-packets"));
  const approvalStore = createFilePromotionApprovalStore(path.join(projectRoot, "data", "context-approvals"));
  const annexStore = createFilePromptAnnexStore(path.join(projectRoot, "data", "prompt-annexes"));
  const packet = await packetStore.read(packetId);
  const approval = await approvalStore.read(approvalReceiptId);
  const annex = compilePromptAnnex(packet, approval, { annexId });
  const annexPath = await annexStore.write(annex);

  const pilot = {
    result: "PASS",
    task_id: "CEA-015",
    annex_id: annex.annexId,
    annex_path: annexPath,
    source_packet_id: annex.sourcePacketId,
    approval_receipt_id: annex.approvalReceiptId,
    entry_summary_count: annex.entrySummaries.length,
    artifact_ref_count: annex.artifactRefs.length,
    snapshot_ids: annex.snapshotIds,
    mode: annex.mode,
    worker_prompt_use: annex.workerPromptUse,
    approval_verified: annex.boundary.approvalVerified,
    source_packet_hash_verified: annex.boundary.sourcePacketHashVerified,
    auto_injection: annex.boundary.autoInjection,
    raw_content_included: annex.rawContentIncluded,
    direct_real_repo: annex.boundary.directRealRepo,
    managed_session_started: annex.boundary.managedSessionStarted,
  };
  const report = {
    task_id: "CEA-015",
    title: "Prompt Packet Compiler",
    result: pilot.result,
    completed_at: completedAt,
    pilot,
    boundary_flags: {
      auto_injection: pilot.auto_injection,
      raw_content_included: pilot.raw_content_included,
      direct_real_repo: pilot.direct_real_repo,
      managed_session_started: pilot.managed_session_started,
      commit_push_deploy_release_tag: "NOT_USED",
    },
    artifacts: {
      report: reportPath,
      receipt: receiptPath,
      annex: pilot.annex_path,
    },
  };
  await writeJsonArtifact(reportPath, report);
  await writeReceiptArtifact(receiptPath, "CEA-015 Prompt Packet Compiler Receipt", [
    `result: ${report.result}`,
    `annex_id: ${pilot.annex_id}`,
    `annex_path: ${pilot.annex_path}`,
    `source_packet_id: ${pilot.source_packet_id}`,
    `approval_verified: ${pilot.approval_verified}`,
    `raw_content_included: ${pilot.raw_content_included}`,
    `direct_real_repo: ${pilot.direct_real_repo}`,
  ]);
  console.log(JSON.stringify(report, null, 2));
}

void main().catch((error) => {
  console.error(
    JSON.stringify(
      {
        result: "FAIL",
        reason: error instanceof Error ? error.message : "unknown prompt annex pilot failure",
      },
      null,
      2,
    ),
  );
  process.exitCode = 1;
});
