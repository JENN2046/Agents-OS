import type { AppServerClient } from "../appserver/client.js";
import type { ThreadStartResponse } from "../generated/appserver/v2/ThreadStartResponse";
import type { Turn } from "../generated/appserver/v2/Turn";
import type { TurnStartResponse } from "../generated/appserver/v2/TurnStartResponse";
import type { EventStore } from "../stores/event_store.js";
import type { JobStore } from "../stores/job_store.js";
import type { ReceiptStore } from "../stores/receipt_store.js";
import type { JobRecord } from "../types/jobs.js";
import { createStateTransitionEvent, type LoopEvent } from "../types/events.js";
import {
  createSyntheticTurnStartParams,
  reviewerDecisionSchema,
  validateStructuredLoopOutput,
  workerDoneSchema,
  workerNeedReviewerSchema,
  type ReviewerDecision,
  type WorkerDone,
  type WorkerNeedReviewer,
} from "./event_contracts.js";
import { reviewerDecisionPrompt, workerDonePrompt, workerNeedReviewerPrompt } from "./prompts.js";
import { transitionState, type ActiveLoopState } from "./state_machine.js";

export interface OrchestratorPlan {
  readonly jobId: string;
  readonly syntheticWorkspaceRoot: string;
}

export interface ActiveLoopStores {
  readonly jobs: JobStore;
  readonly events: EventStore;
  readonly receipts: ReceiptStore;
}

export interface ActiveLoopOrchestratorOptions {
  readonly client: Pick<AppServerClient, "threadStart" | "turnStart" | "turnSteer">;
  readonly stores: ActiveLoopStores;
  readonly plan: OrchestratorPlan;
  readonly initialState?: ActiveLoopState;
  readonly now?: () => Date;
}

export interface ActiveLoopResult {
  readonly finalState: ActiveLoopState;
  readonly workerNeedReviewer: WorkerNeedReviewer;
  readonly reviewerDecision: ReviewerDecision;
  readonly workerDone: WorkerDone;
  readonly workerThreadId: string;
  readonly reviewerThreadId: string;
  readonly receiptPath: string;
}

export function createOrchestratorPlan(jobId: string, syntheticWorkspaceRoot: string): OrchestratorPlan {
  return { jobId, syntheticWorkspaceRoot };
}

export function createActiveLoopOrchestrator(options: ActiveLoopOrchestratorOptions) {
  return new ActiveLoopOrchestrator(options);
}

class ActiveLoopOrchestrator {
  readonly #client: ActiveLoopOrchestratorOptions["client"];
  readonly #stores: ActiveLoopStores;
  readonly #plan: OrchestratorPlan;
  readonly #now: () => Date;
  readonly #createdAt: string;
  #state: ActiveLoopState;

  constructor(options: ActiveLoopOrchestratorOptions) {
    this.#client = options.client;
    this.#stores = options.stores;
    this.#plan = options.plan;
    this.#now = options.now ?? (() => new Date());
    this.#state = options.initialState ?? "SYNTHETIC_WORKSPACE_READY";
    this.#createdAt = this.#now().toISOString();
  }

