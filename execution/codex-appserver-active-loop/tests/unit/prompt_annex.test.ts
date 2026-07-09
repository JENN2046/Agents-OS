import { mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { createContextLedgerEntry } from "../../src/bridge/context_ledger.js";
import { buildContextPromotionPacket } from "../../src/bridge/context_promotion.js";
import { createPromotionApprovalReceipt } from "../../src/bridge/promotion_approval.js";
import { compilePromptAnnex, validatePromptAnnex } from "../../src/bridge/prompt_annex.js";
import { createFilePromptAnnexStore } from "../../src/stores/prompt_annex_store.js";

const tmpRoot = path.join(process.cwd(), "data", "tmp", "prompt-annex");

describe("prompt annex compiler", () => {
  it("compiles approved packet metadata into a dry-run annex", () => {
    const { packet, approval } = samplePacketAndApproval();
    const annex = compilePromptAnnex(packet, approval, {
      annexId: "cea-015-annex-1",
      createdAt: "2026-07-07T00:00:01.000Z",
    });

    expect(annex.mode).toBe("DRY_RUN");
    expect(annex.workerPromptUse).toBe("APPROVED_PACKET_ONLY");
    expect(annex.autoInject).toBe(false);
    expect(annex.rawContentIncluded).toBe(false);
    expect(annex.boundary.approvalVerified).toBe(true);
    expect(annex.boundary.managedSessionStarted).toBe(false);
    expect(annex.entrySummaries).toHaveLength(2);
    expect(annex.artifactRefs).toEqual(["docs/CONTEXT_PROMOTION_GATE.md"]);
    expect(annex.snapshotIds).toEqual(["cea-011-safe-snapshot-20260707080426"]);
    expect(JSON.stringify(annex)).not.toContain("raw worker detail");
    expect(validatePromptAnnex(annex)).toBe(true);
  });

  it("rejects unbound approval receipts and raw fields", () => {
    const { packet, approval } = samplePacketAndApproval();
    const otherPacket = buildContextPromotionPacket({
      packetId: "cea-013-other-packet",
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

    expect(() => compilePromptAnnex(otherPacket, approval, { annexId: "cea-015-annex-2" })).toThrow("bound");
    const annex = compilePromptAnnex(packet, approval, { annexId: "cea-015-annex-3" });
    expect(validatePromptAnnex({ ...annex, response: "raw response" })).toBe(false);
  });

  it("writes and reads annex files safely", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });
    const store = createFilePromptAnnexStore(root);
    const { packet, approval } = samplePacketAndApproval();
    const annex = compilePromptAnnex(packet, approval, { annexId: "cea-015-annex-store" });

    const annexPath = await store.write(annex);
    expect(annexPath.endsWith("cea-015-annex-store.prompt-annex.json")).toBe(true);
    await expect(store.read("cea-015-annex-store")).resolves.toEqual(annex);
    await expect(store.write({ ...annex, rawContentIncluded: true } as never)).rejects.toThrow("dry run");
  });
});

function samplePacketAndApproval() {
  const packet = buildContextPromotionPacket({
    packetId: "cea-013-packet-annex-source",
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
        content: "annex source metadata",
        artifactRef: "docs/CONTEXT_PROMOTION_GATE.md",
      }),
      createContextLedgerEntry({
        taskId: "cea-012-test",
        eventId: "cea-012-test:002",
        eventType: "SNAPSHOT_BOUND",
        at: "2026-07-07T00:00:01.000Z",
        agentId: "bridge",
        role: "bridge",
        source: "bridge-exporter",
        frontendOrSession: "snapshot",
        content: "raw worker detail should never persist",
        snapshotId: "cea-011-safe-snapshot-20260707080426",
      }),
    ],
    query: { taskId: "cea-012-test" },
    createdAt: "2026-07-07T00:00:00.000Z",
  });
  const approval = createPromotionApprovalReceipt(packet, {
    receiptId: "cea-014-annex-approval",
    approvedByRole: "reviewer",
    approvedByAgentId: "reviewer-1",
    reason: "packet-only use approved",
    evidence: ["docs/PROMOTION_APPROVAL_RECEIPT.md"],
    createdAt: "2026-07-07T00:00:00.000Z",
  });
  return { packet, approval };
}
