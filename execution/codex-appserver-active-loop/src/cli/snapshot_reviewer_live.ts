import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { createAppServerClient } from "../appserver/client.js";
import { createStdioTransport } from "../appserver/transport_stdio.js";
import { createServerRequestResponsePlan, type PolicyDecision } from "../bridge/policy_gate.js";
import { assertPromptAnnex, type PromptAnnex } from "../bridge/prompt_annex.js";
import { createSnapshotReviewerLivePrompt, type SnapshotWorkerLiveEvidence } from "../bridge/snapshot_reviewer_live.js";
import {
  assertSnapshotBoundWorkerPlan,
  assertSnapshotBoundWorkerPlanLiveBoundary,
  assertSnapshotBoundWorkerPlanPathBoundary,
  type SnapshotBoundWorkerPlan,
} from "../bridge/snapshot_worker_pilot.js";
import type { SnapshotManifest } from "../bridge/repo_snapshot.js";
import { reviewerDecisionSchema, validateStructuredLoopOutput, type ReviewerDecision } from "../bridge/event_contracts.js";
import type { ServerNotification } from "../generated/appserver/ServerNotification";
import type { ServerRequest } from "../generated/appserver/ServerRequest";
import type { Turn } from "../generated/appserver/v2/Turn";
import { createFileEventStore } from "../stores/event_store.js";
import { safeJoin } from "../stores/safe_path.js";
import type { LoopEvent } from "../types/events.js";

const TURN_TIMEOUT_MS = 180_000;
const REQUEST_TIMEOUT_MS = 60_000;

interface TurnTracker {
  readonly completedTurns: Map<string, Turn>;
  readonly agentTextByTurn: Map<string, string>;
}

interface Cea016PrepReport {
  readonly pilot?: {
    readonly plan_path?: unknown;
  };
}