  async runWorkerReviewerLoop(): Promise<ActiveLoopResult> {
    await this.#writeJob();

    const workerThread = await this.#client.threadStart({
      cwd: this.#plan.syntheticWorkspaceRoot,
      sandbox: "read-only",
      ephemeral: true,
      baseInstructions: "MVP Worker. Use only the synthetic workspace. Return structured JSON only.",
    });
    await this.#transition("WORKER_THREAD_STARTED", "worker thread started");

    const workerNeedReviewerTurn = await this.#client.turnStart(
      createSyntheticTurnStartParams({
        threadId: getThreadId(workerThread),
        syntheticWorkspaceRoot: this.#plan.syntheticWorkspaceRoot,
        prompt: workerNeedReviewerPrompt,
        outputSchema: workerNeedReviewerSchema,
      }),
    );
    await this.#transition("WORKER_RUNNING", "worker turn started");
    const workerNeedReviewer = parseStructuredTurnOutput(workerNeedReviewerTurn.turn, "NEED_REVIEWER");
    await this.#transition("NEED_REVIEWER", "worker emitted NEED_REVIEWER");

    const reviewerThread = await this.#client.threadStart({
      cwd: this.#plan.syntheticWorkspaceRoot,
      sandbox: "read-only",
      ephemeral: true,
      baseInstructions: "MVP Reviewer. Use only the synthetic workspace. Return structured JSON only.",
    });
    await this.#transition("REVIEWER_THREAD_STARTED", "reviewer thread started");

    const reviewerDecisionTurn = await this.#client.turnStart(
      createSyntheticTurnStartParams({
        threadId: getThreadId(reviewerThread),
        syntheticWorkspaceRoot: this.#plan.syntheticWorkspaceRoot,
        prompt: `${reviewerDecisionPrompt}\n\nWorker payload:\n${JSON.stringify(workerNeedReviewer)}`,
        outputSchema: reviewerDecisionSchema,
      }),
    );
    await this.#transition("REVIEWER_RUNNING", "reviewer turn started");
    const reviewerDecision = parseStructuredTurnOutput(reviewerDecisionTurn.turn, "REVIEWER_DECISION");
    await this.#transition("REVIEW_RECEIVED", "reviewer emitted REVIEWER_DECISION");

    const workerDoneTurn = await this.#client.turnStart(
      createSyntheticTurnStartParams({
        threadId: getThreadId(workerThread),
        syntheticWorkspaceRoot: this.#plan.syntheticWorkspaceRoot,
        prompt: `${workerDonePrompt}\n\nReviewer decision:\n${JSON.stringify(reviewerDecision)}`,
        outputSchema: workerDoneSchema,
      }),
    );
    await this.#transition("CODEX_RESUMED", "worker resumed with reviewer decision");
    const workerDone = parseStructuredTurnOutput(workerDoneTurn.turn, "DONE");

    const receiptPath = await this.#stores.receipts.write({
      jobId: this.#plan.jobId,
      result: "PASS",
      finalState: "DONE",
      validation: ["worker NEED_REVIEWER parsed", "reviewer REVIEWER_DECISION parsed", "worker DONE parsed"],
      artifacts: [this.#stores.events.pathFor(this.#plan.jobId), this.#stores.jobs.pathFor(this.#plan.jobId)],
      boundaryFlags: {
        synthetic_workspace_only: "YES",
        read_only_sandbox: "YES",
        malformed_structured_output_rejected: "YES",
      },
    });
    await this.#transition("DONE", "worker emitted DONE and receipt was written");

    await this.#appendEvent({
      jobId: this.#plan.jobId,
      type: "RECEIPT_WRITTEN",
      at: this.#now().toISOString(),
      state: this.#state,
      payload: { receiptPath },
    });
    await this.#writeJob({ receiptPath });

    return {
      finalState: this.#state,
      workerNeedReviewer,
      reviewerDecision,
      workerDone,
      workerThreadId: getThreadId(workerThread),
      reviewerThreadId: getThreadId(reviewerThread),
      receiptPath,
    };
  }

  async #transition(to: ActiveLoopState, reason: string): Promise<void> {
    const result = transitionState(this.#state, to, reason, this.#now());
    this.#state = result.state;
    await this.#appendEvent(createStateTransitionEvent(this.#plan.jobId, result.transition));
    if (!result.ok) {
      await this.#writeJob();
      throw new Error(result.error ?? "invalid state transition");
    }
    await this.#writeJob();
  }

  async #appendEvent(event: LoopEvent): Promise<void> {
    await this.#stores.events.append(this.#plan.jobId, event);
  }

  async #writeJob(extra: Partial<JobRecord> = {}): Promise<void> {
    const now = this.#now().toISOString();
    await this.#stores.jobs.put({
      jobId: this.#plan.jobId,
      createdAt: extra.createdAt ?? this.#createdAt,
      updatedAt: now,
      state: this.#state,
      syntheticWorkspaceRoot: this.#plan.syntheticWorkspaceRoot,
      eventLogPath: this.#stores.events.pathFor(this.#plan.jobId),
      ...extra,
    });
  }
}

export function parseStructuredTurnOutput<T extends "NEED_REVIEWER" | "REVIEWER_DECISION" | "DONE">(
  turn: Turn,
  expectedType: T,
): Extract<WorkerNeedReviewer | ReviewerDecision | WorkerDone, { type: T }> {
  const text = [...turn.items]
    .reverse()
    .find((item) => item.type === "agentMessage")
    ?.text.trim();
  if (!text) {
    throw new Error(`missing agentMessage output for ${expectedType}`);
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (error) {
    throw new Error(`malformed structured output for ${expectedType}: ${error instanceof Error ? error.message : "parse failed"}`);
  }

  if (!validateStructuredLoopOutput(parsed) || parsed.type !== expectedType) {
    throw new Error(`invalid structured output for ${expectedType}`);
  }

  return parsed as Extract<WorkerNeedReviewer | ReviewerDecision | WorkerDone, { type: T }>;
}

function getThreadId(response: ThreadStartResponse): string {
  return response.thread.id;
}
