import type { ReviewerDecision, WorkerDone } from "./event_contracts.js";

export interface E2eSafeReviewBoundaryInput {
  readonly snapshotRoot: string;
  readonly appServerProcessCwd: string;
  readonly workerCwd: string;
  readonly reviewerCwd: string;
  readonly workerDone: WorkerDone;
  readonly reviewerDecision: ReviewerDecision;
  readonly policyDecisionCount: number;
}

export interface E2eSafeReviewBoundarySummary {
  readonly appServerProcessCwdSnapshot: true;
  readonly workerCwdSnapshot: true;
  readonly reviewerCwdSnapshot: true;
  readonly workerOutputDone: true;
  readonly reviewerDecisionContinue: true;
  readonly policyDecisionCount: number;
  readonly directRealRepo: "BLOCKED";
  readonly managedWorkerStarted: "STARTED";
  readonly managedReviewerStarted: "STARTED";
}

export function createE2eSafeReviewBoundarySummary(input: E2eSafeReviewBoundaryInput): E2eSafeReviewBoundarySummary {
  if (input.appServerProcessCwd !== input.snapshotRoot) {
    throw new Error("E2E App Server process cwd must be the snapshot root");
  }
  if (input.workerCwd !== input.snapshotRoot) {
    throw new Error("E2E Worker cwd must be the snapshot root");
  }
  if (input.reviewerCwd !== input.snapshotRoot) {
    throw new Error("E2E Reviewer cwd must be the snapshot root");
  }
  if (input.workerDone.type !== "DONE") {
    throw new Error("E2E Worker output must be DONE");
  }
  if (input.reviewerDecision.type !== "REVIEWER_DECISION") {
    throw new Error("E2E Reviewer output must be REVIEWER_DECISION");
  }
  assertReviewerDecisionAllowsContinuation(input.reviewerDecision);
  return {
    appServerProcessCwdSnapshot: true,
    workerCwdSnapshot: true,
    reviewerCwdSnapshot: true,
    workerOutputDone: true,
    reviewerDecisionContinue: true,
    policyDecisionCount: input.policyDecisionCount,
    directRealRepo: "BLOCKED",
    managedWorkerStarted: "STARTED",
    managedReviewerStarted: "STARTED",
  };
}

export function assertReviewerDecisionAllowsContinuation(reviewerDecision: ReviewerDecision): void {
  if (reviewerDecision.type !== "REVIEWER_DECISION") {
    throw new Error("E2E Reviewer output must be REVIEWER_DECISION");
  }
  if (reviewerDecision.decision !== "continue") {
    throw new Error(`E2E Reviewer decision must be continue before PASS: ${reviewerDecision.decision}`);
  }
}
