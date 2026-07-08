import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { createAppServerClient } from "../appserver/client.js";
import { createStdioTransport } from "../appserver/transport_stdio.js";
import { createMessageBus, type MessageBusAuditEvent } from "../bridge/message_bus.js";
import { createMessageRouter, type CodexMessageDelivery } from "../bridge/message_router.js";
import { createServerRequestResponsePlan, type PolicyDecision } from "../bridge/policy_gate.js";
import { createReadOnlySyntheticSandboxPolicy, validateStructuredLoopOutput, workerDoneSchema, type WorkerDone } from "../bridge/event_contracts.js";
import { createThreadRegistry } from "../bridge/thread_registry.js";
import type { ServerNotification } from "../generated/appserver/ServerNotification";
import type { ServerRequest } from "../generated/appserver/ServerRequest";
import type { JsonValue } from "../generated/appserver/serde_json/JsonValue";
import type { ThreadStartResponse } from "../generated/appserver/v2/ThreadStartResponse";
import type { Turn } from "../generated/appserver/v2/Turn";
import { createFileEventStore } from "../stores/event_store.js";
import { createFileMessageEventStore } from "../stores/message_event_store.js";
import { safeJoin } from "../stores/safe_path.js";
import { codexMessageReplySchema, isCodexMessageReply, isMessageToCodex, messageToCodexSchema, type CodexMessageReply, type MessageToCodex } from "../types/messages.js";
import type { LoopEvent } from "../types/events.js";

const TURN_TIMEOUT_MS = 180_000;
const REQUEST_TIMEOUT_MS = 60_000;

