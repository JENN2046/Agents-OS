import { describe, expect, it } from "vitest";
import {
  buildConversationSnapshot,
  createDeliveryFingerprint,
  createInMemoryMessageLedgerStore,
  hashCanonicalJson,
  hashMessagePayload,
} from "../../src/stores/message_ledger.js";
import type { MessageToCodex } from "../../src/types/messages.js";

describe("message ledger store", () => {
  it("hashes canonical JSON independent of object key order", () => {
    expect(hashCanonicalJson({ b: 2, a: 1, nested: { z: true, c: "x" } })).toBe(
      hashCanonicalJson({ nested: { c: "x", z: true }, a: 1, b: 2 }),
    );
  });

  it("records in-memory ledger entries without raw payload content", () => {
    const store = createInMemoryMessageLedgerStore();
    const message = workerMessage();
    const payloadHash = hashMessagePayload(message);
    const deliveryFingerprint = createDeliveryFingerprint({
      message_id: message.message_id,
      payload_hash: payloadHash,
    });

    store.record({
      kind: "MESSAGE",
      at: "2026-07-08T00:00:00.000Z",
      message_id: message.message_id,
      conversation_id: message.conversation_id,
      correlation_id: message.correlation_id,
      from: message.from,
      to: message.to,
      message_kind: message.kind,
      state: "CAPTURED",
      payload_hash: payloadHash,
      delivery_fingerprint: deliveryFingerprint,
    });

    const snapshot = store.snapshot();

    expect(snapshot.entries).toHaveLength(1);
    expect(snapshot.messages[0]).toMatchObject({
      message_id: "msg_worker_001",
      payload_hash: expect.stringMatching(/^sha256:/),
      delivery_fingerprint: expect.stringMatching(/^sha256:/),
    });
    expect(JSON.stringify(snapshot)).not.toContain("Please review this decision point.");
  });

  it("builds compact conversation snapshots without raw payload exposure", () => {
    const store = createInMemoryMessageLedgerStore();
    const message = workerMessage();
    const payloadHash = hashMessagePayload(message);

    store.record({
      kind: "MESSAGE",
      at: "2026-07-08T00:00:00.000Z",
      message_id: message.message_id,
      conversation_id: message.conversation_id,
      correlation_id: message.correlation_id,
      from: message.from,
      to: message.to,
      state: "CAPTURED",
      round: 1,
      payload_hash: payloadHash,
      delivery_fingerprint: createDeliveryFingerprint(["captured", message.message_id, payloadHash]),
    });
    store.record({
      kind: "ROUTE",
      at: "2026-07-08T00:00:00.100Z",
      message_id: message.message_id,
      conversation_id: message.conversation_id,
      correlation_id: message.correlation_id,
      from: message.from,
      to: message.to,
      fromThreadId: "thread_worker_001",
      toThreadId: "thread_reviewer_001",
      state: "ROUTED",
      round: 1,
      payload_hash: payloadHash,
      delivery_fingerprint: createDeliveryFingerprint(["routed", message.message_id, payloadHash]),
    });

    const snapshot = buildConversationSnapshot(store.snapshot());
    const conversation = snapshot.by_conversation_id.conv_channel_001;

    expect(conversation?.trail).toEqual([
      expect.objectContaining({
        round: 1,
        message_id: "msg_worker_001",
        conversation_id: "conv_channel_001",
        correlation_id: "corr_channel_001",
        from: "worker",
        to: "reviewer",
        payload_hash: expect.stringMatching(/^sha256:/),
        state: "CAPTURED",
        timestamp: "2026-07-08T00:00:00.000Z",
      }),
      expect.objectContaining({
        fromThreadId: "thread_worker_001",
        toThreadId: "thread_reviewer_001",
        state: "ROUTED",
      }),
    ]);
    expect(conversation?.idempotency).toMatchObject({
      accepted_message_ids: ["msg_worker_001"],
      correlation_ids: ["corr_channel_001"],
      in_flight_message_id: "msg_worker_001",
      idempotency_ok: true,
      ordering_ok: true,
      guard_ok: true,
    });
    expect(JSON.stringify(snapshot)).not.toContain("Please review this decision point.");
  });

  it("flags idempotency duplicate evidence in conversation snapshots", () => {
    const store = createInMemoryMessageLedgerStore();

    for (const at of ["2026-07-08T00:00:00.000Z", "2026-07-08T00:00:01.000Z"]) {
      store.record({
        kind: "MESSAGE",
        at,
        message_id: "msg_duplicate",
        conversation_id: "conv_duplicate",
        correlation_id: "corr_duplicate",
        from: "worker",
        to: "reviewer",
        state: "CAPTURED",
        payload_hash: hashCanonicalJson({ at }),
        delivery_fingerprint: createDeliveryFingerprint(["duplicate", at]),
      });
    }

    const conversation = buildConversationSnapshot(store.snapshot()).by_conversation_id.conv_duplicate;

    expect(conversation?.idempotency).toMatchObject({
      accepted_message_ids: ["msg_duplicate", "msg_duplicate"],
      correlation_ids: ["corr_duplicate", "corr_duplicate"],
      duplicate_message_ids: ["msg_duplicate"],
      duplicate_correlation_ids: ["corr_duplicate"],
      idempotency_ok: false,
      ordering_ok: true,
      guard_ok: false,
    });
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