const boundaryFlags = {
  app_server_process_cwd_snapshot: "YES",
  reviewer_thread_cwd_snapshot: "YES",
  reviewer_turn_cwd_snapshot: "YES",
  sandbox_read_only_network_off: "YES",
  context_auto_injection: "DISABLED",
  direct_real_repo: "BLOCKED",
  managed_worker_evidence_used: "YES",
  managed_reviewer_started: "STARTED",
  command_exec: "NOT_USED",
  file_write: "NOT_USED",
  secrets_read: "NOT_USED",
  commit_push_deploy_release_tag: "NOT_USED",
} as const;

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const jobId = `cea-017-live-snapshot-reviewer-${timestamp}`;
  const events = createFileEventStore(path.join(projectRoot, "data", "events"));
  const reportPath = path.join(projectRoot, "data", "reports", "cea-017_snapshot_bound_reviewer_pilot.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", "2026-07-07-cea-017-snapshot-bound-reviewer-pilot.receipt.md");
  const prepReport = JSON.parse(
    await readFile(path.join(projectRoot, "data", "reports", "cea-016_snapshot_bound_worker_prep.json"), "utf8"),
  ) as Cea016PrepReport;
  const planPath = typeof prepReport.pilot?.plan_path === "string" ? prepReport.pilot.plan_path : "";
  if (!planPath) {
    throw new Error("CEA-016 prep plan path is missing");
  }
  const plan = JSON.parse(await readFile(planPath, "utf8")) as SnapshotBoundWorkerPlan;
  assertSnapshotBoundWorkerPlan(plan);
  assertSnapshotBoundWorkerPlanPathBoundary(projectRoot, plan);
  const manifest = JSON.parse(await readFile(plan.manifestPath, "utf8")) as SnapshotManifest;
  assertSnapshotBoundWorkerPlanLiveBoundary(projectRoot, plan, manifest);
  const verifiedSnapshotRoot = path.resolve(plan.snapshotRoot);
  const verifiedWorkerCwd = path.resolve(plan.workerCwd);
  const annex = JSON.parse(await readFile(plan.annexRef, "utf8")) as PromptAnnex;
  assertPromptAnnex(annex);
  const workerEvidence = JSON.parse(
    await readFile(path.join(projectRoot, "data", "reports", "cea-016_live_snapshot_worker_run.json"), "utf8"),
  ) as SnapshotWorkerLiveEvidence;
  const prompt = createSnapshotReviewerLivePrompt({ plan, annex, workerEvidence });

  const tracker: TurnTracker = { completedTurns: new Map(), agentTextByTurn: new Map() };
  const eventWrites: Promise<void>[] = [];
  const policyDecisions: PolicyDecision[] = [];
  let stopReason: string | undefined;
  let reviewerThreadId: string | undefined;
  let reviewerTurnId: string | undefined;

  const appendEvent = async (type: LoopEvent["type"], payload: unknown): Promise<void> => {
    await events.append(jobId, { jobId, type, at: new Date().toISOString(), payload });
  };
  const recordEvent = (type: LoopEvent["type"], payload: unknown): void => {
    eventWrites.push(appendEvent(type, payload));
  };

  const transport = createStdioTransport({ cwd: verifiedSnapshotRoot, timeoutMs: REQUEST_TIMEOUT_MS });
  const client = createAppServerClient(transport, {
    requestTimeoutMs: REQUEST_TIMEOUT_MS,
    clientInfo: {
      name: "codex-appserver-active-loop",
      title: "Snapshot-Bound Reviewer Pilot",
      version: "0.0.0",
    },
  });

  client.onNotification((notification) => {
    trackNotification(tracker, notification);
    recordEvent("APP_SERVER_MESSAGE", summarizeNotification(notification));
  });
  client.onServerRequest((request) => {
    const planResponse = createServerRequestResponsePlan(request);
    policyDecisions.push(planResponse.policyDecision);
    if (planResponse.response.kind === "result") {
      client.respondToServerRequest(request.id, planResponse.response.result);
    } else {
      client.respondToServerRequestError(
        request.id,
        planResponse.response.code,
        planResponse.response.message,
        planResponse.response.data,
      );
    }
    recordEvent("POLICY_DECISION", {
      request: summarizeServerRequest(request),
      decision: planResponse.policyDecision,
      responseKind: planResponse.response.kind,
    });
    if (planResponse.policyDecision.kind !== "allow" && !stopReason) {
      stopReason = `${planResponse.policyDecision.kind}: ${planResponse.policyDecision.reason}`;
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

  try {
    await client.start();
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "app-server/start",
      appServerProcessCwd: verifiedSnapshotRoot,
    });
    const initialized = await client.initialize();
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "initialize/result",
      codexHomeRedacted: Boolean(initialized.codexHome),
      userAgent: initialized.userAgent,
      platformFamily: initialized.platformFamily,
      platformOs: initialized.platformOs,
    });
    client.sendInitialized();

    const thread = await client.threadStart({
      cwd: verifiedWorkerCwd,
      approvalPolicy: "never",
      sandbox: "read-only",
      ephemeral: true,
      baseInstructions: [
        "Snapshot-bound Reviewer live pilot.",
        "Stay inside the safe snapshot cwd.",
        "Review only supplied Worker DONE evidence and metadata.",
        "Do not call tools, commands, approvals, network, or private state.",
        "Return only final JSON matching the output schema.",
      ].join(" "),
    });
    reviewerThreadId = thread.thread.id;
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "thread/start/result",
      role: "Reviewer",
      threadId: reviewerThreadId,
      cwd: verifiedWorkerCwd,
    });

    const turnStart = await client.turnStart({
      threadId: reviewerThreadId,
      input: [{ type: "text", text: prompt, text_elements: [] }],
      cwd: verifiedWorkerCwd,
      approvalPolicy: "never",
      sandboxPolicy: plan.sandboxPolicy,
      summary: "none",
      outputSchema: reviewerDecisionSchema,
    });
    reviewerTurnId = turnStart.turn.id;
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "turn/start/result",
      threadId: reviewerThreadId,
      turnId: reviewerTurnId,
      cwd: verifiedWorkerCwd,
      outputSchema: "REVIEWER_DECISION",
    });

    const completedTurn = await waitForCompletedTurn(tracker, turnStart.turn, TURN_TIMEOUT_MS);
    if (stopReason) {
      throw new Error(stopReason);
    }
    const reviewerDecision = parseReviewerDecision(completedTurn, tracker.agentTextByTurn.get(completedTurn.id));
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "structured-output/parsed",
      expectedType: "REVIEWER_DECISION",
      turnId: completedTurn.id,
      output: reviewerDecision,
    });

    const report = {
      task_id: "CEA-017",
      title: "Snapshot-Bound Reviewer Pilot",
      result: "PASS",
      completed_at: new Date().toISOString(),
      job_id: jobId,
      reviewer_thread_id: reviewerThreadId,
      reviewer_turn_id: reviewerTurnId,
      worker_job_id: workerEvidence.job_id,
      worker_turn_id: workerEvidence.worker_turn_id,
      prep_plan_id: plan.planId,
      prep_plan_path: planPath,
      snapshot_id: plan.snapshotId,
      reviewer_cwd: verifiedWorkerCwd,
      app_server_process_cwd: verifiedSnapshotRoot,
      annex_id: annex.annexId,
      output: reviewerDecision,
      artifacts: {
        events: events.pathFor(jobId),
        report: reportPath,
        receipt: receiptPath,
      },
      policy_decisions: policyDecisions,
      boundary_flags: boundaryFlags,
    };
    await writeJson(reportPath, report);
    await writeReceipt(receiptPath, report);
    await appendEvent("REPORT_WRITTEN", { reportPath });
    await appendEvent("RECEIPT_WRITTEN", { receiptPath });
    await Promise.all(eventWrites);
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    const failure = stopReason ?? (error instanceof Error ? error.message : "unknown live Reviewer failure");
    const report = {
      task_id: "CEA-017",
      title: "Snapshot-Bound Reviewer Pilot",
      result: stopReason ? "BLOCK" : "FAIL",
      completed_at: new Date().toISOString(),
      job_id: jobId,
      reviewer_thread_id: reviewerThreadId ?? null,
      reviewer_turn_id: reviewerTurnId ?? null,
      worker_job_id: workerEvidence.job_id,
      worker_turn_id: workerEvidence.worker_turn_id,
      prep_plan_id: plan.planId,
      prep_plan_path: planPath,
      snapshot_id: plan.snapshotId,
      reviewer_cwd: verifiedWorkerCwd,
      app_server_process_cwd: verifiedSnapshotRoot,
      annex_id: annex.annexId,
      stopped_reason: failure,
      artifacts: {
        events: events.pathFor(jobId),
        report: reportPath,
        receipt: receiptPath,
      },
      policy_decisions: policyDecisions,
      boundary_flags: boundaryFlags,
    };
    await writeJson(reportPath, report);
    await writeReceipt(receiptPath, report);
    await appendEvent("REPORT_WRITTEN", { reportPath });
    await appendEvent("RECEIPT_WRITTEN", { receiptPath });
    await Promise.all(eventWrites);
    console.error(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await client.stop();
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
  if (initialTurn.status === "completed") return Promise.resolve(initialTurn);
  if (initialTurn.status === "failed") return Promise.reject(new Error(formatTurnFailure(initialTurn)));
  const existing = tracker.completedTurns.get(initialTurn.id);
  if (existing) return existing.status === "failed" ? Promise.reject(new Error(formatTurnFailure(existing))) : Promise.resolve(existing);
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

function parseReviewerDecision(turn: Turn, fallbackText?: string): ReviewerDecision {
  const text =
    [...turn.items]
      .reverse()
      .find((item) => item.type === "agentMessage")
      ?.text.trim() ?? fallbackText?.trim();
  if (!text) {
    throw new Error("missing agentMessage output for REVIEWER_DECISION");
  }
  const parsed = JSON.parse(text) as unknown;
  if (!validateStructuredLoopOutput(parsed) || parsed.type !== "REVIEWER_DECISION") {
    throw new Error("invalid structured output for REVIEWER_DECISION");
  }
  return parsed;
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
    case "turn/completed":
      return {
        method: notification.method,
        threadId: notification.params.threadId,
        turnId: notification.params.turn.id,
        status: notification.params.turn.status,
        itemTypes: notification.params.turn.items.map((item) => item.type),
      };
    case "turn/started":
      return { method: notification.method, params: notification.params };
    default:
      return { method: notification.method };
  }
}

