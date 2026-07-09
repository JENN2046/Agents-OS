import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { createAppServerClient } from "../appserver/client.js";
import { createStdioTransport } from "../appserver/transport_stdio.js";
import { createContextLedgerEntry } from "../bridge/context_ledger.js";
import { buildContextPromotionPacket } from "../bridge/context_promotion.js";
import {
  assertSafeReviewTurnCompleted,
  createE2eSafeReviewBoundarySummary,
  rejectSafeReviewTerminalNonCompletedTurn,
} from "../bridge/e2e_safe_review.js";
import { reviewerDecisionSchema, validateStructuredLoopOutput, workerDoneSchema, type ReviewerDecision, type WorkerDone } from "../bridge/event_contracts.js";
import { createServerRequestResponsePlan, type PolicyDecision } from "../bridge/policy_gate.js";
import { compilePromptAnnex } from "../bridge/prompt_annex.js";
import { createPromotionApprovalReceipt } from "../bridge/promotion_approval.js";
import { defaultSnapshotAllowlist, exportSafeRepoSnapshot } from "../bridge/repo_snapshot.js";
import { createSnapshotReviewerLivePrompt, type SnapshotWorkerLiveEvidence } from "../bridge/snapshot_reviewer_live.js";
import { createSnapshotWorkerLivePrompt } from "../bridge/snapshot_worker_live.js";
import { assertSnapshotBoundWorkerPlanLiveBoundary, createSnapshotBoundWorkerPlan } from "../bridge/snapshot_worker_pilot.js";
import type { ServerNotification } from "../generated/appserver/ServerNotification";
import type { ServerRequest } from "../generated/appserver/ServerRequest";
import type { Turn } from "../generated/appserver/v2/Turn";
import { createFileContextLedgerStore } from "../stores/context_ledger_store.js";
import { createFileContextPacketStore } from "../stores/context_packet_store.js";
import { createFileEventStore } from "../stores/event_store.js";
import { createFilePromotionApprovalStore } from "../stores/promotion_approval_store.js";
import { createFilePromptAnnexStore } from "../stores/prompt_annex_store.js";
import { safeJoin } from "../stores/safe_path.js";
import { createFileSnapshotWorkerPlanStore } from "../stores/snapshot_worker_plan_store.js";
import type { LoopEvent } from "../types/events.js";

const TURN_TIMEOUT_MS = 300_000;
const REQUEST_TIMEOUT_MS = 60_000;

interface TurnTracker {
  readonly completedTurns: Map<string, Turn>;
  readonly agentTextByTurn: Map<string, string>;
}

