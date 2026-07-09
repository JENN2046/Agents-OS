import path from "node:path";
import { mkdir } from "node:fs/promises";
import { createAppServerClient } from "../appserver/client.js";
import { createStdioTransport } from "../appserver/transport_stdio.js";
import {
  createSyntheticTurnStartParams,
  reviewerDecisionSchema,
  validateStructuredLoopOutput,
  workerDoneSchema,
  workerNeedReviewerSchema,
  type ReviewerDecision,
  type WorkerDone,
  type WorkerNeedReviewer,
} from "../bridge/event_contracts.js";
import { reviewerDecisionPrompt, workerDonePrompt, workerNeedReviewerPrompt } from "../bridge/prompts.js";
import { transitionState, type ActiveLoopState } from "../bridge/state_machine.js";
import { createServerRequestResponsePlan, type PolicyDecision } from "../bridge/policy_gate.js";
import type { JsonValue } from "../generated/appserver/serde_json/JsonValue";
import type { ServerNotification } from "../generated/appserver/ServerNotification";
import type { ServerRequest } from "../generated/appserver/ServerRequest";
import type { ThreadStartResponse } from "../generated/appserver/v2/ThreadStartResponse";
import type { Turn } from "../generated/appserver/v2/Turn";
import { createFileEventStore } from "../stores/event_store.js";
import { createFileJobStore } from "../stores/job_store.js";
import { createFileReceiptStore } from "../stores/receipt_store.js";
import { createFileReportStore } from "../stores/report_store.js";
import { createStateTransitionEvent, type LoopEvent } from "../types/events.js";
import type { JobRecord } from "../types/jobs.js";

const TURN_TIMEOUT_MS = 180_000;
const REQUEST_TIMEOUT_MS = 60_000;

const boundaryFlags = {
  workspace_agents_api: "NOT_USED",
  responses_api: "NOT_USED",
  browser_automation: "NOT_USED",
  websocket: "NOT_USED",
  thread_shell_command: "NOT_USED",
  command_exec: "NOT_USED",
  command_exec_write: "NOT_USED",
  process_api: "NOT_USED",
  full_access: "NOT_USED",
  danger_full_access: "NOT_USED",
  real_repo_smoke: "NOT_USED",
  commit_push_deploy_release_tag: "NOT_USED",
  experimental_api: "NOT_USED",
} as const;

type BoundaryFlags = Record<keyof typeof boundaryFlags, "USED" | "NOT_USED" | "BLOCKED" | "REDACTED">;
type ExpectedOutputType = "NEED_REVIEWER" | "REVIEWER_DECISION" | "DONE";