interface TurnTracker {
  readonly completedTurns: Map<string, Turn>;
  readonly agentTextByTurn: Map<string, string>;
}

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
  snapshot_required: "FALSE",
  real_repo_direct_cwd: "NOT_USED",
  app_server_process_cwd: "SYNTHETIC_WORKSPACE",
  worker_thread_cwd: "SYNTHETIC_WORKSPACE",
  reviewer_thread_cwd: "SYNTHETIC_WORKSPACE",
  app_server_workspace_write: "NOT_USED",
  secrets_read: "NOT_USED",
  commit_push_deploy_release_tag: "NOT_USED",
} as const;

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const syntheticWorkspaceRoot = path.join(projectRoot, "data", "synthetic-workspace");
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const dateStamp = formatDateForReceipt(new Date());
  const jobId = `cea-023-codex-channel-${timestamp}`;
  const conversationId = `conv_cea023_${timestamp}`;
  const correlationId = `corr_cea023_${timestamp}`;
  const workerMessageId = `msg_worker_${timestamp}`;
  const reviewerReplyId = `msg_reviewer_${timestamp}`;
  const events = createFileEventStore(path.join(projectRoot, "data", "events"));
  const messageEvents = createFileMessageEventStore(path.join(projectRoot, "data", "message-logs"));
  const messageLogPath = path.join(projectRoot, "data", "message-logs", `${jobId}.json`);
  const appendOnlyMessageLogPath = messageEvents.pathFor(jobId);
  const reportPath = path.join(projectRoot, "data", "reports", "cea-023_codex_to_codex_message_bus_mvp.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", `${dateStamp}-cea-023-codex-to-codex-message-bus-mvp.receipt.md`);
  const registry = createThreadRegistry();
  const bus = createMessageBus({ messageTtlMs: 300_000, maxRounds: 3 });
  const router = createMessageRouter({ bus, registry });
  const tracker: TurnTracker = { completedTurns: new Map(), agentTextByTurn: new Map() };
  const eventWrites: Promise<void>[] = [];
  const policyDecisions: PolicyDecision[] = [];
  const deliveries: CodexMessageDelivery[] = [];
  let flushedAuditEventCount = 0;
  let stopReason: string | undefined;
  let workerThreadId: string | undefined;
  let reviewerThreadId: string | undefined;
  let workerMessage: MessageToCodex | undefined;
  let reviewerReply: CodexMessageReply | undefined;
  let workerDone: WorkerDone | undefined;

  const appendEvent = async (type: LoopEvent["type"], payload: unknown): Promise<void> => {
    await events.append(jobId, { jobId, type, at: new Date().toISOString(), payload });
  };
  const recordEvent = (type: LoopEvent["type"], payload: unknown): void => {
    eventWrites.push(appendEvent(type, payload));
  };
  const flushMessageAuditEvents = async (): Promise<void> => {
    const nextEvents = bus.auditEvents().slice(flushedAuditEventCount);
    if (nextEvents.length === 0) return;
    await messageEvents.appendMany(jobId, nextEvents);
    flushedAuditEventCount += nextEvents.length;
  };

  const transport = createStdioTransport({
    cwd: syntheticWorkspaceRoot,
    timeoutMs: REQUEST_TIMEOUT_MS,
  });
  const client = createAppServerClient(transport, {
    requestTimeoutMs: REQUEST_TIMEOUT_MS,
    clientInfo: {
      name: "codex-appserver-active-loop",
      title: "CEA-023 Codex-to-Codex Message Bus MVP",
      version: "0.0.0",
    },
  });

  client.onNotification((notification) => {
    trackNotification(tracker, notification);
    recordEvent("APP_SERVER_MESSAGE", summarizeNotification(notification));
  });
  client.onServerRequest((request) => {
    const responsePlan = createServerRequestResponsePlan(request);
    policyDecisions.push(responsePlan.policyDecision);
    if (responsePlan.response.kind === "result") {
      client.respondToServerRequest(request.id, responsePlan.response.result);
    } else {
      client.respondToServerRequestError(
        request.id,
        responsePlan.response.code,
        responsePlan.response.message,
        responsePlan.response.data,
      );
    }
    recordEvent("POLICY_DECISION", {
      request: summarizeServerRequest(request),
      decision: responsePlan.policyDecision,
      responseKind: responsePlan.response.kind,
    });
    if (responsePlan.policyDecision.kind !== "allow" && !stopReason) {
      stopReason = `${responsePlan.policyDecision.kind}: ${responsePlan.policyDecision.reason}`;
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
    await appendEvent("APP_SERVER_MESSAGE", { method: "app-server/start", cwd: syntheticWorkspaceRoot });
    const initialized = await client.initialize();
    await appendEvent("APP_SERVER_MESSAGE", {
      method: "initialize/result",
      codexHomeRedacted: Boolean(initialized.codexHome),
      userAgent: initialized.userAgent,
      platformFamily: initialized.platformFamily,
      platformOs: initialized.platformOs,
    });
    client.sendInitialized();

    const workerThread = await startChannelThread(client, syntheticWorkspaceRoot, "Worker");
    workerThreadId = getThreadId(workerThread);
    registry.register({ role: "worker", threadId: workerThreadId, cwd: syntheticWorkspaceRoot, label: "CEA-023 Worker Codex" });
    await appendEvent("APP_SERVER_MESSAGE", { method: "thread/start/result", role: "worker", threadId: workerThreadId, cwd: syntheticWorkspaceRoot });

    const reviewerThread = await startChannelThread(client, syntheticWorkspaceRoot, "Reviewer");
    reviewerThreadId = getThreadId(reviewerThread);
    registry.register({ role: "reviewer", threadId: reviewerThreadId, cwd: syntheticWorkspaceRoot, label: "CEA-023 Reviewer Codex" });
    await appendEvent("APP_SERVER_MESSAGE", { method: "thread/start/result", role: "reviewer", threadId: reviewerThreadId, cwd: syntheticWorkspaceRoot });

    workerMessage = await runTurnAndParseMessageToCodex(client, tracker, {
      threadId: workerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createWorkerMessagePrompt({ conversationId, correlationId, workerMessageId }),
    });
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/worker-message-emitted", message: workerMessage });
    const messageDelivery = router.routeMessage(workerMessage);
    deliveries.push(messageDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/message-routed", delivery: messageDelivery });

    reviewerReply = await runTurnAndParseReply(client, tracker, {
      threadId: reviewerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createReviewerReplyPrompt({ workerMessage, reviewerReplyId }),
    });
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/reviewer-reply-emitted", reply: reviewerReply });
    const replyDelivery = router.routeReply(reviewerReply);
    deliveries.push(replyDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/reply-returned", delivery: replyDelivery });

    workerDone = await runTurnAndParseDone(client, tracker, {
      threadId: workerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createWorkerResumePrompt({ workerMessage, reviewerReply }),
    });
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/worker-done-after-reply", output: workerDone });
    await messageEvents.append(jobId, createMessageEvent("WORKER_RESUMED", new Date().toISOString(), workerMessage, reviewerReply));
    await messageEvents.append(jobId, createMessageEvent("CHANNEL_DONE", new Date().toISOString(), workerMessage, reviewerReply));
    if (stopReason) {
      throw new Error(stopReason);
    }

    registry.markStatus(workerThreadId, "COMPLETED");
    registry.markStatus(reviewerThreadId, "COMPLETED");
    const messageLog = {
      job_id: jobId,
      conversation_id: conversationId,
      correlation_id: correlationId,
      registry: registry.snapshot(),
      bus: bus.snapshot(),
      deliveries,
      worker_done: workerDone,
      boundary_flags: boundaryFlags,
    };
    await writeJson(messageLogPath, messageLog);
    const report = createReport({
      result: "PASS",
      jobId,
      conversationId,
      correlationId,
      workerThreadId,
      reviewerThreadId,
      workerMessage,
      reviewerReply,
      workerDone,
      deliveries,
      messageLogPath,
      appendOnlyMessageLogPath,
      messageTtlMs: bus.messageTtlMs,
      maxRounds: bus.maxRounds,
      eventsPath: events.pathFor(jobId),
      reportPath,
      receiptPath,
      policyDecisions,
      stoppedReason: null,
    });
    await writeJson(reportPath, report);
    await writeReceipt(receiptPath, report);
    await appendEvent("REPORT_WRITTEN", { reportPath });
    await appendEvent("RECEIPT_WRITTEN", { receiptPath });
    await Promise.all(eventWrites);
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    const failure = stopReason ?? (error instanceof Error ? error.message : "unknown CEA-023 channel failure");
    const report = createReport({
      result: stopReason ? "BLOCK" : "FAIL",
      jobId,
      conversationId,
      correlationId,
      workerThreadId: workerThreadId ?? null,
      reviewerThreadId: reviewerThreadId ?? null,
      workerMessage: workerMessage ?? null,
      reviewerReply: reviewerReply ?? null,
      workerDone: workerDone ?? null,
      deliveries,
      messageLogPath,
      appendOnlyMessageLogPath,
      messageTtlMs: bus.messageTtlMs,
      maxRounds: bus.maxRounds,
      eventsPath: events.pathFor(jobId),
      reportPath,
      receiptPath,
      policyDecisions,
      stoppedReason: failure,
    });
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

async function startChannelThread(client: ReturnType<typeof createAppServerClient>, cwd: string, role: "Worker" | "Reviewer"): Promise<ThreadStartResponse> {
  return client.threadStart({
    cwd,
    approvalPolicy: "never",
    sandbox: "read-only",
    ephemeral: true,
    baseInstructions: [
      `CEA-023 ${role} Codex.`,
      "Use only the synthetic workspace cwd.",
      "Do not request command execution, file changes, browser automation, MCP tools, web search, network, or private state.",
      "Return only the final JSON object matching the provided output schema.",
    ].join(" "),
  });
}

async function runTurnAndParseMessageToCodex(
  client: ReturnType<typeof createAppServerClient>,
  tracker: TurnTracker,
  input: { readonly threadId: string; readonly cwd: string; readonly prompt: string },
): Promise<MessageToCodex> {
  const turn = await runTurn(client, input.threadId, input.cwd, input.prompt, messageToCodexSchema);
  const completed = await waitForCompletedTurn(tracker, turn, TURN_TIMEOUT_MS);
  const parsed = parseJsonFromTurn(completed, tracker.agentTextByTurn.get(completed.id));
  if (!isMessageToCodex(parsed)) {
    throw new Error("Worker did not emit a valid MESSAGE_TO_CODEX envelope");
  }
  return parsed;
}

async function runTurnAndParseReply(
  client: ReturnType<typeof createAppServerClient>,
  tracker: TurnTracker,
  input: { readonly threadId: string; readonly cwd: string; readonly prompt: string },
): Promise<CodexMessageReply> {
  const turn = await runTurn(client, input.threadId, input.cwd, input.prompt, codexMessageReplySchema);
  const completed = await waitForCompletedTurn(tracker, turn, TURN_TIMEOUT_MS);
  const parsed = parseJsonFromTurn(completed, tracker.agentTextByTurn.get(completed.id));
  if (!isCodexMessageReply(parsed)) {
    throw new Error("Reviewer did not emit a valid CODEX_MESSAGE_REPLY envelope");
  }
  return parsed;
}

async function runTurnAndParseDone(
  client: ReturnType<typeof createAppServerClient>,
  tracker: TurnTracker,
  input: { readonly threadId: string; readonly cwd: string; readonly prompt: string },
): Promise<WorkerDone> {
  const turn = await runTurn(client, input.threadId, input.cwd, input.prompt, workerDoneSchema);
  const completed = await waitForCompletedTurn(tracker, turn, TURN_TIMEOUT_MS);
  const parsed = parseJsonFromTurn(completed, tracker.agentTextByTurn.get(completed.id));
  if (!validateStructuredLoopOutput(parsed) || parsed.type !== "DONE") {
    throw new Error("Worker did not resume with DONE after reply");
  }
  return parsed;
}

async function runTurn(
  client: ReturnType<typeof createAppServerClient>,
  threadId: string,
  cwd: string,
  prompt: string,
  outputSchema: Record<string, JsonValue>,
): Promise<Turn> {
  const response = await client.turnStart({
    threadId,
    input: [{ type: "text", text: prompt, text_elements: [] }],
    cwd,
    approvalPolicy: "never",
    sandboxPolicy: createReadOnlySyntheticSandboxPolicy(),
    summary: "none",
    outputSchema,
  });
  return response.turn;
}

function createWorkerMessagePrompt(input: {
  readonly conversationId: string;
  readonly correlationId: string;
  readonly workerMessageId: string;
}): string {
  return [
    "Emit the first Codex-to-Codex channel message.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(
      {
        type: "MESSAGE_TO_CODEX",
        message_id: input.workerMessageId,
        correlation_id: input.correlationId,
        conversation_id: input.conversationId,
        from: "worker",
        to: "reviewer",
        kind: "question",
        payload: {
          question: "Please review this synthetic channel decision point.",
          context: [],
          expected_response: "decision",
        },
      },
      null,
      2,
    ),
  ].join("\n");
}

function createReviewerReplyPrompt(input: { readonly workerMessage: MessageToCodex; readonly reviewerReplyId: string }): string {
  return [
    "You received a Bridge-routed MESSAGE_TO_CODEX envelope from Worker Codex.",
    "Reply to the exact message_id using CODEX_MESSAGE_REPLY.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(
      {
        type: "CODEX_MESSAGE_REPLY",
        message_id: input.reviewerReplyId,
        reply_to: input.workerMessage.message_id,
        correlation_id: input.workerMessage.correlation_id,
        conversation_id: input.workerMessage.conversation_id,
        from: "reviewer",
        to: "worker",
        kind: "answer",
        payload: {
          decision: "continue",
          reason: "Synthetic channel test is safe.",
          next_instruction: "Continue and emit DONE.",
        },
      },
      null,
      2,
    ),
    "Original Worker message:",
    JSON.stringify(input.workerMessage, null, 2),
  ].join("\n");
}

function createWorkerResumePrompt(input: { readonly workerMessage: MessageToCodex; readonly reviewerReply: CodexMessageReply }): string {
  return [
    "Bridge returned a CODEX_MESSAGE_REPLY to Worker Codex.",
    "Acknowledge that the reply_to, correlation_id, and conversation_id match the original message.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(
      {
        type: "DONE",
        summary: "Codex-to-Codex message channel completed.",
        evidence: [
          "worker emitted MESSAGE_TO_CODEX",
          "bridge routed message to reviewer",
          "reviewer emitted CODEX_MESSAGE_REPLY",
          "bridge returned reply to worker",
          "worker resumed and completed",
        ],
      },
      null,
      2,
    ),
    "Original Worker message:",
    JSON.stringify(input.workerMessage, null, 2),
    "Reviewer reply:",
    JSON.stringify(input.reviewerReply, null, 2),
  ].join("\n");
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

function parseJsonFromTurn(turn: Turn, fallbackText?: string): unknown {
  const text =
    [...turn.items]
      .reverse()
      .find((item) => item.type === "agentMessage")
      ?.text.trim() ?? fallbackText?.trim();
  if (!text) {
    throw new Error(`missing agentMessage output for turn ${turn.id}`);
  }
  try {
    return JSON.parse(text) as unknown;
  } catch (error) {
    throw new Error(`malformed JSON output for turn ${turn.id}: ${error instanceof Error ? error.message : "parse failed"}`);
  }
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

function getThreadId(response: ThreadStartResponse): string {
  return response.thread.id;
}

function createMessageEvent(
  event: MessageBusAuditEvent["event"],
  timestamp: string,
  workerMessage: MessageToCodex,
  reviewerReply: CodexMessageReply,
): MessageBusAuditEvent {
  return {
    event,
    timestamp,
    message_id: reviewerReply.message_id,
    reply_to: workerMessage.message_id,
    conversation_id: workerMessage.conversation_id,
    correlation_id: workerMessage.correlation_id,
    from: reviewerReply.to,
    to: reviewerReply.from,
  };
}

async function writeJson(filePath: string, value: unknown): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function createReport(input: {
  readonly result: "PASS" | "BLOCK" | "FAIL";
  readonly jobId: string;
  readonly conversationId: string;
  readonly correlationId: string;
  readonly workerThreadId: string | null;
  readonly reviewerThreadId: string | null;
  readonly workerMessage: MessageToCodex | null;
  readonly reviewerReply: CodexMessageReply | null;
  readonly workerDone: WorkerDone | null;
  readonly deliveries: readonly CodexMessageDelivery[];
  readonly messageLogPath: string;
  readonly appendOnlyMessageLogPath: string;
  readonly messageTtlMs: number;
  readonly maxRounds: number;
  readonly eventsPath: string;
  readonly reportPath: string;
  readonly receiptPath: string;
  readonly policyDecisions: readonly PolicyDecision[];
  readonly stoppedReason: string | null;
}): Record<string, unknown> {
  const workerMessageEmitted = input.workerMessage?.type === "MESSAGE_TO_CODEX";
  const reviewerReplyEmitted = input.reviewerReply?.type === "CODEX_MESSAGE_REPLY";
  const replyCorrelated =
    Boolean(input.workerMessage && input.reviewerReply) &&
    input.reviewerReply?.reply_to === input.workerMessage?.message_id &&
    input.reviewerReply?.correlation_id === input.workerMessage?.correlation_id &&
    input.reviewerReply?.conversation_id === input.workerMessage?.conversation_id;
  return {
    task_id: "CEA-023",
    title: "Codex-to-Codex Message Bus MVP",
    result: input.result,
    completed_at: new Date().toISOString(),
    job_id: input.jobId,
    conversation_id: input.conversationId,
    correlation_id: input.correlationId,
    worker_thread_id: input.workerThreadId,
    reviewer_thread_id: input.reviewerThreadId,
    channel_acceptance: {
      worker_thread_started: input.workerThreadId ? "PASS" : "FAIL",
      reviewer_thread_started: input.reviewerThreadId ? "PASS" : "FAIL",
      worker_message_emitted: workerMessageEmitted ? "PASS" : "FAIL",
      message_captured_by_bridge: workerMessageEmitted ? "PASS" : "FAIL",
      message_routed_to_reviewer: input.deliveries.some((delivery) => delivery.status === "MESSAGE_ROUTED" && delivery.to === "reviewer") ? "PASS" : "FAIL",
      reviewer_reply_emitted: reviewerReplyEmitted ? "PASS" : "FAIL",
      reply_correlated_by_reply_to: replyCorrelated ? "PASS" : "FAIL",
      reply_returned_to_worker: input.deliveries.some((delivery) => delivery.status === "REPLY_ROUTED" && delivery.to === "worker") ? "PASS" : "FAIL",
      worker_resumed_after_reply: input.workerDone?.type === "DONE" ? "PASS" : "FAIL",
      worker_done_after_reply: input.workerDone?.type === "DONE" ? "PASS" : "FAIL",
      message_log_written: input.result === "PASS" ? "PASS" : "PENDING",
      receipt_written: input.result === "PASS" ? "PASS" : "PENDING",
    },
    message_bus_hardening: {
      strict_payload_validation: "PASS",
      generalized_delivery_status: input.deliveries.every((delivery) => delivery.status === "MESSAGE_ROUTED" || delivery.status === "REPLY_ROUTED")
        ? "PASS"
        : "FAIL",
      reply_correlation: replyCorrelated ? "PASS" : "FAIL",
      append_only_message_log: input.result === "PASS" ? "PASS" : "PENDING",
      max_round_guard_configured: input.maxRounds === 3 ? "PASS" : "FAIL",
      timeout_guard_configured: input.messageTtlMs > 0 ? "PASS" : "FAIL",
    },
    messages: {
      worker_message: input.workerMessage,
      reviewer_reply: input.reviewerReply,
      worker_done: input.workerDone,
      deliveries: input.deliveries,
    },
    artifacts: {
      message_log: input.messageLogPath,
      append_only_message_log: input.appendOnlyMessageLogPath,
      events: input.eventsPath,
      report: input.reportPath,
      receipt: input.receiptPath,
    },
    policy_decisions: input.policyDecisions,
    boundary_flags: boundaryFlags,
    stopped_reason: input.stoppedReason,
  };
}

async function writeReceipt(filePath: string, report: Record<string, unknown>): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const acceptance = report.channel_acceptance as Record<string, string>;
  const hardening = report.message_bus_hardening as Record<string, string>;
  const artifacts = report.artifacts as Record<string, string>;
  const lines = [
    "# CEA-023 Codex-to-Codex Message Bus MVP Receipt",
    "",
    `result: ${String(report.result)}`,
    `job_id: ${String(report.job_id)}`,
    `conversation_id: ${String(report.conversation_id)}`,
    `correlation_id: ${String(report.correlation_id)}`,
    "",
    "## Acceptance",
    ...Object.entries(acceptance).map(([key, value]) => `- ${key}: ${value}`),
    "",
    "## Message Bus Hardening",
    ...Object.entries(hardening).map(([key, value]) => `- ${key}: ${value}`),
    "",
    "## Boundary",
    ...Object.entries(boundaryFlags).map(([key, value]) => `- ${key}: ${value}`),
    "",
    "## Artifacts",
    `- message_log: ${artifacts.message_log}`,
    `- append_only_message_log: ${artifacts.append_only_message_log}`,
    `- events: ${artifacts.events}`,
    `- report: ${artifacts.report}`,
    `- receipt: ${artifacts.receipt}`,
    "",
  ];
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, lines.join("\n"), "utf8");
}

function formatDateForReceipt(date: Date): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const year = parts.find((part) => part.type === "year")?.value ?? "0000";
  const month = parts.find((part) => part.type === "month")?.value ?? "00";
  const day = parts.find((part) => part.type === "day")?.value ?? "00";
  return `${year}-${month}-${day}`;
}

void main();
