import { describe, expect, it } from "vitest";
import { createMessageBus } from "../../src/bridge/message_bus.js";
import { createMessageRouter } from "../../src/bridge/message_router.js";
import { createThreadRegistry } from "../../src/bridge/thread_registry.js";
import type { CodexMessageReply, MessageToCodex } from "../../src/types/messages.js";

describe("Codex message router", () => {
  it("routes Worker messages to Reviewer and replies back to Worker with generalized statuses", () => {
    const registry = readyRegistry();
    const bus = createMessageBus();
    const router = createMessageRouter({ bus, registry });

    const messageDelivery = router.routeMessage(workerMessage(), "2026-07-08T00:00:00.000Z");
    const replyDelivery = router.routeReply(reviewerReply(), "2026-07-08T00:00:01.000Z");

    expect(messageDelivery).toMatchObject({
      status: "MESSAGE_ROUTED",
      from: "worker",
      to: "reviewer",
      fromThreadId: "thread_worker_001",
      toThreadId: "thread_reviewer_001",
    });
    expect(replyDelivery).toMatchObject({
      status: "REPLY_ROUTED",
      replyTo: "msg_worker_001",
      from: "reviewer",
      to: "worker",
      fromThreadId: "thread_reviewer_001",
      toThreadId: "thread_worker_001",
    });
    expect(bus.getMessage("msg_worker_001")?.state).toBe("REPLIED");
    expect(bus.getMessage("msg_worker_001")).toMatchObject({
      fromThreadId: "thread_worker_001",
      toThreadId: "thread_reviewer_001",
    });
    expect(bus.getReplyFor("msg_worker_001")).toMatchObject({
      fromThreadId: "thread_reviewer_001",
      toThreadId: "thread_worker_001",
    });
    expect(bus.snapshot().ledger.routes).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          message_id: "msg_worker_001",
          fromThreadId: "thread_worker_001",
          toThreadId: "thread_reviewer_001",
        }),
        expect.objectContaining({
          message_id: "msg_reviewer_001",
          fromThreadId: "thread_reviewer_001",
          toThreadId: "thread_worker_001",
        }),
      ]),
    );
    expect(bus.conversationSnapshot("conv_channel_001")?.trail).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          message_id: "msg_worker_001",
          fromThreadId: "thread_worker_001",
          toThreadId: "thread_reviewer_001",
          state: "ROUTED",
        }),
        expect.objectContaining({
          message_id: "msg_reviewer_001",
          reply_to: "msg_worker_001",
          fromThreadId: "thread_reviewer_001",
          toThreadId: "thread_worker_001",
          state: "REPLIED",
        }),
      ]),
    );
  });

  it("records observe-only deliveries without claiming live route or resume", () => {
    const registry = readyRegistry();
    const bus = createMessageBus({ mode: "observe_only" });
    const router = createMessageRouter({ bus, registry });

    const messageDelivery = router.routeMessage(workerMessage(), "2026-07-08T00:00:00.000Z");
    const replyDelivery = router.routeReply(reviewerReply(), "2026-07-08T00:00:01.000Z");

    expect(messageDelivery).toMatchObject({
      mode: "observe_only",
      status: "DRY_ROUTE_RECORDED",
      fromThreadId: "thread_worker_001",
      toThreadId: "thread_reviewer_001",
    });
    expect(replyDelivery).toMatchObject({
      mode: "observe_only",
      status: "DRY_REPLY_RECORDED",
      replyTo: "msg_worker_001",
      fromThreadId: "thread_reviewer_001",
      toThreadId: "thread_worker_001",
    });
    expect(bus.auditEvents().map((event) => event.event)).toEqual(["MESSAGE_CAPTURED", "MESSAGE_OBSERVED", "REPLY_OBSERVED"]);
    expect(bus.auditEvents().map((event) => event.event)).not.toContain("MESSAGE_ROUTED");
    expect(bus.auditEvents().map((event) => event.event)).not.toContain("REPLY_ROUTED");
    expect(bus.snapshot().ledger.routes).toHaveLength(0);
    expect(bus.conversationSnapshot("conv_channel_001")?.trail).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          message_id: "msg_worker_001",
          state: "OBSERVED",
          fromThreadId: "thread_worker_001",
          toThreadId: "thread_reviewer_001",
        }),
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

  it("rejects unregistered target roles before routing", () => {
    const router = createMessageRouter({ bus: createMessageBus(), registry: readyRegistry() });

    expect(() => router.routeMessage({ ...workerMessage(), to: "external" })).toThrow("missing registered external thread");
  });

  it("rejects replies to unregistered target roles before routing", () => {
    const router = createMessageRouter({ bus: createMessageBus(), registry: readyRegistry() });

    expect(() => router.routeReply({ ...reviewerReply(), to: "external" })).toThrow("missing registered external thread");
  });

  it("requires both endpoint roles to be registered", () => {
    const registry = createThreadRegistry();
    registry.register({ role: "worker", threadId: "thread_worker_001", cwd: "A:/synthetic" });
    const router = createMessageRouter({ bus: createMessageBus(), registry });

    expect(() => router.routeMessage(workerMessage())).toThrow("missing registered reviewer thread");
  });

  it("rejects inactive target threads", () => {
    const registry = readyRegistry();
    registry.markStatus("thread_reviewer_001", "COMPLETED");
    const router = createMessageRouter({ bus: createMessageBus(), registry });

    expect(() => router.routeMessage(workerMessage())).toThrow("reviewer thread is not active: COMPLETED");
  });

  it("routes two dialogue rounds without losing conversation or correlation integrity", () => {
    const registry = readyRegistry();
    const bus = createMessageBus({ maxRounds: 3 });
    const router = createMessageRouter({ bus, registry });

    const round1Message = router.routeMessage(workerMessageForRound(1), "2026-07-08T00:00:00.000Z");
    const round1Reply = router.routeReply(reviewerReplyForRound(1), "2026-07-08T00:00:01.000Z");
    const round2Message = router.routeMessage(workerMessageForRound(2), "2026-07-08T00:00:02.000Z");
    const round2Reply = router.routeReply(reviewerReplyForRound(2), "2026-07-08T00:00:03.000Z");

    expect([round1Message.status, round2Message.status]).toEqual(["MESSAGE_ROUTED", "MESSAGE_ROUTED"]);
    expect([round1Reply.status, round2Reply.status]).toEqual(["REPLY_ROUTED", "REPLY_ROUTED"]);
    expect([round1Message.conversationId, round1Reply.conversationId, round2Message.conversationId, round2Reply.conversationId]).toEqual([
      "conv_channel_001",
      "conv_channel_001",
      "conv_channel_001",
      "conv_channel_001",
    ]);
    expect([round1Message.correlationId, round1Reply.correlationId]).toEqual(["corr_channel_001", "corr_channel_001"]);
    expect([round2Message.correlationId, round2Reply.correlationId]).toEqual(["corr_channel_002", "corr_channel_002"]);
    expect([round1Reply.replyTo, round2Reply.replyTo]).toEqual(["msg_worker_001", "msg_worker_002"]);
    expect(bus.getConversationState("conv_channel_001")?.round_count).toBe(2);
  });

  it("propagates max round blocking from the bus", () => {
    const registry = readyRegistry();
    const bus = createMessageBus({ maxRounds: 1 });
    const router = createMessageRouter({ bus, registry });

    router.routeMessage(workerMessageForRound(1));
    router.routeReply(reviewerReplyForRound(1));

    expect(() => router.routeMessage(workerMessageForRound(2))).toThrow("conversation max rounds exceeded: conv_channel_001");
    expect(bus.getConversationState("conv_channel_001")?.status).toBe("BLOCKED");
  });

  it("routes Worker Reviewer Verifier role hops with role-specific thread ids", () => {
    const registry = readyMultiroleRegistry();
    const bus = createMessageBus({ maxRounds: 3 });
    const router = createMessageRouter({ bus, registry });

    const workerReviewer = router.routeMessage(workerToReviewerMessage(), "2026-07-08T00:00:00.000Z");
    const reviewerWorker = router.routeReply(reviewerToWorkerReply(), "2026-07-08T00:00:01.000Z");
    const workerVerifier = router.routeMessage(workerToVerifierMessage(), "2026-07-08T00:00:02.000Z");
    const verifierWorker = router.routeReply(verifierToWorkerReply(), "2026-07-08T00:00:03.000Z");

    expect(workerReviewer).toMatchObject({
      status: "MESSAGE_ROUTED",
      from: "worker",
      to: "reviewer",
      fromThreadId: "thread_worker_001",
      toThreadId: "thread_reviewer_001",
      correlationId: "corr_worker_reviewer",
    });
    expect(reviewerWorker).toMatchObject({
      status: "REPLY_ROUTED",
      from: "reviewer",
      to: "worker",
      fromThreadId: "thread_reviewer_001",
      toThreadId: "thread_worker_001",
      replyTo: "msg_worker_to_reviewer",
      correlationId: "corr_worker_reviewer",
    });
    expect(workerVerifier).toMatchObject({
      status: "MESSAGE_ROUTED",
      from: "worker",
      to: "verifier",
      fromThreadId: "thread_worker_001",
      toThreadId: "thread_verifier_001",
      correlationId: "corr_worker_verifier",
    });
    expect(verifierWorker).toMatchObject({
      status: "REPLY_ROUTED",
      from: "verifier",
      to: "worker",
      fromThreadId: "thread_verifier_001",
      toThreadId: "thread_worker_001",
      replyTo: "msg_worker_to_verifier",
      correlationId: "corr_worker_verifier",
    });
    expect(bus.getConversationState("conv_multirole_001")?.round_count).toBe(2);
  });

  it("rejects Worker to inactive Verifier before routing", () => {
    const registry = readyMultiroleRegistry();
    registry.markStatus("thread_verifier_001", "COMPLETED");
    const router = createMessageRouter({ bus: createMessageBus(), registry });

    expect(() => router.routeMessage(workerToVerifierMessage())).toThrow("verifier thread is not active: COMPLETED");
  });

  it("rejects role-confused multi-role replies", () => {
    const registry = readyMultiroleRegistry();
    const reviewerBus = createMessageBus({ maxRounds: 3 });
    const reviewerRouter = createMessageRouter({ bus: reviewerBus, registry });
    reviewerRouter.routeMessage(workerToReviewerMessage());

    expect(() => reviewerRouter.routeReply({ ...reviewerToWorkerReply(), message_id: "msg_verifier_wrong", from: "verifier" })).toThrow(
      "reply endpoints do not invert original message endpoints",
    );

    const verifierBus = createMessageBus({ maxRounds: 3 });
    const verifierRouter = createMessageRouter({ bus: verifierBus, registry });
    verifierRouter.routeMessage(workerToVerifierMessage());

    expect(() => verifierRouter.routeReply({ ...verifierToWorkerReply(), message_id: "msg_reviewer_wrong", from: "reviewer" })).toThrow(
      "reply endpoints do not invert original message endpoints",
    );
  });

  it("routes messages and replies between arbitrary registered role labels", () => {
    const registry = createThreadRegistry();
    registry.register({ role: "planner", threadId: "thread_planner_001", cwd: "A:/synthetic" });
    registry.register({ role: "auditor", threadId: "thread_auditor_001", cwd: "A:/synthetic" });
    const bus = createMessageBus({ maxRounds: 3 });
    const router = createMessageRouter({ bus, registry });

    const messageDelivery = router.routeMessage(plannerToAuditorMessage(), "2026-07-08T00:00:00.000Z");
    const replyDelivery = router.routeReply(auditorToPlannerReply(), "2026-07-08T00:00:01.000Z");

    expect(messageDelivery).toMatchObject({
      status: "MESSAGE_ROUTED",
      from: "planner",
      to: "auditor",
      fromThreadId: "thread_planner_001",
      toThreadId: "thread_auditor_001",
    });
    expect(replyDelivery).toMatchObject({
      status: "REPLY_ROUTED",
      from: "auditor",
      to: "planner",
      fromThreadId: "thread_auditor_001",
      toThreadId: "thread_planner_001",
    });
    expect(bus.getConversationState("conv_arbitrary_roles_001")?.round_count).toBe(1);
  });

  it("does not special-case worker reviewer or verifier routing statuses", () => {
    const registry = createThreadRegistry();
    registry.register({ role: "critic", threadId: "thread_critic_001", cwd: "A:/synthetic" });
    registry.register({ role: "executor", threadId: "thread_executor_001", cwd: "A:/synthetic" });
    const router = createMessageRouter({ bus: createMessageBus(), registry });

    const messageDelivery = router.routeMessage({
      ...plannerToAuditorMessage(),
      message_id: "msg_critic_to_executor",
      correlation_id: "corr_critic_executor",
      conversation_id: "conv_no_special_case_001",
      from: "critic",
      to: "executor",
    });

    expect(messageDelivery.status).toBe("MESSAGE_ROUTED");
    expect(messageDelivery.from).toBe("critic");
    expect(messageDelivery.to).toBe("executor");
  });
});

