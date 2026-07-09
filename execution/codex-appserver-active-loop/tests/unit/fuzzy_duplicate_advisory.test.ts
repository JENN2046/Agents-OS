import { describe, expect, it } from "vitest";
import { createMessageBus } from "../../src/bridge/message_bus.js";
import { createFuzzyDuplicateAdvisory } from "../../src/bridge/fuzzy_duplicate_advisory.js";
import type { CodexMessageReply, MessageToCodex } from "../../src/types/messages.js";

describe("fuzzy duplicate advisory", () => {
  it("emits non-authoritative near-duplicate metadata without raw payload text", () => {
    const advisory = createFuzzyDuplicateAdvisory({
      message: nearDuplicateWorkerMessage(),
      candidates: [workerMessage()],
    });

    expect(advisory).toMatchObject({
      suspected_near_duplicate: true,
      compared_with: "msg_worker_001",
      message_id: "msg_worker_002",
      action_taken: "NONE",
      authority: "ADVISORY_ONLY",
      candidate_count: 1,
    });
    expect(advisory.similarity).toBeGreaterThanOrEqual(0.8);
    expect(advisory.payload_hash).toMatch(/^sha256:/);
    expect(advisory.compared_with_payload_hash).toMatch(/^sha256:/);
    expect(JSON.stringify(advisory)).not.toContain("Please review this decision point");
    expect(JSON.stringify(advisory)).not.toContain("Please review this decision point again");
  });

  it("does not alter exact Message Bus delivery decisions for high-similarity traffic", () => {
    const bus = createMessageBus({ maxRounds: 3 });

    bus.captureMessage(workerMessage());
    bus.markRouted("msg_worker_001", "thread_reviewer_001");
    bus.captureReply(reviewerReply(), "thread_worker_001");

    const advisory = createFuzzyDuplicateAdvisory({
      message: nearDuplicateWorkerMessage(),
      candidates: [workerMessage()],
    });

    expect(advisory.suspected_near_duplicate).toBe(true);
    expect(advisory.action_taken).toBe("NONE");
    expect(() => bus.captureMessage(nearDuplicateWorkerMessage())).not.toThrow();
    expect(() => bus.markRouted("msg_worker_002", "thread_reviewer_001")).not.toThrow();
    expect(() => bus.captureReply(nearDuplicateReviewerReply(), "thread_worker_001")).not.toThrow();
    expect(bus.getConversationState("conv_channel_001")?.round_count).toBe(2);
    expect(bus.auditEvents().filter((event) => event.event === "MESSAGE_ROUTED")).toHaveLength(2);
    expect(bus.auditEvents().map((event) => event.event)).not.toContain("MESSAGE_REJECTED");
  });

  it("does not override exact duplicate-id rejection", () => {
    const bus = createMessageBus();
    bus.captureMessage(workerMessage());
    const duplicate = {
      ...nearDuplicateWorkerMessage(),
      message_id: "msg_worker_001",
      correlation_id: "corr_channel_002",
    };

    const advisory = createFuzzyDuplicateAdvisory({
      message: duplicate,
      candidates: [workerMessage()],
    });

    expect(advisory.action_taken).toBe("NONE");
    expect(() => bus.captureMessage(duplicate)).toThrow("duplicate message id: msg_worker_001");
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
      context: ["The message bus must keep delivery decisions exact."],
      expected_response: "decision",
    },
  };
}

function nearDuplicateWorkerMessage(): MessageToCodex {
  return {
    ...workerMessage(),
    message_id: "msg_worker_002",
    correlation_id: "corr_channel_002",
    payload: {
      question: "Please review this decision point again.",
      context: ["The message bus must keep delivery decisions exact."],
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
      reason: "First exact route accepted.",
      next_instruction: "Continue.",
    },
  };
}

function nearDuplicateReviewerReply(): CodexMessageReply {
  return {
    ...reviewerReply(),
    message_id: "msg_reviewer_002",
    reply_to: "msg_worker_002",
    correlation_id: "corr_channel_002",
    payload: {
      decision: "continue",
      reason: "Second exact route accepted despite fuzzy advisory.",
      next_instruction: "Continue.",
    },
  };
}
