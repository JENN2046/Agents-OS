import { mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { createContextLedgerEntry } from "../../src/bridge/context_ledger.js";
import { buildContextPromotionPacket } from "../../src/bridge/context_promotion.js";
import {
  createPromotionApprovalReceipt,
  hashPromotionPacket,
  validatePromotionApprovalReceipt,
  verifyPromotionApprovalReceiptForPacket,
} from "../../src/bridge/promotion_approval.js";
import { createFilePromotionApprovalStore } from "../../src/stores/promotion_approval_store.js";

const tmpRoot = path.join(process.cwd(), "data", "tmp", "promotion-approval");

describe("promotion approval receipts", () => {
  it("creates a metadata-only approval receipt bound to a blocked packet hash", () => {
    const packet = samplePacket();
    const receipt = createPromotionApprovalReceipt(packet, {
      receiptId: "cea-014-approval-1",
      approvedByRole: "commander",
      approvedByAgentId: "commander-1",
      reason: "packet refs are scoped",
      evidence: ["docs/CONTEXT_PROMOTION_GATE.md"],
      approvedAt: "2026-07-07T00:00:01.000Z",
      createdAt: "2026-07-07T00:00:02.000Z",
    });

    expect(receipt.sourcePacketHash).toBe(hashPromotionPacket(packet));
    expect(receipt.statusBefore).toBe("BLOCKED_BY_DEFAULT");
    expect(receipt.statusAfter).toBe("APPROVED_FOR_PACKET_USE");
    expect(receipt.workerPromptUseAfter).toBe("APPROVED_PACKET_ONLY");
    expect(receipt.boundary.autoInjection).toBe("DISABLED");
    expect(receipt.boundary.rawContentIncluded).toBe(false);
    expect(validatePromotionApprovalReceipt(receipt)).toBe(true);
    expect(verifyPromotionApprovalReceiptForPacket(receipt, packet)).toBe(true);
  });

  it("rejects worker self-approval and raw content fields", () => {
    const packet = samplePacket();
    expect(() =>
      createPromotionApprovalReceipt(packet, {
        receiptId: "cea-014-approval-2",
        approvedByRole: "worker" as never,
        approvedByAgentId: "worker-1",
        reason: "self approve",
        evidence: ["packet"],
      }),
    ).toThrow("commander or reviewer");

    const receipt = createPromotionApprovalReceipt(packet, {
      receiptId: "cea-014-approval-3",
      approvedByRole: "reviewer",
      approvedByAgentId: "reviewer-1",
      reason: "reviewed",
      evidence: ["packet"],
    });
    expect(validatePromotionApprovalReceipt({ ...receipt, prompt: "raw prompt" })).toBe(false);
  });

  it("detects packet hash mismatch", () => {
    const packet = samplePacket();
    const otherPacket = buildContextPromotionPacket({
      packetId: "cea-013-packet-other",
      sourceLedgerTaskId: "cea-012-test",
      entries: [
        createContextLedgerEntry({
          taskId: "cea-012-test",
          eventId: "cea-012-test:other",
          eventType: "TASK_OPENED",
          agentId: "commander",
          role: "commander",
          source: "codex-desktop",
          frontendOrSession: "thread",
          content: "other metadata",
        }),
      ],
      query: { taskId: "cea-012-test" },
    });
    const receipt = createPromotionApprovalReceipt(packet, {
      receiptId: "cea-014-approval-4",
      approvedByRole: "reviewer",
      approvedByAgentId: "reviewer-1",
      reason: "reviewed",
      evidence: ["packet"],
    });

    expect(verifyPromotionApprovalReceiptForPacket(receipt, otherPacket)).toBe(false);
  });

  it("writes and reads approval receipts safely", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });
    const store = createFilePromotionApprovalStore(root);
    const receipt = createPromotionApprovalReceipt(samplePacket(), {
      receiptId: "cea-014-approval-store",
      approvedByRole: "reviewer",
      approvedByAgentId: "reviewer-1",
      reason: "reviewed",
      evidence: ["packet"],
    });

    const receiptPath = await store.write(receipt);
    expect(receiptPath.endsWith("cea-014-approval-store.approval.json")).toBe(true);
    await expect(store.read("cea-014-approval-store")).resolves.toEqual(receipt);
    await expect(store.write({ ...receipt, rawContentIncluded: true } as never)).rejects.toThrow("metadata-only");
  });
});

function samplePacket() {
  return buildContextPromotionPacket({
    packetId: "cea-013-packet-approval-source",
    sourceLedgerTaskId: "cea-012-test",
    entries: [
      createContextLedgerEntry({
        taskId: "cea-012-test",
        eventId: "cea-012-test:001",
        eventType: "TASK_OPENED",
        at: "2026-07-07T00:00:00.000Z",
        agentId: "commander",
        role: "commander",
        source: "codex-desktop",
        frontendOrSession: "thread",
        content: "approval source metadata",
        artifactRef: "docs/CONTEXT_PROMOTION_GATE.md",
      }),
    ],
    query: { taskId: "cea-012-test" },
    createdAt: "2026-07-07T00:00:00.000Z",
  });
}