interface TurnTracker {
  readonly completedTurns: Map<string, Turn>;
  readonly agentTextByTurn: Map<string, string>;
}

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const syntheticWorkspaceRoot = path.join(projectRoot, "data", "synthetic-workspace");
  const jobId = `cea-007-real-smoke-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}`;
  const createdAt = new Date().toISOString();
  let state: ActiveLoopState = "CREATED";

  const jobs = createFileJobStore(path.join(projectRoot, "data", "jobs"));
  const events = createFileEventStore(path.join(projectRoot, "data", "events"));
  const receipts = createFileReceiptStore(path.join(projectRoot, "data", "receipts"));
  const reports = createFileReportStore(path.join(projectRoot, "data", "reports"));

  const appendEvent = async (type: LoopEvent["type"], payload: unknown, eventState = state): Promise<void> => {
    await events.append(jobId, {
      jobId,
      type,
      at: new Date().toISOString(),
      state: eventState,
      payload,
    });
  };

  const writeJob = async (extra: Partial<JobRecord> = {}): Promise<void> => {
    await jobs.put({
      jobId,
      createdAt,
      updatedAt: new Date().toISOString(),
      state,
      syntheticWorkspaceRoot,
      eventLogPath: events.pathFor(jobId),
      boundaryFlags: { ...boundaryFlags },
      ...extra,
    });
  };

  const transition = async (to: ActiveLoopState, reason: string): Promise<void> => {
    const result = transitionState(state, to, reason);
    state = result.state;
    await events.append(jobId, createStateTransitionEvent(jobId, result.transition));
    await writeJob();
    if (!result.ok) {
      throw new Error(result.error ?? "invalid state transition");
    }
  };

  await mkdir(syntheticWorkspaceRoot, { recursive: true });
  const transport = createStdioTransport({
    cwd: syntheticWorkspaceRoot,
    timeoutMs: REQUEST_TIMEOUT_MS,
  });
  const client = createAppServerClient(transport, {
    requestTimeoutMs: REQUEST_TIMEOUT_MS,
    clientInfo: {
      name: "codex-appserver-active-loop",
      title: "Codex App Server Active Loop Smoke",
      version: "0.0.0",
    },
  });

  const tracker: TurnTracker = {
    completedTurns: new Map(),
    agentTextByTurn: new Map(),
  };
  const eventWrites: Promise<void>[] = [];
  const policyDecisions: PolicyDecision[] = [];
  let stopReason: string | undefined;

  const recordEvent = (type: LoopEvent["type"], payload: unknown, eventState = state): void => {
    eventWrites.push(appendEvent(type, payload, eventState));
  };

  client.onNotification((notification) => {
    trackNotification(tracker, notification);
    recordEvent("APP_SERVER_MESSAGE", summarizeNotification(notification));
  });
  client.onServerRequest((request) => {
    const plan = createServerRequestResponsePlan(request);
    const decision = plan.policyDecision;
    policyDecisions.push(decision);
    if (plan.response.kind === "result") {
      client.respondToServerRequest(request.id, plan.response.result);
    } else {
      client.respondToServerRequestError(request.id, plan.response.code, plan.response.message, plan.response.data);
    }
    recordEvent("POLICY_DECISION", {
      request: summarizeServerRequest(request),
      decision,
      responseKind: plan.response.kind,
    });
    if (decision.kind !== "allow" && !stopReason) {
      stopReason = `${decision.kind}: ${decision.reason}`;
    }
  });
  transport.on("stderr", (chunk) => {
    recordEvent("APP_SERVER_MESSAGE", {
      method: "stderr",
      byteLength: Buffer.byteLength(chunk, "utf8"),
      hasWarning: /\bWARN\b|warning/i.test(chunk),
      hasError: /\bERROR\b|error/i.test(chunk),
    });
  });

  await writeJob();

  try {
    await client.start();
    await appendEvent("APP_SERVER_MESSAGE", { method: "app-server/start", cwd: syntheticWorkspaceRoot });
    await transition("APP_SERVER_STARTED", "real codex app-server --stdio started in synthetic workspace");

    const initializeResponse = await client.initialize();
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "initialize/result",
      codexHomeRedacted: Boolean(initializeResponse.codexHome),
      userAgent: initializeResponse.userAgent,
      platformFamily: initializeResponse.platformFamily,
      platformOs: initializeResponse.platformOs,
    });
    client.sendInitialized();
    await transition("INITIALIZED", "initialize and initialized completed without experimentalApi");

    await transition("SCHEMA_GENERATED", "schemas were generated in phase0 and reused by smoke");
    await transition("SYNTHETIC_WORKSPACE_READY", "synthetic read-only workspace selected");

    const workerThread = await startThread("Worker");
    await transition("WORKER_THREAD_STARTED", "worker thread started");

    const workerNeedReviewer = await runTurnAndParse<"NEED_REVIEWER">({
      threadId: getThreadId(workerThread),
      prompt: workerNeedReviewerPrompt,
      outputSchema: workerNeedReviewerSchema,
      expectedType: "NEED_REVIEWER",
      runningState: "WORKER_RUNNING",
      runningReason: "worker turn started",
      completedState: "NEED_REVIEWER",
      completedReason: "worker emitted NEED_REVIEWER",
    });

    const reviewerThread = await startThread("Reviewer");
    await transition("REVIEWER_THREAD_STARTED", "reviewer thread started");

    const reviewerDecision = await runTurnAndParse<"REVIEWER_DECISION">({
      threadId: getThreadId(reviewerThread),
      prompt: `${reviewerDecisionPrompt}\n\nWorker payload:\n${JSON.stringify(workerNeedReviewer)}`,
      outputSchema: reviewerDecisionSchema,
      expectedType: "REVIEWER_DECISION",
      runningState: "REVIEWER_RUNNING",
      runningReason: "reviewer turn started",
      completedState: "REVIEW_RECEIVED",
      completedReason: "reviewer emitted REVIEWER_DECISION",
    });

    const workerDone = await runTurnAndParse<"DONE">({
      threadId: getThreadId(workerThread),
      prompt: `${workerDonePrompt}\n\nReviewer decision:\n${JSON.stringify(reviewerDecision)}`,
      outputSchema: workerDoneSchema,
      expectedType: "DONE",
      runningState: "CODEX_RESUMED",
      runningReason: "worker resumed with reviewer decision",
      completedState: "DONE",
      completedReason: "worker emitted DONE",
    });

    const receiptPath = await receipts.write({
      jobId,
      result: "PASS",
      finalState: state,
      validation: [
        "real App Server initialized",
        "worker NEED_REVIEWER parsed and validated",
        "reviewer REVIEWER_DECISION parsed and validated",
        "worker DONE parsed and validated",
      ],
      artifacts: [jobs.pathFor(jobId), events.pathFor(jobId), reports.pathForFinalReport()],
      boundaryFlags,
    });
    await appendEvent("RECEIPT_WRITTEN", { receiptPath });

    const report = {
      result: "PASS",
      job_id: jobId,
      final_state: state,
      real_app_server_smoke: "PASS",
      artifacts: {
        job: jobs.pathFor(jobId),
        events: events.pathFor(jobId),
        receipt: receiptPath,
        final_report: reports.pathForFinalReport(),
      },
      outputs: {
        worker_need_reviewer: workerNeedReviewer,
        reviewer_decision: reviewerDecision,
        worker_done: workerDone,
      },
      boundary_flags: boundaryFlags,
      policy_decisions: policyDecisions,
      stopped_reason: null,
    };
    const reportPath = await reports.writeFinalReport(report);
    await appendEvent("REPORT_WRITTEN", { reportPath });
    await writeJob({ receiptPath, reportPath });

    await Promise.all(eventWrites);
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    const failure = error instanceof Error ? error.message : "unknown smoke failure";
    const finalState: ActiveLoopState = stopReason ? "BLOCKED" : "FAILED";
    const terminalStates: readonly ActiveLoopState[] = ["DONE", "BLOCKED", "FAILED", "HUMAN_GATE_REQUIRED"];
    if (!terminalStates.includes(state)) {
      const result = transitionState(state, finalState, stopReason ?? failure);
      state = result.state;
      await events.append(jobId, createStateTransitionEvent(jobId, result.transition));
    }

    const result = stopReason ? "BLOCK" : "FAIL";
    const receiptPath = await receipts.write({
      jobId,
      result,
      finalState: state,
      validation: ["real App Server smoke did not complete"],
      artifacts: [jobs.pathFor(jobId), events.pathFor(jobId), reports.pathForFinalReport()],
      boundaryFlags,
      risks: [stopReason ?? failure],
    });
    const report = {
      result,
      job_id: jobId,
      final_state: state,
      real_app_server_smoke: result,
      artifacts: {
        job: jobs.pathFor(jobId),
        events: events.pathFor(jobId),
        receipt: receiptPath,
        final_report: reports.pathForFinalReport(),
      },
      boundary_flags: boundaryFlags,
      policy_decisions: policyDecisions,
      stopped_reason: stopReason ?? failure,
    };
    const reportPath = await reports.writeFinalReport(report);
    await appendEvent("RECEIPT_WRITTEN", { receiptPath });
    await appendEvent("REPORT_WRITTEN", { reportPath });
    await writeJob({ receiptPath, reportPath });
    await Promise.all(eventWrites);
    console.error(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await client.stop();
  }

  async function startThread(role: "Worker" | "Reviewer"): Promise<ThreadStartResponse> {
    const response = await client.threadStart({
      cwd: syntheticWorkspaceRoot,
      approvalPolicy: "never",
      sandbox: "read-only",
      ephemeral: true,
      baseInstructions: [
        `MVP ${role}.`,
        "Use only the synthetic workspace.",
        "Do not request command execution, file changes, browser automation, MCP tools, web search, network, or private state.",
        "Return only the final JSON object matching the provided output schema.",
      ].join(" "),
    });
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "thread/start/result",
      role,
      threadId: getThreadId(response),
    });
    return response;
  }

  async function runTurnAndParse<TExpected extends ExpectedOutputType>(input: {
    readonly threadId: string;
    readonly prompt: string;
    readonly outputSchema: Record<string, JsonValue>;
    readonly expectedType: TExpected;
    readonly runningState: ActiveLoopState;
    readonly runningReason: string;
    readonly completedState: ActiveLoopState;
    readonly completedReason: string;
  }): Promise<Extract<WorkerNeedReviewer | ReviewerDecision | WorkerDone, { type: TExpected }>> {
    const response = await client.turnStart(
      {
        ...createSyntheticTurnStartParams({
        threadId: input.threadId,
        syntheticWorkspaceRoot,
        prompt: input.prompt,
        outputSchema: input.outputSchema,
        }),
        summary: "none",
      },
    );
    await transition(input.runningState, input.runningReason);
    const completedTurn = await waitForCompletedTurn(tracker, response.turn, TURN_TIMEOUT_MS);
    if (stopReason) {
      throw new Error(stopReason);
    }
    const parsed = parseTurnOutput(completedTurn, input.expectedType, tracker.agentTextByTurn.get(completedTurn.id));
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "structured-output/parsed",
      expectedType: input.expectedType,
      turnId: completedTurn.id,
      output: parsed,
    });
    await transition(input.completedState, input.completedReason);
    return parsed;
  }
}

