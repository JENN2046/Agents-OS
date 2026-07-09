import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { createMessageBus } from "../../src/bridge/message_bus.js";
import { transitionState } from "../../src/bridge/state_machine.js";
import { createFileEventStore } from "../../src/stores/event_store.js";
import { createFileJobStore } from "../../src/stores/job_store.js";
import { buildConversationSnapshot } from "../../src/stores/message_ledger.js";
import { createJsonlMessageLedgerStore } from "../../src/stores/message_ledger_jsonl.js";
import { createFileMessageEventStore } from "../../src/stores/message_event_store.js";
import { createFileReceiptStore } from "../../src/stores/receipt_store.js";
import { createFileReportStore } from "../../src/stores/report_store.js";
import { safeJoin } from "../../src/stores/safe_path.js";
import { createStateTransitionEvent } from "../../src/types/events.js";
import type { CodexMessageReply, MessageToCodex } from "../../src/types/messages.js";

const tmpRoot = path.join(process.cwd(), "data", "tmp", "unit-stores");

describe("file stores", () => {
  it("writes and reads job JSON and event JSONL", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });

    const jobStore = createFileJobStore(path.join(root, "jobs"));
    const eventStore = createFileEventStore(path.join(root, "events"));
    const job = {
      jobId: "job-1",
      createdAt: "2026-07-07T00:00:00.000Z",
      updatedAt: "2026-07-07T00:00:00.000Z",
      state: "CREATED" as const,
      syntheticWorkspaceRoot: "data/synthetic-workspace",
    };

    await jobStore.put(job);
    await expect(jobStore.get("job-1")).resolves.toEqual(job);

    const transition = transitionState("CREATED", "APP_SERVER_STARTED", "start", new Date(job.createdAt));
    await eventStore.append("job-1", createStateTransitionEvent("job-1", transition.transition));
    await expect(eventStore.read("job-1")).resolves.toHaveLength(1);
  });

  it("writes receipts and final reports", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}-receipt`);
    const receiptStore = createFileReceiptStore(path.join(root, "receipts"));
    const reportStore = createFileReportStore(path.join(root, "reports"));

    const receiptPath = await receiptStore.write({
      jobId: "job-2",
      result: "PASS",
      finalState: "DONE",
      validation: ["unit: PASS"],
      artifacts: ["data/events/job-2.events.jsonl"],
      boundaryFlags: { secrets_read: "NOT_USED" },
    });
    const reportPath = await reportStore.writeFinalReport({ result: "PASS" });

    expect(receiptPath.endsWith("job-2.receipt.md")).toBe(true);
    expect(reportPath.endsWith("final_report.json")).toBe(true);
  });

  it("rejects store path escapes", () => {
    expect(() => safeJoin(tmpRoot, "../outside.json")).toThrow("escapes store root");
  });

  it("appends and reads message route events as JSONL", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}-messages`);
    await rm(root, { force: true, recursive: true });
    const store = createFileMessageEventStore(path.join(root, "message-logs"));

    await store.append("job-3", {
      event: "MESSAGE_CAPTURED",
      timestamp: "2026-07-08T00:00:00.000Z",
      message_id: "msg_worker_001",
      conversation_id: "conv_001",
      correlation_id: "corr_001",
      from: "worker",
      to: "reviewer",
    });
    await store.append("job-3", {
      event: "MESSAGE_ROUTED",
      timestamp: "2026-07-08T00:00:01.000Z",
      message_id: "msg_worker_001",
      conversation_id: "conv_001",
      correlation_id: "corr_001",
      from: "worker",
      to: "reviewer",
    });

    await expect(store.read("job-3")).resolves.toMatchObject([
      { event: "MESSAGE_CAPTURED", job_id: "job-3" },
      { event: "MESSAGE_ROUTED", job_id: "job-3" },
    ]);
  });

  it("persists message ledger records as append-only JSONL without raw payload copies", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}-ledger`);
    await rm(root, { force: true, recursive: true });
    const ledger = createJsonlMessageLedgerStore(path.join(root, "ledgers"), "job-4");
    const bus = createMessageBus({ ledger, maxRounds: 3 });

    bus.captureMessage(workerMessage(), "2026-07-08T00:00:00.000Z");
    bus.markRouted("msg_worker_001", "thread_reviewer_001", "2026-07-08T00:00:00.100Z", "thread_worker_001");
    bus.captureReply(reviewerReply(), "thread_worker_001", "2026-07-08T00:00:00.200Z", "thread_reviewer_001");
    expect(() => bus.captureReply({ ...reviewerReply(), message_id: "msg_reviewer_002" })).toThrow(
      "message already has a reply: msg_worker_001",
    );

    const persisted = ledger.readPersistedSnapshot();
    const conversation = buildConversationSnapshot(persisted).by_conversation_id.conv_channel_001;
    const text = await readFile(ledger.pathFor(), "utf8");

    expect(persisted.entries.map((entry) => entry.kind)).toEqual([
      "CONVERSATION",
      "MESSAGE",
      "ROUTE",
      "CONVERSATION",
      "REPLY",
      "ROUTE",
      "REJECTION",
    ]);
    expect(persisted.messages[0]).toMatchObject({
      message_id: "msg_worker_001",
      payload_hash: expect.stringMatching(/^sha256:/),
      delivery_fingerprint: expect.stringMatching(/^sha256:/),
    });
    expect(persisted.rejections[0]?.failure_reason).toBe("message already has a reply: msg_worker_001");
    expect(conversation?.idempotency.guard_ok).toBe(true);
    expect(text).not.toContain("Please review this decision point.");
    expect(text).not.toContain("Synthetic channel test is safe.");
  });

  it("rejects unsafe JSONL ledger ids before writing", () => {
    expect(() => createJsonlMessageLedgerStore(tmpRoot, "../escape")).toThrow("unsafe job id");
  });

  it("reports clear errors when JSONL ledger appends fail", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}-ledger-fail`);
    await rm(root, { force: true, recursive: true });
    await mkdir(tmpRoot, { recursive: true });
    await writeFile(root, "not a directory", "utf8");
    const ledger = createJsonlMessageLedgerStore(root, "job-5");

    expect(() =>
      ledger.record({
        kind: "MESSAGE",
        at: "2026-07-08T00:00:00.000Z",
        state: "CAPTURED",
        delivery_fingerprint: "sha256:test",
      }),
    ).toThrow("failed to append message ledger entry");
  });
});

function workerMessage(): MessageToCodex {
  return {
    type: "MESSAGE_TO_CODEX",
    message_id: "msg_worker_001",
    correlation_id: "corr_channel_001",
    conversation_id: "conv_channel_001",
    from: "worker",
    to: "reviewer",
    kind: "question",
    payload: {
      question: "Please review this decision point.",
      context: [],
      expected_response: "decision",
    },
  };
}

function reviewerReply(): CodexMessageReply {
  return {
    type: "CODEX_MESSAGE_REPLY",
    message_id: "msg_reviewer_001",
    reply_to: "msg_worker_001",
    correlation_id: "corr_channel_001",
    conversation_id: "conv_channel_001",
    from: "reviewer",
    to: "worker",
    kind: "answer",
    payload: {
      decision: "continue",
      reason: "Synthetic channel test is safe.",
      next_instruction: "Continue and emit DONE.",
    },
  };
}