function readyRegistry() {
  const registry = createThreadRegistry();
  registry.register({ role: "worker", threadId: "thread_worker_001", cwd: "A:/synthetic" });
  registry.register({ role: "reviewer", threadId: "thread_reviewer_001", cwd: "A:/synthetic" });
  return registry;
}

function readyMultiroleRegistry() {
  const registry = readyRegistry();
  registry.register({ role: "verifier", threadId: "thread_verifier_001", cwd: "A:/synthetic" });
  return registry;
}

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

function workerMessageForRound(round: 1 | 2): MessageToCodex {
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

function reviewerReplyForRound(round: 1 | 2): CodexMessageReply {
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

function plannerToAuditorMessage(): MessageToCodex {
  return {
    type: "MESSAGE_TO_CODEX",
    message_id: "msg_planner_to_auditor",
    correlation_id: "corr_planner_auditor",
    conversation_id: "conv_arbitrary_roles_001",
    from: "planner",
    to: "auditor",
    kind: "request_review",
    payload: {
      question: "Please review this transport-level route.",
      context: [],
      expected_response: "status",
    },
  };
}

function auditorToPlannerReply(): CodexMessageReply {
  return {
    type: "CODEX_MESSAGE_REPLY",
    message_id: "msg_auditor_to_planner",
    reply_to: "msg_planner_to_auditor",
    correlation_id: "corr_planner_auditor",
    conversation_id: "conv_arbitrary_roles_001",
    from: "auditor",
    to: "planner",
    kind: "status",
    payload: {
      decision: "observed",
      reason: "Arbitrary registered roles are routing identities.",
      next_instruction: "Continue without role-policy interpretation.",
    },
  };
}