function trackNotification(tracker: TurnTracker, notification: ServerNotification): void {
  if (notification.method === "item/agentMessage/delta") {
    const current = tracker.agentTextByTurn.get(notification.params.turnId) ?? "";
    tracker.agentTextByTurn.set(notification.params.turnId, `${current}${notification.params.delta}`);
    return;
  }

  if (notification.method === "turn/completed") {
    tracker.completedTurns.set(notification.params.turn.id, notification.params.turn);
  }
}

function waitForCompletedTurn(tracker: TurnTracker, initialTurn: Turn, timeoutMs: number): Promise<Turn> {
  if (initialTurn.status === "completed") {
    return Promise.resolve(initialTurn);
  }
  if (initialTurn.status === "failed") {
    return Promise.reject(new Error(formatTurnFailure(initialTurn)));
  }

  const existing = tracker.completedTurns.get(initialTurn.id);
  if (existing) {
    return existing.status === "failed" ? Promise.reject(new Error(formatTurnFailure(existing))) : Promise.resolve(existing);
  }

  return new Promise((resolve, reject) => {
    const startedAt = Date.now();
    const timer = setInterval(() => {
      const completed = tracker.completedTurns.get(initialTurn.id);
      if (completed) {
        clearInterval(timer);
        if (completed.status === "failed") {
          reject(new Error(formatTurnFailure(completed)));
          return;
        }
        resolve(completed);
        return;
      }
      if (Date.now() - startedAt > timeoutMs) {
        clearInterval(timer);
        reject(new Error(`timed out waiting for turn completion: ${initialTurn.id}`));
      }
    }, 250);
  });
}

