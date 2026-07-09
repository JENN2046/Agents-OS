import { describe, expect, it } from "vitest";
import { createMessageBus } from "../../src/bridge/message_bus.js";
import type { CodexMessageReply, MessageToCodex } from "../../src/types/messages.js";

describe("Codex message bus", () => {
  it("captures, routes, and correlates a Worker message and Reviewer reply", () => {
    const bus = createMessageBus({ messageTtlMs: 1_000, maxRounds: 3 });

    const captured = bus.captureMessage(workerMessage(), "2026-07-08T00:00:00.000Z");
    const routed = bus.markRouted(captured.envelope.message_id, "thread_reviewer_001", "2026-07-08T00:00:00.100Z");
    const reply = bus.captureReply(reviewerReply(), "thread_worker_001", "2026-07-08T00:00:00.200Z");

    expect(captured.state).toBe("CAPTURED");
    expect(captured.expires_at).toBe("2026-07-08T00:00:01.000Z");
    expect(routed.state).toBe("ROUTED");
    expect(reply.envelope.reply_to).toBe("msg_worker_001");
    expect(captured.payload_hash).toMatch(/^sha256:/);
    expect(captured.delivery_fingerprint).toMatch(/^sha256:/);
    expect(reply.payload_hash).toMatch(/^sha256:/);
    expect(reply.delivery_fingerprint).toMatch(/^sha256:/);
    expect(bus.getMessage("msg_worker_001")?.state).toBe("REPLIED");
    expect(bus.getReplyFor("msg_worker_001")?.envelope.message_id).toBe("msg_reviewer_001");
    expect(bus.getConversationState("conv_channel_001")?.round_count).toBe(1);
    expect(bus.auditEvents().map((event) => event.event)).toEqual([
      "MESSAGE_CAPTURED",
      "MESSAGE_ROUTED",
      "REPLY_CAPTURED",
      "REPLY_ROUTED",
    ]);
  });

  it("records a ledger snapshot without raw payload exposure", () => {
    const bus = createMessageBus({ messageTtlMs: 1_000, maxRounds: 3 });

    bus.captureMessage(workerMessage(), "2026-07-08T00:00:00.000Z");
    bus.markRouted("msg_worker_001", "thread_reviewer_001", "2026-07-08T00:00:00.100Z", "thread_worker_001");
    bus.captureReply(reviewerReply(), "thread_worker_001", "2026-07-08T00:00:00.200Z", "thread_reviewer_001");
    expect(() => bus.captureReply({ ...reviewerReply(), message_id: "msg_reviewer_002" })).toThrow(
      "message already has a reply: msg_worker_001",
    );

    const ledger = bus.snapshot().ledger;

    expect(ledger.messages.some((entry) => entry.message_id === "msg_worker_001" && entry.payload_hash?.startsWith("sha256:"))).toBe(true);
    expect(ledger.routes.some((entry) => entry.fromThreadId === "thread_worker_001" && entry.toThreadId === "thread_reviewer_001")).toBe(true);
    expect(ledger.replies.some((entry) => entry.message_id === "msg_reviewer_001" && entry.reply_to === "msg_worker_001")).toBe(true);
    expect(ledger.rejections.some((entry) => entry.failure_reason === "message already has a reply: msg_worker_001")).toBe(true);
    expect(ledger.conversations.some((entry) => entry.conversation_id === "conv_channel_001" && entry.round_count === 1)).toBe(true);
    expect(JSON.stringify(ledger)).not.toContain("Please review this decision point.");
  });

  it("builds a compact conversation snapshot for route and idempotency review", () => {
    const bus = createMessageBus({ maxRounds: 3 });

    bus.captureMessage(workerMessageForRound(1), "2026-07-08T00:00:00.000Z");
    bus.markRouted("msg_worker_001", "thread_reviewer_001", "2026-07-08T00:00:00.100Z", "thread_worker_001");
    bus.captureReply(reviewerReplyForRound(1), "thread_worker_001", "2026-07-08T00:00:00.200Z", "thread_reviewer_001");
    bus.captureMessage(workerMessageForRound(2), "2026-07-08T00:00:01.000Z");
    bus.markRouted("msg_worker_002", "thread_reviewer_001", "2026-07-08T00:00:01.100Z", "thread_worker_001");
    bus.captureReply(reviewerReplyForRound(2), "thread_worker_001", "2026-07-08T00:00:01.200Z", "thread_reviewer_001");

    const snapshot = bus.conversationSnapshot("conv_channel_001");
    const routedTrail = snapshot?.trail.filter((entry) => entry.state === "ROUTED");

    expect(snapshot).toMatchObject({
      conversation_id: "conv_channel_001",
      status: "ACTIVE",
      round_count: 2,
      max_rounds: 3,
      idempotency: {
        accepted_message_ids: ["msg_worker_001", "msg_reviewer_001", "msg_worker_002", "msg_reviewer_002"],
        reply_to_ids: ["msg_worker_001", "msg_worker_002"],
        correlation_ids: ["corr_channel_001", "corr_channel_002"],
        duplicate_message_ids: [],
        duplicate_reply_to_ids: [],
        duplicate_correlation_ids: [],
        idempotency_ok: true,
        ordering_ok: true,
        guard_ok: true,
      },
    });
    expect(snapshot?.idempotency.in_flight_message_id).toBeUndefined();
    expect(routedTrail).toEqual([
      expect.objectContaining({
        round: 1,
        message_id: "msg_worker_001",
        from: "worker",
        to: "reviewer",
        fromThreadId: "thread_worker_001",
        toThreadId: "thread_reviewer_001",
        payload_hash: expect.stringMatching(/^sha256:/),
      }),
      expect.objectContaining({
        round: 2,
        message_id: "msg_worker_002",
        from: "worker",
        to: "reviewer",
        fromThreadId: "thread_worker_001",
        toThreadId: "thread_reviewer_001",
        payload_hash: expect.stringMatching(/^sha256:/),
      }),
    ]);
    expect(bus.snapshot().conversation_snapshots.by_conversation_id.conv_channel_001).toBeDefined();
    expect(JSON.stringify(snapshot)).not.toContain("Please review this decision point.");
  });

  it("records observe-only messages without claiming live routing", () => {
    const bus = createMessageBus({ mode: "observe_only", messageTtlMs: 1_000, maxRounds: 3 });

    const captured = bus.captureMessage(workerMessage(), "2026-07-08T00:00:00.000Z");
    const observed = bus.observeMessage("msg_worker_001", "thread_reviewer_001", "2026-07-08T00:00:00.100Z", "thread_worker_001");

    expect(captured.state).toBe("CAPTURED");
    expect(observed).toMatchObject({
      state: "OBSERVED",
      observed_at: "2026-07-08T00:00:00.100Z",
      fromThreadId: "thread_worker_001",
      toThreadId: "thread_reviewer_001",
    });
    expect(() => bus.markRouted("msg_worker_001", "thread_reviewer_001")).toThrow(
      "observe-only message bus cannot mark live routes; use observeMessage",
    );
    expect(bus.auditEvents().map((event) => event.event)).toEqual(["MESSAGE_CAPTURED", "MESSAGE_OBSERVED"]);
    expect(bus.auditEvents().map((event) => event.event)).not.toContain("MESSAGE_ROUTED");
    expect(bus.snapshot().ledger.routes).toHaveLength(0);
    expect(bus.snapshot().ledger.messages).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          message_id: "msg_worker_001",
          state: "OBSERVED",
          payload_hash: expect.stringMatching(/^sha256:/),
        }),
      ]),
    );
    expect(bus.conversationSnapshot("conv_channel_001")?.trail).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          message_id: "msg_worker_001",
          state: "OBSERVED",
          fromThreadId: "thread_worker_001",
          toThreadId: "thread_reviewer_001",
        }),
      ]),
    );
  });

  it("records observe-only replies without claiming live resume", () => {
    const bus = createMessageBus({ mode: "observe_only", messageTtlMs: 1_000, maxRounds: 3 });

    bus.captureMessage(workerMessage(), "2026-07-08T00:00:00.000Z");
    bus.observeMessage("msg_worker_001", "thread_reviewer_001", "2026-07-08T00:00:00.100Z", "thread_worker_001");
    const reply = bus.observeReply(reviewerReply(), "thread_worker_001", "2026-07-08T00:00:00.200Z", "thread_reviewer_001");

    expect(reply).toMatchObject({
      state: "OBSERVED",
      observed_at: "2026-07-08T00:00:00.200Z",
      fromThreadId: "thread_reviewer_001",
      toThreadId: "thread_worker_001",
    });
    expect(() => bus.captureReply({ ...reviewerReply(), message_id: "msg_reviewer_002" })).toThrow(
      "observe-only message bus cannot capture live replies; use observeReply",
    );
    expect(bus.getMessage("msg_worker_001")?.state).toBe("REPLIED");
    expect(bus.getConversationState("conv_channel_001")?.round_count).toBe(1);
    expect(bus.auditEvents().map((event) => event.event)).toEqual(["MESSAGE_CAPTURED", "MESSAGE_OBSERVED", "REPLY_OBSERVED"]);
    expect(bus.auditEvents().map((event) => event.event)).not.toContain("REPLY_ROUTED");
    expect(bus.auditEvents().map((event) => event.event)).not.toContain("WORKER_RESUMED");
    expect(bus.conversationSnapshot("conv_channel_001")?.trail).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          message_id: "msg_reviewer_001",
          reply_to: "msg_worker_001",
          state: "OBSERVED",
          fromThreadId: "thread_reviewer_001",
          toThreadId: "thread_worker_001",
        }),
      ]),
    );
  });

  it("rejects malformed, duplicate, cross-wired, and single-flight observed traffic", () => {
    const bus = createMessageBus({ mode: "observe_only", maxRounds: 3 });

    expect(() => bus.captureMessage({ ...workerMessage(), message_id: "" })).toThrow("message_id must be a non-empty string");
    bus.captureMessage(workerMessageForRound(1));
    bus.observeMessage("msg_worker_001", "thread_reviewer_001");
    expect(() => bus.captureMessage(workerMessageForRound(2))).toThrow("conversation has in-flight message: msg_worker_001");
    expect(() => bus.observeReply({ ...reviewerReplyForRound(1), correlation_id: "corr_other" })).toThrow(
      "reply correlation_id does not match original message",
    );
    bus.observeReply(reviewerReplyForRound(1), "thread_worker_001");
    expect(() => bus.observeReply({ ...reviewerReplyForRound(1), message_id: "msg_reviewer_002" })).toThrow(
      "message already has a reply: msg_worker_001",
    );
  });

  it("rejects malformed outbound messages before capture", () => {
    const bus = createMessageBus();
    expect(() => bus.captureMessage({ ...workerMessage(), message_id: undefined })).toThrow("message_id must be a string");
    expect(() => bus.captureMessage({ ...workerMessage(), message_id: "" })).toThrow("message_id must be a non-empty string");
    expect(() => bus.captureMessage(omit(workerMessage(), "message_id"))).toThrow("message_id is required");
    expect(() => bus.captureMessage(omit(workerMessage(), "conversation_id"))).toThrow("conversation_id is required");
    expect(() => bus.captureMessage({ ...workerMessage(), conversation_id: "" })).toThrow("conversation_id must be a non-empty string");
    expect(() => bus.captureMessage(omit(workerMessage(), "correlation_id"))).toThrow("correlation_id is required");
    expect(() => bus.captureMessage({ ...workerMessage(), payload: { ...workerMessage().payload, question: "" } })).toThrow(
      "MESSAGE_TO_CODEX payload.question must be a non-empty string",
    );
  });

  it("rejects duplicate message ids", () => {
    const bus = createMessageBus();
    bus.captureMessage(workerMessage());

    expect(() => bus.captureMessage(workerMessage())).toThrow("duplicate message id: msg_worker_001");
  });

  it("rejects a new message while a previous message in the conversation is in flight", () => {
    const capturedBus = createMessageBus();
    capturedBus.captureMessage(workerMessageForRound(1));

    expect(() => capturedBus.captureMessage(workerMessageForRound(2))).toThrow(
      "conversation has in-flight message: msg_worker_001",
    );

    const routedBus = createMessageBus();
    routedBus.captureMessage(workerMessageForRound(1));
    routedBus.markRouted("msg_worker_001", "thread_reviewer_001");

    expect(() => routedBus.captureMessage(workerMessageForRound(2))).toThrow(
      "conversation has in-flight message: msg_worker_001",
    );
  });

  it("rejects route attempts for already routed messages", () => {
    const bus = createMessageBus();
    bus.captureMessage(workerMessage());
    bus.markRouted("msg_worker_001", "thread_reviewer_001");

    expect(() => bus.markRouted("msg_worker_001", "thread_reviewer_001")).toThrow("message is not routable from state: ROUTED");
  });

  it("rejects replies that do not reference a captured and routed original message", () => {
    const bus = createMessageBus();

    expect(() => bus.captureReply(reviewerReply())).toThrow("reply_to does not reference a captured message: msg_worker_001");

    bus.captureMessage(workerMessage());
    expect(() => bus.captureReply(reviewerReply())).toThrow("reply before original message is routed: msg_worker_001");
  });

  it("rejects duplicate replies and mismatched reply metadata", () => {
    const bus = createMessageBus();
    bus.captureMessage(workerMessage());
    bus.markRouted("msg_worker_001", "thread_reviewer_001");

    expect(() => bus.captureReply({ ...reviewerReply(), conversation_id: "conv_other" })).toThrow(
      "reply conversation_id does not match original message",
    );
    expect(() => bus.captureReply({ ...reviewerReply(), correlation_id: "corr_other" })).toThrow(
      "reply correlation_id does not match original message",
    );
    expect(() => bus.captureReply({ ...reviewerReply(), to: "reviewer" } as unknown)).toThrow("reply endpoints must not be identical");
    expect(() => bus.captureReply({ ...reviewerReply(), from: "worker", to: "reviewer" })).toThrow(
      "reply endpoints do not invert original message endpoints",
    );

    bus.captureReply(reviewerReply());
    expect(() => bus.captureReply({ ...reviewerReply(), message_id: "msg_reviewer_002" })).toThrow(
      "message already has a reply: msg_worker_001",
    );
  });

  it("allows replies before timeout and rejects late replies after expiration", () => {
    const bus = createMessageBus({ messageTtlMs: 1_000 });
    bus.captureMessage(workerMessage(), "2026-07-08T00:00:00.000Z");
    bus.markRouted("msg_worker_001", "thread_reviewer_001", "2026-07-08T00:00:00.100Z");

    expect(() => bus.captureReply(reviewerReply(), "thread_worker_001", "2026-07-08T00:00:00.999Z")).not.toThrow();

    const lateBus = createMessageBus({ messageTtlMs: 1_000 });
    lateBus.captureMessage(workerMessage(), "2026-07-08T00:00:00.000Z");
    lateBus.markRouted("msg_worker_001", "thread_reviewer_001", "2026-07-08T00:00:00.100Z");
    expect(() => lateBus.captureReply(reviewerReply(), "thread_worker_001", "2026-07-08T00:00:01.000Z")).toThrow(
      "message expired: msg_worker_001",
    );
    expect(lateBus.getMessage("msg_worker_001")?.state).toBe("EXPIRED");
    expect(lateBus.auditEvents().map((event) => event.event)).toContain("MESSAGE_EXPIRED");
  });

  it("marks due messages expired deterministically", () => {
    const bus = createMessageBus({ messageTtlMs: 1_000 });
    bus.captureMessage(workerMessage(), "2026-07-08T00:00:00.000Z");

    const expired = bus.expireDueMessages("2026-07-08T00:00:01.000Z");

    expect(expired).toHaveLength(1);
    expect(expired[0]?.state).toBe("EXPIRED");
    expect(bus.getMessage("msg_worker_001")?.state).toBe("EXPIRED");
  });

  it("blocks routing after max rounds are completed", () => {
    const bus = createMessageBus({ maxRounds: 1 });
    bus.captureMessage(workerMessage());
    bus.markRouted("msg_worker_001", "thread_reviewer_001");
    bus.captureReply(reviewerReply(), "thread_worker_001");

    const nextMessage = { ...workerMessage(), message_id: "msg_worker_002", correlation_id: "corr_channel_002" };
    bus.captureMessage(nextMessage);

    expect(() => bus.markRouted("msg_worker_002", "thread_reviewer_001")).toThrow(
      "conversation max rounds exceeded: conv_channel_001",
    );
    expect(bus.getConversationState("conv_channel_001")?.status).toBe("BLOCKED");
    expect(bus.getMessage("msg_worker_002")?.state).toBe("FAILED");
  });

  it("allows routing through the configured max round", () => {
    const bus = createMessageBus({ maxRounds: 1 });
    bus.captureMessage(workerMessage());

    expect(() => bus.markRouted("msg_worker_001", "thread_reviewer_001")).not.toThrow();
  });

  it("tracks two Worker Reviewer dialogue rounds in one conversation", () => {
    const bus = createMessageBus({ maxRounds: 3 });

    bus.captureMessage(workerMessageForRound(1));
    bus.markRouted("msg_worker_001", "thread_reviewer_001");
    bus.captureReply(reviewerReplyForRound(1), "thread_worker_001");
    bus.captureMessage(workerMessageForRound(2));
    bus.markRouted("msg_worker_002", "thread_reviewer_001");
    bus.captureReply(reviewerReplyForRound(2), "thread_worker_001");

    const conversation = bus.getConversationState("conv_channel_001");
    expect(conversation).toMatchObject({
      conversation_id: "conv_channel_001",
      round_count: 2,
      max_rounds: 3,
      message_ids: ["msg_worker_001", "msg_worker_002"],
      reply_ids: ["msg_reviewer_001", "msg_reviewer_002"],
      status: "ACTIVE",
    });
    expect(bus.getReplyFor("msg_worker_001")?.envelope.reply_to).toBe("msg_worker_001");
    expect(bus.getReplyFor("msg_worker_002")?.envelope.reply_to).toBe("msg_worker_002");
    expect(bus.getReplyFor("msg_worker_001")?.envelope.correlation_id).toBe("corr_channel_001");
    expect(bus.getReplyFor("msg_worker_002")?.envelope.correlation_id).toBe("corr_channel_002");
    expect(bus.auditEvents().map((event) => [event.event, event.round])).toEqual([
      ["MESSAGE_CAPTURED", 1],
      ["MESSAGE_ROUTED", 1],
      ["REPLY_CAPTURED", 1],
      ["REPLY_ROUTED", 1],
      ["MESSAGE_CAPTURED", 2],
      ["MESSAGE_ROUTED", 2],
      ["REPLY_CAPTURED", 2],
      ["REPLY_ROUTED", 2],
    ]);
  });

  it("rejects duplicate correlation ids across rounds in one conversation", () => {
    const bus = createMessageBus({ maxRounds: 3 });
    bus.captureMessage(workerMessageForRound(1));
    bus.markRouted("msg_worker_001", "thread_reviewer_001");
    bus.captureReply(reviewerReplyForRound(1), "thread_worker_001");

    expect(() => bus.captureMessage({ ...workerMessageForRound(2), correlation_id: "corr_channel_001" })).toThrow(
      "duplicate correlation id in conversation: corr_channel_001",
    );
  });

  it("rejects round 2 replies that target the wrong prior message", () => {
    const bus = createMessageBus({ maxRounds: 3 });
    bus.captureMessage(workerMessageForRound(1));
    bus.markRouted("msg_worker_001", "thread_reviewer_001");
    bus.captureReply(reviewerReplyForRound(1), "thread_worker_001");
    bus.captureMessage(workerMessageForRound(2));
    bus.markRouted("msg_worker_002", "thread_reviewer_001");

    expect(() => bus.captureReply({ ...reviewerReplyForRound(2), reply_to: "msg_worker_001" }, "thread_worker_001")).toThrow(
      "message already has a reply: msg_worker_001",
    );
  });

  it("rejects round 2 replies with mismatched conversation or correlation metadata", () => {
    const bus = createMessageBus({ maxRounds: 3 });
    bus.captureMessage(workerMessageForRound(1));
    bus.markRouted("msg_worker_001", "thread_reviewer_001");
    bus.captureReply(reviewerReplyForRound(1), "thread_worker_001");
    bus.captureMessage(workerMessageForRound(2));
    bus.markRouted("msg_worker_002", "thread_reviewer_001");

    expect(() => bus.captureReply({ ...reviewerReplyForRound(2), conversation_id: "conv_other" }, "thread_worker_001")).toThrow(
      "reply conversation_id does not match original message",
    );
    expect(() => bus.captureReply({ ...reviewerReplyForRound(2), correlation_id: "corr_other" }, "thread_worker_001")).toThrow(
      "reply correlation_id does not match original message",
    );
  });

  it("blocks the fourth attempted round when maxRounds is three", () => {
    const bus = createMessageBus({ maxRounds: 3 });
    for (const round of [1, 2, 3] as const) {
      bus.captureMessage(workerMessageForRound(round));
      bus.markRouted(`msg_worker_00${round}`, "thread_reviewer_001");
      bus.captureReply(reviewerReplyForRound(round), "thread_worker_001");
    }
    bus.captureMessage(workerMessageForRound(4));

    expect(() => bus.markRouted("msg_worker_004", "thread_reviewer_001")).toThrow(
      "conversation max rounds exceeded: conv_channel_001",
    );
    expect(bus.getConversationState("conv_channel_001")?.status).toBe("BLOCKED");
    expect(bus.getMessage("msg_worker_004")?.state).toBe("FAILED");
    expect(bus.auditEvents().map((event) => event.event)).toContain("CONVERSATION_BLOCKED");
  });

  it("rejects messages after a conversation is marked DONE", () => {
    const bus = createMessageBus({ maxRounds: 3 });
    bus.captureMessage(workerMessageForRound(1));
    bus.markRouted("msg_worker_001", "thread_reviewer_001");
    bus.captureReply(reviewerReplyForRound(1), "thread_worker_001");
    bus.markConversationDone("conv_channel_001", "2026-07-08T00:00:02.000Z");

    expect(bus.getConversationState("conv_channel_001")?.status).toBe("DONE");
    expect(() => bus.captureMessage(workerMessageForRound(2))).toThrow("conversation is done: conv_channel_001");
    expect(() => bus.captureReply({ ...reviewerReplyForRound(2), reply_to: "msg_worker_001" })).toThrow(
      "conversation is done: conv_channel_001",
    );
  });

  it("rejects replies after a conversation is BLOCKED", () => {
    const bus = createMessageBus({ maxRounds: 0 });
    bus.captureMessage(workerMessageForRound(1));
    expect(() => bus.markRouted("msg_worker_001", "thread_reviewer_001")).toThrow(
      "conversation max rounds exceeded: conv_channel_001",
    );

    expect(() => bus.captureReply(reviewerReplyForRound(1), "thread_worker_001")).toThrow(
      "conversation is blocked: conv_channel_001",
    );
  });

  it("routes Worker Reviewer Verifier role hops in one conversation", () => {
    const bus = createMessageBus({ maxRounds: 3 });

    bus.captureMessage(workerToReviewerMessage());
    bus.markRouted("msg_worker_to_reviewer", "thread_reviewer_001");
    bus.captureReply(reviewerToWorkerReply(), "thread_worker_001");
    bus.captureMessage(workerToVerifierMessage());
    bus.markRouted("msg_worker_to_verifier", "thread_verifier_001");
    bus.captureReply(verifierToWorkerReply(), "thread_worker_001");

    expect(bus.getConversationState("conv_multirole_001")).toMatchObject({
      conversation_id: "conv_multirole_001",
      round_count: 2,
      max_rounds: 3,
      message_ids: ["msg_worker_to_reviewer", "msg_worker_to_verifier"],
      reply_ids: ["msg_reviewer_to_worker", "msg_verifier_to_worker"],
      status: "ACTIVE",
    });
    expect(bus.auditEvents().map((event) => [event.event, event.from, event.to, event.round])).toEqual([
      ["MESSAGE_CAPTURED", "worker", "reviewer", 1],
      ["MESSAGE_ROUTED", "worker", "reviewer", 1],
      ["REPLY_CAPTURED", "reviewer", "worker", 1],
      ["REPLY_ROUTED", "reviewer", "worker", 1],
      ["MESSAGE_CAPTURED", "worker", "verifier", 2],
      ["MESSAGE_ROUTED", "worker", "verifier", 2],
      ["REPLY_CAPTURED", "verifier", "worker", 2],
      ["REPLY_ROUTED", "verifier", "worker", 2],
    ]);
  });

  it("rejects role-specific replies that do not invert the original route", () => {
    const reviewerBus = createMessageBus({ maxRounds: 3 });
    reviewerBus.captureMessage(workerToReviewerMessage());
    reviewerBus.markRouted("msg_worker_to_reviewer", "thread_reviewer_001");

    expect(() => reviewerBus.captureReply({ ...reviewerToWorkerReply(), message_id: "msg_verifier_wrong", from: "verifier" })).toThrow(
      "reply endpoints do not invert original message endpoints",
    );

    const verifierBus = createMessageBus({ maxRounds: 3 });
    verifierBus.captureMessage(workerToVerifierMessage());
    verifierBus.markRouted("msg_worker_to_verifier", "thread_verifier_001");

    expect(() => verifierBus.captureReply({ ...verifierToWorkerReply(), message_id: "msg_reviewer_wrong", from: "reviewer" })).toThrow(
      "reply endpoints do not invert original message endpoints",
    );
  });

  it("rejects bad Verifier replies and duplicate Verifier replies", () => {
    const bus = createMessageBus({ maxRounds: 3 });
    bus.captureMessage(workerToVerifierMessage());
    bus.markRouted("msg_worker_to_verifier", "thread_verifier_001");

    expect(() => bus.captureReply({ ...verifierToWorkerReply(), conversation_id: "conv_other" })).toThrow(
      "reply conversation_id does not match original message",
    );
    expect(() => bus.captureReply({ ...verifierToWorkerReply(), correlation_id: "corr_other" })).toThrow(
      "reply correlation_id does not match original message",
    );

    bus.captureReply(verifierToWorkerReply(), "thread_worker_001");
    expect(() => bus.captureReply({ ...verifierToWorkerReply(), message_id: "msg_verifier_to_worker_2" })).toThrow(
      "message already has a reply: msg_worker_to_verifier",
    );
  });

  it("rejects unsafe role label syntax in message envelopes", () => {
    const bus = createMessageBus({ maxRounds: 3 });

    expect(() => bus.captureMessage({ ...workerToVerifierMessage(), to: "external:http" } as unknown)).toThrow(
      "to contains unsafe role characters",
    );
    expect(() => bus.captureMessage({ ...workerToVerifierMessage(), from: "../escape" } as unknown)).toThrow(
      "from contains unsafe role characters",
    );
  });

  it("routes structurally valid authority-like payloads without interpreting role policy", () => {
    const bus = createMessageBus({ maxRounds: 3 });
    const message = {
      ...workerToReviewerMessage(),
      kind: "decision" as const,
      payload: {
        question: "Please decide whether this role-authority-looking payload is structurally valid.",
        context: ["The channel must not decide whether approve_write is safe."],
        expected_response: "approve_write",
      },
    };
    const reply = {
      ...reviewerToWorkerReply(),
      payload: {
        decision: "approve_write",
        reason: "This is routed as data only; AGENTS.md owns whether it has authority.",
        next_instruction: "Treat this as a message payload, not a permission grant.",
      },
    };

    bus.captureMessage(message);
    bus.markRouted(message.message_id, "thread_reviewer_001");

    expect(() => bus.captureReply(reply, "thread_worker_001")).not.toThrow();
    expect(bus.getConversationState("conv_multirole_001")?.round_count).toBe(1);
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

function workerMessageForRound(round: 1 | 2 | 3 | 4): MessageToCodex {
  return {
    ...workerMessage(),
    message_id: `msg_worker_00${round}`,
    correlation_id: `corr_channel_00${round}`,
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

function reviewerReplyForRound(round: 1 | 2 | 3 | 4): CodexMessageReply {
  return {
    ...reviewerReply(),
    message_id: `msg_reviewer_00${round}`,
    reply_to: `msg_worker_00${round}`,
    correlation_id: `corr_channel_00${round}`,
  };
}

function workerToReviewerMessage(): MessageToCodex {
  return {
    type: "MESSAGE_TO_CODEX",
    message_id: "msg_worker_to_reviewer",
    correlation_id: "corr_worker_reviewer",
    conversation_id: "conv_multirole_001",
    from: "worker",
    to: "reviewer",
    kind: "request_review",
    payload: {
      question: "Please review the Worker decision before verifier check.",
      context: [],
      expected_response: "decision",
    },
  };
}

function reviewerToWorkerReply(): CodexMessageReply {
  return {
    type: "CODEX_MESSAGE_REPLY",
    message_id: "msg_reviewer_to_worker",
    reply_to: "msg_worker_to_reviewer",
    correlation_id: "corr_worker_reviewer",
    conversation_id: "conv_multirole_001",
    from: "reviewer",
    to: "worker",
    kind: "decision",
    payload: {
      decision: "continue",
      reason: "Reviewer approves proceeding to Verifier in this synthetic multi-role test.",
      next_instruction: "Ask Verifier to verify the route evidence.",
    },
  };
}

function workerToVerifierMessage(): MessageToCodex {
  return {
    type: "MESSAGE_TO_CODEX",
    message_id: "msg_worker_to_verifier",
    correlation_id: "corr_worker_verifier",
    conversation_id: "conv_multirole_001",
    from: "worker",
    to: "verifier",
    kind: "request_decision",
    payload: {
      question: "Please verify that the Worker-Reviewer route evidence is consistent.",
      context: [],
      expected_response: "verification",
    },
  };
}

function verifierToWorkerReply(): CodexMessageReply {
  return {
    type: "CODEX_MESSAGE_REPLY",
    message_id: "msg_verifier_to_worker",
    reply_to: "msg_worker_to_verifier",
    correlation_id: "corr_worker_verifier",
    conversation_id: "conv_multirole_001",
    from: "verifier",
    to: "worker",
    kind: "decision",
    payload: {
      decision: "continue",
      reason: "Verifier confirms the multi-role route evidence is internally consistent.",
      next_instruction: "Emit DONE with evidence for Reviewer and Verifier routes.",
    },
  };
}

function omit(value: object, key: string): Record<string, unknown> {
  const copy = { ...(value as Record<string, unknown>) };
  delete copy[key];
  return copy;
}
