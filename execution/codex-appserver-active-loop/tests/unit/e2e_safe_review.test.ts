import { describe, expect, it } from "vitest";
import type { Turn } from "../../src/generated/appserver/v2/Turn.js";
import {
  assertReviewerDecisionAllowsContinuation,
  assertSafeReviewTurnCompleted,
  createE2eSafeReviewBoundarySummary,
  rejectSafeReviewTerminalNonCompletedTurn,
} from "../../src/bridge/e2e_safe_review.js";

describe("E2E safe review boundary summary", () => {
  it("accepts only snapshot-bound Worker and Reviewer cwd", () => {
    const summary = createE2eSafeReviewBoundarySummary({
      snapshotRoot: "A:/snapshot",
      appServerProcessCwd: "A:/snapshot",
      workerCwd: "A:/snapshot",
      reviewerCwd: "A:/snapshot",
      workerDone: { type: "DONE", summary: "ok", evidence: ["snapshot"] },
      reviewerDecision: {
        type: "REVIEWER_DECISION",
        decision: "continue",
        reason: "ok",
        next_instruction: "continue",
        constraints: ["snapshot"],
        evidence_used: ["snapshot"],
      },
      policyDecisionCount: 0,
    });

    expect(summary.appServerProcessCwdSnapshot).toBe(true);
    expect(summary.workerCwdSnapshot).toBe(true);
    expect(summary.reviewerCwdSnapshot).toBe(true);
    expect(summary.reviewerDecisionContinue).toBe(true);
    expect(summary.directRealRepo).toBe("BLOCKED");
  });

  it("rejects direct real repo cwd", () => {
    expect(() =>
      createE2eSafeReviewBoundarySummary({
        snapshotRoot: "A:/snapshot",
        appServerProcessCwd: "A:/snapshot",
        workerCwd: "A:/real-repo",
        reviewerCwd: "A:/snapshot",
        workerDone: { type: "DONE", summary: "ok", evidence: [] },
        reviewerDecision: {
          type: "REVIEWER_DECISION",
          decision: "continue",
          reason: "ok",
          next_instruction: "continue",
          constraints: [],
          evidence_used: [],
        },
        policyDecisionCount: 0,
      }),
    ).toThrow("Worker cwd");
  });

  it("rejects Reviewer block decisions before PASS", () => {
    expect(() =>
      assertReviewerDecisionAllowsContinuation({
        type: "REVIEWER_DECISION",
        decision: "block",
        reason: "missing evidence",
        next_instruction: "stop",
        constraints: [],
        evidence_used: [],
      }),
    ).toThrow("must be continue");
  });

  it("rejects interrupted turns before safe-review output parsing", () => {
    expect(() => assertSafeReviewTurnCompleted(makeTurn("interrupted"))).toThrow("status=interrupted");
    expect(() => rejectSafeReviewTerminalNonCompletedTurn(makeTurn("interrupted"))).toThrow("status=interrupted");
  });

  it("allows only in-progress turns to keep waiting", () => {
    expect(() => rejectSafeReviewTerminalNonCompletedTurn(makeTurn("inProgress"))).not.toThrow();
    expect(() => assertSafeReviewTurnCompleted(makeTurn("inProgress"))).toThrow("status=inProgress");
  });

  it("keeps failed turn errors explicit", () => {
    expect(() => assertSafeReviewTurnCompleted(makeTurn("failed", "worker failed"))).toThrow("worker failed");
  });
});

function makeTurn(status: string, message: string | null = null): Turn {
  return {
    id: "turn-1",
    items: [],
    itemsView: { type: "all" },
    status,
    error: message ? { message, codexErrorInfo: null, additionalDetails: null } : null,
    startedAt: null,
    completedAt: null,
    durationMs: null,
  } as unknown as Turn;
}
