import { mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { createContextLedgerEntry } from "../../src/bridge/context_ledger.js";
import {
  approveContextPromotionPacket,
  assertContextPromotionPacket,
  buildContextPromotionPacket,
  queryContextLedger,
  validateContextPromotionPacket,
} from "../../src/bridge/context_promotion.js";
import { createFileContextPacketStore } from "../../src/stores/context_packet_store.js";

const tmpRoot = path.join(process.cwd(), "data", "tmp", "context-promotion");

describe("context promotion gate", () => {
  it("builds blocked-by-default metadata packets from ledger queries", () => {
    const entries = sampleEntries();
    const packet = buildContextPromotionPacket({
      packetId: "cea-013-packet-1",
      sourceLedgerTaskId: "cea-012-test",
      entries,
      query: { taskId: "cea-012-test" },
      createdAt: "2026-07-07T00:00:00.000Z",
    });

    expect(packet.status).toBe("BLOCKED_BY_DEFAULT");
    expect(packet.workerPromptUse).toBe("BLOCKED");
    expect(packet.autoInject).toBe(false);
    expect(packet.rawContentIncluded).toBe(false);
    expect(packet.entryRefs).toHaveLength(3);
    expect(packet.snapshotIds).toEqual(["cea-011-safe-snapshot-20260707080426"]);
    expect(packet.artifactRefs).toEqual(["data/reports/cea-011_safe_repo_snapshot_pilot.json", "docs/CONTEXT_LEDGER.md"]);
    expect(JSON.stringify(packet)).not.toContain("raw worker content");
    expect(validateContextPromotionPacket(packet)).toBe(true);
  });

  it("queries by role, tag, artifact, hash, and snapshot", () => {
    const entries = sampleEntries();
    const workerEntry = entries[1];

    expect(queryContextLedger(entries, { role: "worker" })).toEqual([workerEntry]);
    expect(queryContextLedger(entries, { tag: "snapshot_ref" })).toEqual([entries[2]]);
    expect(queryContextLedger(entries, { artifactRef: "docs/CONTEXT_LEDGER.md" })).toEqual([entries[0]]);
    expect(queryContextLedger(entries, { contentHash: workerEntry.contentHash })).toEqual([workerEntry]);
    expect(queryContextLedger(entries, { snapshotId: "cea-011-safe-snapshot-20260707080426" })).toEqual([entries[2]]);
  });

  it("requires commander or reviewer approval before packet use", () => {
    const packet = buildContextPromotionPacket({
      packetId: "cea-013-packet-approval",
      sourceLedgerTaskId: "cea-012-test",
      entries: sampleEntries(),
      query: { taskId: "cea-012-test" },
      createdAt: "2026-07-07T00:00:00.000Z",
    });

    expect(() =>
      approveContextPromotionPacket(packet, {
        approvedByRole: "worker" as never,
        approvedByAgentId: "worker-1",
        reason: "worker cannot self-promote",
        evidence: ["review"],
        approvedAt: "2026-07-07T00:00:01.000Z",
      }),
    ).toThrow("commander or reviewer");

    const approved = approveContextPromotionPacket(packet, {
      approvedByRole: "reviewer",
      approvedByAgentId: "reviewer-1",
      reason: "metadata packet is scoped and artifact-only",
      evidence: ["docs/CONTEXT_LEDGER.md"],
      approvedAt: "2026-07-07T00:00:01.000Z",
    });
    expect(approved.status).toBe("APPROVED_FOR_PACKET_USE");
    expect(approved.workerPromptUse).toBe("APPROVED_PACKET_ONLY");
    expect(approved.autoInject).toBe(false);
    expect(validateContextPromotionPacket(approved)).toBe(true);
  });

  it("rejects raw content fields and inconsistent approval state", () => {
    const packet = buildContextPromotionPacket({
      packetId: "cea-013-packet-invalid",
      sourceLedgerTaskId: "cea-012-test",
      entries: sampleEntries(),
      query: { taskId: "cea-012-test" },
    });

    expect(validateContextPromotionPacket({ ...packet, content: "raw text" })).toBe(false);
    expect(validateContextPromotionPacket({ ...packet, status: "APPROVED_FOR_PACKET_USE" })).toBe(false);
    expect(() => assertContextPromotionPacket({ ...packet, workerPromptUse: "APPROVED_PACKET_ONLY" })).toThrow("blocked by default");
  });

  it("writes and reads promotion packets safely", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });
    const store = createFileContextPacketStore(root);
    const packet = buildContextPromotionPacket({
      packetId: "cea-013-packet-store",
      sourceLedgerTaskId: "cea-012-test",
      entries: sampleEntries(),
      query: { taskId: "cea-012-test" },
      createdAt: "2026-07-07T00:00:00.000Z",
    });

    const packetPath = await store.write(packet);
    expect(packetPath.endsWith("cea-013-packet-store.context-packet.json")).toBe(true);
    await expect(store.read("cea-013-packet-store")).resolves.toEqual(packet);
    await expect(store.write({ ...packet, autoInject: true } as never)).rejects.toThrow("metadata-only");
  });
});

function sampleEntries() {
  return [
    createContextLedgerEntry({
      taskId: "cea-012-test",
      eventId: "cea-012-test:001",
      eventType: "TASK_OPENED",
      at: "2026-07-07T00:00:00.000Z",
      agentId: "commander",
      role: "commander",
      source: "codex-desktop",
      frontendOrSession: "current-thread",
      content: "open context ledger pilot",
      artifactRef: "docs/CONTEXT_LEDGER.md",
      tags: ["record_only"],
    }),
    createContextLedgerEntry({
      taskId: "cea-012-test",
      eventId: "cea-012-test:002",
      eventType: "MESSAGE_RECORDED",
      at: "2026-07-07T00:00:01.000Z",
      agentId: "worker-1",
      role: "worker",
      source: "app-server-jsonrpc",
      frontendOrSession: "thread-1",
      content: "raw worker content should never persist",
      tags: ["metadata_only"],
    }),
    createContextLedgerEntry({
      taskId: "cea-012-test",
      eventId: "cea-012-test:003",
      eventType: "SNAPSHOT_BOUND",
      at: "2026-07-07T00:00:02.000Z",
      agentId: "bridge",
      role: "bridge",
      source: "bridge-exporter",
      frontendOrSession: "snapshot-pilot",
      content: "snapshot boundary reference",
      artifactRef: "data/reports/cea-011_safe_repo_snapshot_pilot.json",
      snapshotId: "cea-011-safe-snapshot-20260707080426",
      tags: ["snapshot_ref"],
    }),
  ];
}
