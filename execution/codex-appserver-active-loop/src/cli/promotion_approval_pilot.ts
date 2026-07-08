import { readFile } from "node:fs/promises";
import path from "node:path";
import { createPromotionApprovalReceipt, verifyPromotionApprovalReceiptForPacket } from "../bridge/promotion_approval.js";
import { createFileContextPacketStore } from "../stores/context_packet_store.js";
import { createFilePromotionApprovalStore } from "../stores/promotion_approval_store.js";

interface Cea013Report {
  readonly pilot?: {
    readonly packet_id?: unknown;
  };
}

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const receiptId = `cea-014-promotion-approval-${timestamp}`;
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
  const receiptPath = await approvalStore.write(receipt);

  console.log(
    JSON.stringify(
      {
        result: "PASS",
        task_id: "CEA-014",
        approval_receipt_id: receipt.receiptId,
        approval_receipt_path: receiptPath,
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
        reason: error instanceof Error ? error.message : "unknown promotion approval pilot failure",
      },
      null,
      2,
    ),
  );
  process.exitCode = 1;
});