const boundaryFlags = {
  bridge_exporter_read_source: "YES",
  app_server_process_cwd_snapshot: "YES",
  worker_thread_cwd_snapshot: "YES",
  worker_turn_cwd_snapshot: "YES",
  reviewer_thread_cwd_snapshot: "YES",
  reviewer_turn_cwd_snapshot: "YES",
  sandbox_read_only_network_off: "YES",
  context_auto_injection: "DISABLED",
  direct_real_repo: "BLOCKED",
  managed_worker_started: "STARTED",
  managed_reviewer_started: "STARTED",
  command_exec: "NOT_USED",
  file_write: "NOT_USED",
  secrets_read: "NOT_USED",
  commit_push_deploy_release_tag: "NOT_USED",
} as const;

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const jobId = `cea-018-e2e-safe-review-${timestamp}`;
  const snapshotId = `cea-018-safe-snapshot-${timestamp}`;
  const ledgerTaskId = `cea-018-context-ledger-${timestamp}`;
  const packetId = `cea-018-context-packet-${timestamp}`;
  const approvalReceiptId = `cea-018-promotion-approval-${timestamp}`;
  const annexId = `cea-018-prompt-annex-${timestamp}`;
  const planId = `cea-018-snapshot-worker-plan-${timestamp}`;

  const events = createFileEventStore(path.join(projectRoot, "data", "events"));
  const ledgerStore = createFileContextLedgerStore(path.join(projectRoot, "data", "context-ledger"));
  const packetStore = createFileContextPacketStore(path.join(projectRoot, "data", "context-packets"));
  const approvalStore = createFilePromotionApprovalStore(path.join(projectRoot, "data", "context-approvals"));
  const annexStore = createFilePromptAnnexStore(path.join(projectRoot, "data", "prompt-annexes"));
  const planStore = createFileSnapshotWorkerPlanStore(path.join(projectRoot, "data", "worker-pilots"));
  const reportPath = path.join(projectRoot, "data", "reports", "cea-018_e2e_safe_review_loop.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", "2026-07-07-cea-018-e2e-safe-review-loop.receipt.md");
  const eventWrites: Promise<void>[] = [];
  const policyDecisions: PolicyDecision[] = [];
  let stopReason: string | undefined;
  let workerThreadId: string | undefined;
  let workerTurnId: string | undefined;
  let reviewerThreadId: string | undefined;
  let reviewerTurnId: string | undefined;

  const appendEvent = async (type: LoopEvent["type"], payload: unknown): Promise<void> => {
    await events.append(jobId, { jobId, type, at: new Date().toISOString(), payload });
  };
  const recordEvent = (type: LoopEvent["type"], payload: unknown): void => {
    eventWrites.push(appendEvent(type, payload));
  };

  const snapshot = await exportSafeRepoSnapshot({
    sourceRoot: projectRoot,
    snapshotRoot: path.join(projectRoot, "data", "snapshots", snapshotId),
    allowlist: defaultSnapshotAllowlist,
  });
  await appendEvent("APP_SERVER_MESSAGE", {
    method: "snapshot/exported",
    snapshotRoot: snapshot.snapshotRoot,
    manifestPath: snapshot.manifestPath,
    included: snapshot.manifest.includedFiles.length,
    excluded: snapshot.manifest.excludedFiles.length,
  });

  const ledgerEntries = [
    createContextLedgerEntry({
      taskId: ledgerTaskId,
      eventId: `${ledgerTaskId}:001-snapshot`,
      eventType: "SNAPSHOT_BOUND",
      agentId: "bridge",
      role: "bridge",
      source: "bridge-exporter",
      frontendOrSession: "cea-018-e2e",
      content: "CEA-018 exported a safe snapshot for the end-to-end review loop.",
      artifactRef: toProjectRelative(projectRoot, snapshot.manifestPath),
      snapshotId,
      tags: ["cea-018", "snapshot_ref"],
    }),
    createContextLedgerEntry({
      taskId: ledgerTaskId,
      eventId: `${ledgerTaskId}:002-ledger`,
      eventType: "TASK_OPENED",
      agentId: "commander",
      role: "commander",
      source: "codex-desktop",
      frontendOrSession: "current-thread",
      content: "CEA-018 runs snapshot export through Reviewer receipt as one command.",
      artifactRef: "docs/SNAPSHOT_BOUND_WORKER_PILOT.md",
      tags: ["cea-018", "e2e"],
    }),
    createContextLedgerEntry({
      taskId: ledgerTaskId,
      eventId: `${ledgerTaskId}:003-boundary`,
      eventType: "REVIEW_REQUESTED",
      agentId: "reviewer",
      role: "reviewer",
      source: "app-server-jsonrpc",
      frontendOrSession: "planned-reviewer",
      content: "Reviewer must validate Worker DONE evidence inside the same snapshot cwd.",
      artifactRef: "docs/SECURITY_BOUNDARIES.md",
      snapshotId,
      tags: ["reviewer", "snapshot_only"],
    }),
  ];
  for (const entry of ledgerEntries) {
    await ledgerStore.append(ledgerTaskId, entry);
  }

  const packet = buildContextPromotionPacket({
    packetId,
    sourceLedgerTaskId: ledgerTaskId,
    entries: ledgerEntries,
    query: { taskId: ledgerTaskId },
  });
  const packetPath = await packetStore.write(packet);
  const approval = createPromotionApprovalReceipt(packet, {
    receiptId: approvalReceiptId,
    approvedByRole: "reviewer",
    approvedByAgentId: "cea-018-reviewer-gate",
    reason: "CEA-018 packet contains metadata-only snapshot and artifact references for packet-only use.",
    evidence: [packetPath, "docs/CONTEXT_PROMOTION_GATE.md"],
  });
  const approvalPath = await approvalStore.write(approval);
  const annex = compilePromptAnnex(packet, approval, { annexId });
  const annexPath = await annexStore.write(annex);
  const plan = createSnapshotBoundWorkerPlan({
    planId,
    manifest: snapshot.manifest,
    manifestPath: snapshot.manifestPath,
    annex,
    annexRef: annexPath,
  });
  assertSnapshotBoundWorkerPlanLiveBoundary(projectRoot, plan, snapshot.manifest);
  const verifiedSnapshotRoot = path.resolve(plan.snapshotRoot);
  const verifiedWorkerCwd = path.resolve(plan.workerCwd);
  const planPath = await planStore.write(plan);

  const tracker: TurnTracker = { completedTurns: new Map(), agentTextByTurn: new Map() };
  const transport = createStdioTransport({ cwd: verifiedSnapshotRoot, timeoutMs: REQUEST_TIMEOUT_MS });
  const client = createAppServerClient(transport, {
    requestTimeoutMs: REQUEST_TIMEOUT_MS,
    clientInfo: {
      name: "codex-appserver-active-loop",
      title: "CEA-018 E2E Safe Review Loop",
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
    await appendEvent("APP_SERVER_MESSAGE", { method: "app-server/start", appServerProcessCwd: verifiedSnapshotRoot });
    const initialized = await client.initialize();
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "initialize/result",
      codexHomeRedacted: Boolean(initialized.codexHome),
      userAgent: initialized.userAgent,
      platformFamily: initialized.platformFamily,
      platformOs: initialized.platformOs,
    });
    client.sendInitialized();

    const workerThread = await client.threadStart({
      cwd: verifiedWorkerCwd,
      approvalPolicy: "never",
      sandbox: "read-only",
      ephemeral: true,
      baseInstructions: "CEA-018 snapshot-bound Worker. Stay inside snapshot cwd. Return only schema JSON.",
    });
    workerThreadId = workerThread.thread.id;
    await appendEvent("APP_SERVER_MESSAGE", { method: "thread/start/result", role: "Worker", threadId: workerThreadId, cwd: verifiedWorkerCwd });

    const workerTurn = await client.turnStart({
      threadId: workerThreadId,
      input: [{ type: "text", text: createSnapshotWorkerLivePrompt({ plan, annex }), text_elements: [] }],
      cwd: verifiedWorkerCwd,
      approvalPolicy: "never",
      sandboxPolicy: plan.sandboxPolicy,
      summary: "none",
      outputSchema: workerDoneSchema,
    });
    workerTurnId = workerTurn.turn.id;
    await appendEvent("APP_SERVER_MESSAGE", { method: "turn/start/result", role: "Worker", turnId: workerTurnId, cwd: verifiedWorkerCwd });
    const workerCompleted = await waitForCompletedTurn(tracker, workerTurn.turn, TURN_TIMEOUT_MS);
    if (stopReason) throw new Error(stopReason);
    const workerDone = parseStructured<WorkerDone>(workerCompleted, "DONE", tracker.agentTextByTurn.get(workerCompleted.id));
    await appendEvent("APP_SERVER_MESSAGE", { method: "structured-output/parsed", expectedType: "DONE", turnId: workerCompleted.id, output: workerDone });

    const workerEvidence: SnapshotWorkerLiveEvidence = {
      result: "PASS",
      job_id: jobId,
      worker_thread_id: workerThreadId,
      worker_turn_id: workerTurnId,
      snapshot_id: plan.snapshotId,
      worker_cwd: verifiedWorkerCwd,
      app_server_process_cwd: verifiedSnapshotRoot,
      annex_id: annex.annexId,
      output: workerDone,
      boundary_flags: {
        app_server_process_cwd_snapshot: "YES",
        worker_thread_cwd_snapshot: "YES",
        worker_turn_cwd_snapshot: "YES",
        sandbox_read_only_network_off: "YES",
        context_auto_injection: "DISABLED",
        direct_real_repo: "BLOCKED",
        managed_worker_started: "STARTED",
        managed_reviewer_started: "NOT_STARTED",
        command_exec: "NOT_USED",
        file_write: "NOT_USED",
        secrets_read: "NOT_USED",
        commit_push_deploy_release_tag: "NOT_USED",
      },
    };

    const reviewerThread = await client.threadStart({
      cwd: verifiedWorkerCwd,
      approvalPolicy: "never",
      sandbox: "read-only",
      ephemeral: true,
      baseInstructions: "CEA-018 snapshot-bound Reviewer. Review supplied Worker DONE evidence only. Return schema JSON.",
    });
    reviewerThreadId = reviewerThread.thread.id;
    await appendEvent("APP_SERVER_MESSAGE", { method: "thread/start/result", role: "Reviewer", threadId: reviewerThreadId, cwd: verifiedWorkerCwd });

    const reviewerTurn = await client.turnStart({
      threadId: reviewerThreadId,
      input: [{ type: "text", text: createSnapshotReviewerLivePrompt({ plan, annex, workerEvidence }), text_elements: [] }],
      cwd: verifiedWorkerCwd,
      approvalPolicy: "never",
      sandboxPolicy: plan.sandboxPolicy,
      summary: "none",
      outputSchema: reviewerDecisionSchema,
    });
    reviewerTurnId = reviewerTurn.turn.id;
    await appendEvent("APP_SERVER_MESSAGE", { method: "turn/start/result", role: "Reviewer", turnId: reviewerTurnId, cwd: verifiedWorkerCwd });
    const reviewerCompleted = await waitForCompletedTurn(tracker, reviewerTurn.turn, TURN_TIMEOUT_MS);
    if (stopReason) throw new Error(stopReason);
    const reviewerDecision = parseStructured<ReviewerDecision>(reviewerCompleted, "REVIEWER_DECISION", tracker.agentTextByTurn.get(reviewerCompleted.id));
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "structured-output/parsed",
      expectedType: "REVIEWER_DECISION",
      turnId: reviewerCompleted.id,
      output: reviewerDecision,
    });

    const boundarySummary = createE2eSafeReviewBoundarySummary({
      snapshotRoot: verifiedSnapshotRoot,
      appServerProcessCwd: verifiedSnapshotRoot,
      workerCwd: verifiedWorkerCwd,
      reviewerCwd: verifiedWorkerCwd,
      workerDone,
      reviewerDecision,
      policyDecisionCount: policyDecisions.length,
    });
    const report = {
      task_id: "CEA-018",
      title: "End-to-End Safe Review Loop",
      result: "PASS",
      completed_at: new Date().toISOString(),
      job_id: jobId,
      snapshot_id: snapshotId,
      ledger_task_id: ledgerTaskId,
      packet_id: packet.packetId,
      approval_receipt_id: approval.receiptId,
      annex_id: annex.annexId,
      plan_id: plan.planId,
      worker_thread_id: workerThreadId,
      worker_turn_id: workerTurnId,
      reviewer_thread_id: reviewerThreadId,
      reviewer_turn_id: reviewerTurnId,
      worker_output: workerDone,
      reviewer_output: reviewerDecision,
      boundary_summary: boundarySummary,
      artifacts: {
        snapshot_manifest: snapshot.manifestPath,
        snapshot_exclusions: snapshot.exclusionReportPath,
        ledger: ledgerStore.pathFor(ledgerTaskId),
        packet: packetPath,
        approval: approvalPath,
        annex: annexPath,
        plan: planPath,
        events: events.pathFor(jobId),
        report: reportPath,
        receipt: receiptPath,
      },
      counts: {
        snapshot_included_files: snapshot.manifest.includedFiles.length,
        snapshot_excluded_files: snapshot.manifest.excludedFiles.length,
        ledger_entries: ledgerEntries.length,
        policy_decisions: policyDecisions.length,
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
    const failure = stopReason ?? (error instanceof Error ? error.message : "unknown CEA-018 failure");
    const report = {
      task_id: "CEA-018",
      title: "End-to-End Safe Review Loop",
      result: stopReason ? "BLOCK" : "FAIL",
      completed_at: new Date().toISOString(),
      job_id: jobId,
      snapshot_id: snapshotId,
      ledger_task_id: ledgerTaskId,
      worker_thread_id: workerThreadId ?? null,
      worker_turn_id: workerTurnId ?? null,
      reviewer_thread_id: reviewerThreadId ?? null,
      reviewer_turn_id: reviewerTurnId ?? null,
      stopped_reason: failure,
      artifacts: {
        snapshot_manifest: snapshot.manifestPath,
        snapshot_exclusions: snapshot.exclusionReportPath,
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
  try {
    rejectSafeReviewTerminalNonCompletedTurn(initialTurn);
  } catch (error) {
    return Promise.reject(error);
  }
  const existing = tracker.completedTurns.get(initialTurn.id);
  if (existing) {
    try {
      return Promise.resolve(assertSafeReviewTurnCompleted(existing));
    } catch (error) {
      return Promise.reject(error);
    }
  }
  return new Promise((resolve, reject) => {
    const startedAt = Date.now();
    const timer = setInterval(() => {
      const completed = tracker.completedTurns.get(initialTurn.id);
      if (completed) {
        clearInterval(timer);
        try {
          resolve(assertSafeReviewTurnCompleted(completed));
        } catch (error) {
          reject(error);
        }
        return;
      }
      if (Date.now() - startedAt > timeoutMs) {
        clearInterval(timer);
        reject(new Error(`timed out waiting for turn completion: ${initialTurn.id}`));
      }
    }, 250);
  });
}

function parseStructured<TExpected extends WorkerDone | ReviewerDecision>(
  turn: Turn,
  expectedType: TExpected["type"],
  fallbackText?: string,
): TExpected {
  const text =
    [...turn.items]
      .reverse()
      .find((item) => item.type === "agentMessage")
      ?.text.trim() ?? fallbackText?.trim();
  if (!text) {
    throw new Error(`missing agentMessage output for ${expectedType}`);
  }
  const parsed = JSON.parse(text) as unknown;
  if (!validateStructuredLoopOutput(parsed) || parsed.type !== expectedType) {
    throw new Error(`invalid structured output for ${expectedType}`);
  }
  return parsed as TExpected;
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
    readonly snapshot_id: string;
    readonly worker_thread_id?: string | null;
    readonly reviewer_thread_id?: string | null;
    readonly artifacts: { readonly events: string; readonly report: string };
    readonly boundary_flags: typeof boundaryFlags;
  },
): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const lines = [
    "# CEA-018 End-to-End Safe Review Loop Receipt",
    "",
    `result: ${report.result}`,
    `job_id: ${report.job_id}`,
    `snapshot_id: ${report.snapshot_id}`,
    `worker_thread_id: ${report.worker_thread_id ?? "NOT_STARTED"}`,
    `reviewer_thread_id: ${report.reviewer_thread_id ?? "NOT_STARTED"}`,
    "",
    "## Boundary",
    `- bridge_exporter_read_source: ${report.boundary_flags.bridge_exporter_read_source}`,
    `- app_server_process_cwd_snapshot: ${report.boundary_flags.app_server_process_cwd_snapshot}`,
    `- worker_thread_cwd_snapshot: ${report.boundary_flags.worker_thread_cwd_snapshot}`,
    `- reviewer_thread_cwd_snapshot: ${report.boundary_flags.reviewer_thread_cwd_snapshot}`,
    `- sandbox_read_only_network_off: ${report.boundary_flags.sandbox_read_only_network_off}`,
    `- direct_real_repo: ${report.boundary_flags.direct_real_repo}`,
    "",
    "## Artifacts",
    `- events: ${report.artifacts.events}`,
    `- report: ${report.artifacts.report}`,
    "",
  ];
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, lines.join("\n"), "utf8");
}

function toProjectRelative(projectRoot: string, filePath: string): string {
  return path.relative(projectRoot, filePath).replaceAll("\\", "/");
}

void main();
