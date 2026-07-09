import { mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  assertRecordOnlyContextLedgerEntry,
  createContextLedgerEntry,
  isDuplicateContextLedgerEntry,
  validateContextLedgerEntry,
} from "../../src/bridge/context_ledger.js";
import { createFileContextLedgerStore } from "../../src/stores/context_ledger_store.js";

const tmpRoot = path.join(process.cwd(), "data", "tmp", "context-ledger");

describe("context ledger", () => {
  it("stores only record-only metadata and a content hash", () => {
    const rawContent = "unique ledger payload that must not be persisted";
    const entry = createContextLedgerEntry({
      taskId: "cea-012-test",
      eventId: "cea-012-test:001",
      eventType: "MESSAGE_RECORDED",
      at: "2026-07-07T00:00:00.000Z",
      agentId: "worker-1",
      role: "worker",
      source: "app-server-jsonrpc",
      frontendOrSession: "thread-1",
      content: rawContent,
      artifactRef: "data/reports/example.json",
      snapshotId: "cea-011-safe-snapshot-20260707080426",
      tags: ["record_only"],
    });

    expect(entry.contentHash).toMatch(/^sha256:[A-F0-9]{64}$/);
    expect(entry.contentBytes).toBe(Buffer.byteLength(rawContent, "utf8"));
    expect(entry.visibility).toBe("record_only");
    expect(entry.autoInject).toBe(false);
    expect(entry.contextPatch).toBe("disabled");
    expect(JSON.stringify(entry)).not.toContain(rawContent);
    expect(validateContextLedgerEntry(entry)).toBe(true);
  });

  it("rejects raw message fields and auto-injection attempts", () => {
    const entry = createContextLedgerEntry({
      taskId: "cea-012-test",
      eventId: "cea-012-test:002",
      eventType: "MESSAGE_RECORDED",
      agentId: "reviewer-1",
      role: "reviewer",
      source: "app-server-jsonrpc",
      frontendOrSession: "thread-2",
      content: "review metadata only",
    });

    expect(validateContextLedgerEntry({ ...entry, content: "raw text" })).toBe(false);
    expect(validateContextLedgerEntry({ ...entry, autoInject: true })).toBe(false);
    expect(validateContextLedgerEntry({ ...entry, visibility: "context_patch" })).toBe(false);
    expect(() => assertRecordOnlyContextLedgerEntry({ ...entry, contextPatch: "enabled" })).toThrow("record-only");
  });

  it("detects duplicate message records by agent, source, session, role, and hash", () => {
    const base = createContextLedgerEntry({
      taskId: "cea-012-test",
      eventId: "cea-012-test:003",
      eventType: "MESSAGE_RECORDED",
      agentId: "worker-1",
      role: "worker",
      source: "app-server-jsonrpc",
      frontendOrSession: "thread-1",
      content: "same message body",
    });
    const duplicate = createContextLedgerEntry({
      taskId: "cea-012-test",
      eventId: "cea-012-test:004",
      eventType: "MESSAGE_RECORDED",
      agentId: "worker-1",
      role: "worker",
      source: "app-server-jsonrpc",
      frontendOrSession: "thread-1",
      content: "same message body",
    });
    const differentSession = createContextLedgerEntry({
      taskId: "cea-012-test",
      eventId: "cea-012-test:005",
      eventType: "MESSAGE_RECORDED",
      agentId: "worker-1",
      role: "worker",
      source: "app-server-jsonrpc",
      frontendOrSession: "thread-2",
      content: "same message body",
    });

    expect(isDuplicateContextLedgerEntry(base, duplicate)).toBe(true);
    expect(isDuplicateContextLedgerEntry(base, differentSession)).toBe(false);
  });

  it("writes and reads context ledger JSONL safely", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });
    const store = createFileContextLedgerStore(root);
    const entry = createContextLedgerEntry({
      taskId: "cea-012-test",
      eventId: "cea-012-test:006",
      eventType: "TASK_OPENED",
      agentId: "commander",
      role: "commander",
      source: "codex-desktop",
      frontendOrSession: "current-thread",
      content: "open context ledger pilot",
    });

    await store.append("cea-012-test", entry);
    await expect(store.read("cea-012-test")).resolves.toEqual([entry]);
    await expect(store.append("other-task", entry)).rejects.toThrow("task id mismatch");
    await expect(
      store.append("cea-012-test", { ...entry, eventId: "cea-012-test:007", autoInject: true } as never),
    ).rejects.toThrow("record-only");
  });
});
