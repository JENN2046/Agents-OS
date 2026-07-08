import { readFile } from "node:fs/promises";
import path from "node:path";
import { compilePromptAnnex } from "../bridge/prompt_annex.js";
import { createFileContextPacketStore } from "../stores/context_packet_store.js";
import { createFilePromotionApprovalStore } from "../stores/promotion_approval_store.js";
import { createFilePromptAnnexStore } from "../stores/prompt_annex_store.js";

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
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const annexId = `cea-015-prompt-annex-${timestamp}`;
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

  console.log(
    JSON.stringify(
      {
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
        reason: error instanceof Error ? error.message : "unknown prompt annex pilot failure",
      },
      null,
      2,
    ),
  );
  process.exitCode = 1;
});
