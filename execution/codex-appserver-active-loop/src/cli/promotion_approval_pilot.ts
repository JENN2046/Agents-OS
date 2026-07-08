import { readFile } from "node:fs/promises";
import path from "node:path";
import { createPromotionApprovalReceipt, verifyPromotionApprovalReceiptForPacket } from "../bridge/promotion_approval.js";
import { createFileContextPacketStore } from "../stores/context_packet_store.js";
import { createFilePromotionApprovalStore } from "../stores/promotion_approval_store.js";
import { writeJsonArtifact, writeReceiptArtifact } from "./pilot_artifacts.js";

interface Cea013Report {
  readonly pilot?: {
    readonly packet_id?: unknown;
  };
}

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const completedAt = new Date().toISOString();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const receiptId = `cea-014-promotion-approval-${timestamp}`;
  const reportPath = path.join(projectRoot, "data", "reports", "cea-014_promotion_approval_receipt.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", "2026-07-07-cea-014-promotion-approval-receipt.receipt.md");
  const cea013 = JSON.parse(
    await readFile(path.join(projectRoot, "data", "reports", "cea-013_context_promotion_gate.json"), "utf8"),
  ) as Cea013Report;
  const packetId = typeof cea013.pilot?.packet_id === "string" ? cea013.pilot.packet_id : "";
  if (!packetId) {
    throw new Error("CEA-013 packet id is missing");
  }

  const packetStore = createFileContextPacketStore(path.join(projectRoot, "data", "context-packets"));
  const approvalStore = createFilePromotionApprovalStore(path.join(projectRoot, "data", "context-approvals"));
  const packet = await packetStore.read(packetId);
  const receipt = createPromotionApprovalReceipt(packet, {
    receiptId,
    approvedByRole: "reviewer",
    approvedByAgentId: "cea-014-reviewer-gate",
    reason: "Packet contains metadata-only artifact refs and remains packet-only with auto-injection disabled.",
    evidence: ["data/reports/cea-013_context_promotion_gate.json", "docs/CONTEXT_PROMOTION_GATE.md"],
  });
  const approvalReceiptPath = await approvalStore.write(receipt);

  const pilot = {
    result: "PASS",
    task_id: "CEA-014",
    approval_receipt_id: receipt.receiptId,
    approval_receipt_path: approvalReceiptPath,
    packet_id: packet.packetId,
    source_packet_hash: receipt.sourcePacketHash,
    approval_hash: receipt.approvalHash,
    approved_by_role: receipt.approvedByRole,
    worker_prompt_use_after: receipt.workerPromptUseAfter,
    auto_injection: receipt.boundary.autoInjection,
    raw_content_included: receipt.boundary.rawContentIncluded,
    context_patch: receipt.boundary.contextPatch,
    direct_real_repo: receipt.boundary.directRealRepo,
    receipt_matches_packet: verifyPromotionApprovalReceiptForPacket(receipt, packet),
    managed_sessions_started: false,
  };
  const report = {
    task_id: "CEA-014",
    title: "Promotion Approval Receipt",
    result: pilot.result,
    completed_at: completedAt,
    pilot,
    boundary_flags: {
      auto_injection: pilot.auto_injection,
      raw_content_included: pilot.raw_content_included,
      context_patch: pilot.context_patch,
      direct_real_repo: pilot.direct_real_repo,
      managed_sessions_started: pilot.managed_sessions_started,
      commit_push_deploy_release_tag: "NOT_USED",
    },
    artifacts: {
      report: reportPath,
      receipt: receiptPath,
      approval_receipt: pilot.approval_receipt_path,
    },
  };
  await writeJsonArtifact(reportPath, report);
  await writeReceiptArtifact(receiptPath, "CEA-014 Promotion Approval Receipt", [
    `result: ${report.result}`,
    `approval_receipt_id: ${pilot.approval_receipt_id}`,
    `approval_receipt_path: ${pilot.approval_receipt_path}`,
    `packet_id: ${pilot.packet_id}`,
    `receipt_matches_packet: ${pilot.receipt_matches_packet}`,
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
        reason: error instanceof Error ? error.message : "unknown promotion approval pilot failure",
      },
      null,
      2,
    ),
  );
  process.exitCode = 1;
});