function parseTurnOutput<TExpected extends ExpectedOutputType>(
  turn: Turn,
  expectedType: TExpected,
  fallbackText?: string,
): Extract<WorkerNeedReviewer | ReviewerDecision | WorkerDone, { type: TExpected }> {
  const text =
    [...turn.items]
      .reverse()
      .find((item) => item.type === "agentMessage")
      ?.text.trim() ?? fallbackText?.trim();
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

  return parsed as Extract<WorkerNeedReviewer | ReviewerDecision | WorkerDone, { type: TExpected }>;
}

function summarizeNotification(notification: ServerNotification): unknown {
  switch (notification.method) {
    case "item/agentMessage/delta":
      return {
        method: notification.method,
        threadId: notification.params.threadId,
        turnId: notification.params.turnId,
        itemId: notification.params.itemId,
        deltaLength: notification.params.delta.length,
      };
    case "item/completed":
      return {
        method: notification.method,
        threadId: notification.params.threadId,
        turnId: notification.params.turnId,
        itemType: notification.params.item.type,
      };
    case "turn/completed":
      return {
        method: notification.method,
        threadId: notification.params.threadId,
        turnId: notification.params.turn.id,
        status: notification.params.turn.status,
        itemTypes: notification.params.turn.items.map((item) => item.type),
      };
    case "turn/started":
      return {
        method: notification.method,
        params: notification.params,
      };
    default:
      return {
        method: notification.method,
      };
  }
}

function summarizeServerRequest(request: ServerRequest): unknown {
  return {
    method: request.method,
    id: request.id,
  };
}

function formatTurnFailure(turn: Turn): string {
  return `turn failed: ${turn.id}${turn.error ? ` ${JSON.stringify(turn.error)}` : ""}`;
}

function getThreadId(response: ThreadStartResponse): string {
  return response.thread.id;
}

void main();