function summarizeServerRequest(request: ServerRequest): unknown {
  return { method: request.method, id: request.id };
}

function formatTurnFailure(turn: Turn): string {
  return `turn failed: ${turn.id}${turn.error ? ` ${JSON.stringify(turn.error)}` : ""}`;
}

async function writeJson(filePath: string, value: unknown): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function writeReceipt(
  filePath: string,
  report: {
    readonly result: string;
    readonly job_id: string;
    readonly reviewer_cwd: string;
    readonly worker_job_id: string;
    readonly artifacts: { readonly events: string; readonly report: string };
    readonly boundary_flags: typeof boundaryFlags;
  },
): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const lines = [
    "# CEA-017 Snapshot-Bound Reviewer Pilot Receipt",
    "",
    `result: ${report.result}`,
    `job_id: ${report.job_id}`,
    `worker_job_id: ${report.worker_job_id}`,
    "",
    "## Boundary",
    `- reviewer_cwd: ${report.reviewer_cwd}`,
    `- app_server_process_cwd_snapshot: ${report.boundary_flags.app_server_process_cwd_snapshot}`,
    `- reviewer_thread_cwd_snapshot: ${report.boundary_flags.reviewer_thread_cwd_snapshot}`,
    `- reviewer_turn_cwd_snapshot: ${report.boundary_flags.reviewer_turn_cwd_snapshot}`,
    `- sandbox_read_only_network_off: ${report.boundary_flags.sandbox_read_only_network_off}`,
    `- direct_real_repo: ${report.boundary_flags.direct_real_repo}`,
    `- managed_worker_evidence_used: ${report.boundary_flags.managed_worker_evidence_used}`,
    "",
    "## Artifacts",
    `- events: ${report.artifacts.events}`,
    `- report: ${report.artifacts.report}`,
    "",
  ];
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, lines.join("\n"), "utf8");
}

void main();
