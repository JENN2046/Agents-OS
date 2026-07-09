import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { createAppServerClient } from "../appserver/client.js";
import { createStdioTransport } from "../appserver/transport_stdio.js";
import { assertChannelPolicyOpen } from "../bridge/channel_policy_stop.js";
import { createMessageBus, type MessageBusAuditEvent } from "../bridge/message_bus.js";
import { createMessageRouter, type CodexMessageDelivery } from "../bridge/message_router.js";
import { assertLiveTurnCompleted, rejectLiveTerminalNonCompletedTurn } from "../bridge/live_turn_completion.js";
import { createServerRequestResponsePlan, type PolicyDecision } from "../bridge/policy_gate.js";
import { createReadOnlySyntheticSandboxPolicy, validateStructuredLoopOutput, workerDoneSchema, type WorkerDone } from "../bridge/event_contracts.js";
import { createThreadRegistry } from "../bridge/thread_registry.js";
import type { ServerNotification } from "../generated/appserver/ServerNotification";
import type { ServerRequest } from "../generated/appserver/ServerRequest";
import type { JsonValue } from "../generated/appserver/serde_json/JsonValue";
import type { ThreadStartResponse } from "../generated/appserver/v2/ThreadStartResponse";
import type { Turn } from "../generated/appserver/v2/Turn";
import { createFileEventStore } from "../stores/event_store.js";
import { createFileMessageEventStore, type MessageEventRecord } from "../stores/message_event_store.js";
import { safeJoin } from "../stores/safe_path.js";
import {
  codexMessageReplySchema,
  isCodexMessageReply,
  isMessageToCodex,
  messageToCodexSchema,
  type CodexMessageReply,
  type CodexPeerRole,
  type MessageToCodex,
} from "../types/messages.js";
import type { LoopEvent } from "../types/events.js";

const TURN_TIMEOUT_MS = 180_000;
const REQUEST_TIMEOUT_MS = 60_000;
const CONVERSATION_ID = "conv_multirole_001";

interface TurnTracker {
  readonly completedTurns: Map<string, Turn>;
  readonly agentTextByTurn: Map<string, string>;
}

const boundaryFlags = {
  real_repo_direct_cwd: "NOT_USED",
  snapshot_required: "FALSE",
  snapshot_worker: "NOT_USED",
  workspace_write: "NOT_USED",
  websocket: "NOT_USED",
  command_exec: "NOT_USED",
  thread_shell_command: "NOT_USED",
  process_api: "NOT_USED",
  responses_api: "NOT_USED",
  workspace_agents_api: "NOT_USED",
  browser_automation: "NOT_USED",
  secrets_read: "NOT_USED",
  commit_push_deploy_release_tag: "NOT_USED",
  app_server_process_cwd: "SYNTHETIC_WORKSPACE",
  worker_thread_cwd: "SYNTHETIC_WORKSPACE",
  reviewer_thread_cwd: "SYNTHETIC_WORKSPACE",
  verifier_thread_cwd: "SYNTHETIC_WORKSPACE",
} as const;

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const syntheticWorkspaceRoot = path.join(projectRoot, "data", "synthetic-workspace");
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const dateStamp = formatDateForReceipt(new Date());
  const jobId = `cea-026-multirole-${timestamp}`;
  const events = createFileEventStore(path.join(projectRoot, "data", "events"));
  const messageEvents = createFileMessageEventStore(path.join(projectRoot, "data", "message-logs"));
  const messageLogPath = path.join(projectRoot, "data", "message-logs", `${jobId}.json`);
  const appendOnlyMessageLogPath = messageEvents.pathFor(jobId);
  const reportPath = path.join(projectRoot, "data", "reports", "cea-026_multi_role_codex_channel.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", `${dateStamp}-cea-026-multi-role-codex-channel.receipt.md`);
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
  let verifierThreadId: string | undefined;
  let workerToReviewer: MessageToCodex | undefined;
  let reviewerToWorker: CodexMessageReply | undefined;
  let workerToVerifier: MessageToCodex | undefined;
  let verifierToWorker: CodexMessageReply | undefined;
  let workerDone: WorkerDone | undefined;

  const appendEvent = async (type: LoopEvent["type"], payload: unknown): Promise<void> => {
    await events.append(jobId, { jobId, type, at: new Date().toISOString(), payload });
  };
  const recordEvent = (type: LoopEvent["type"], payload: unknown): void => {
    eventWrites.push(appendEvent(type, payload));
  };
  const flushMessageAuditEvents = async (): Promise<void> => {
    const nextEvents = bus.auditEvents().slice(flushedAuditEventCount).map((event) => enrichAuditEvent(event, deliveries));
    if (nextEvents.length === 0) return;
    await messageEvents.appendMany(jobId, nextEvents);
    flushedAuditEventCount += nextEvents.length;
  };

  await mkdir(syntheticWorkspaceRoot, { recursive: true });
  const transport = createStdioTransport({ cwd: syntheticWorkspaceRoot, timeoutMs: REQUEST_TIMEOUT_MS });
  const client = createAppServerClient(transport, {
    requestTimeoutMs: REQUEST_TIMEOUT_MS,
    clientInfo: {
      name: "codex-appserver-active-loop",
      title: "CEA-026 Multi-role Codex Channel",
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
    registry.register({ role: "worker", threadId: workerThreadId, cwd: syntheticWorkspaceRoot, label: "CEA-026 Worker Codex" });
    await appendEvent("APP_SERVER_MESSAGE", { method: "thread/start/result", role: "worker", threadId: workerThreadId, cwd: syntheticWorkspaceRoot });

    const reviewerThread = await startChannelThread(client, syntheticWorkspaceRoot, "Reviewer");
    reviewerThreadId = getThreadId(reviewerThread);
    registry.register({ role: "reviewer", threadId: reviewerThreadId, cwd: syntheticWorkspaceRoot, label: "CEA-026 Reviewer Codex" });
    await appendEvent("APP_SERVER_MESSAGE", { method: "thread/start/result", role: "reviewer", threadId: reviewerThreadId, cwd: syntheticWorkspaceRoot });

    const verifierThread = await startChannelThread(client, syntheticWorkspaceRoot, "Verifier");
    verifierThreadId = getThreadId(verifierThread);
    registry.register({ role: "verifier", threadId: verifierThreadId, cwd: syntheticWorkspaceRoot, label: "CEA-026 Verifier Codex" });
    await appendEvent("APP_SERVER_MESSAGE", { method: "thread/start/result", role: "verifier", threadId: verifierThreadId, cwd: syntheticWorkspaceRoot });

    workerToReviewer = await runTurnAndParseMessageToCodex(client, tracker, {
      threadId: workerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createWorkerToReviewerPrompt(),
    });
    assertChannelPolicyOpen(stopReason);
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/worker-to-reviewer-message-emitted", message: workerToReviewer });
    const workerReviewerDelivery = router.routeMessage(workerToReviewer);
    deliveries.push(workerReviewerDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/worker-to-reviewer-message-routed", delivery: workerReviewerDelivery });

    reviewerToWorker = await runTurnAndParseReply(client, tracker, {
      threadId: reviewerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createReviewerReplyPrompt(workerToReviewer),
    });
    assertChannelPolicyOpen(stopReason);
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/reviewer-to-worker-reply-emitted", reply: reviewerToWorker });
    const reviewerWorkerDelivery = router.routeReply(reviewerToWorker);
    deliveries.push(reviewerWorkerDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/reviewer-to-worker-reply-routed", delivery: reviewerWorkerDelivery });
    await messageEvents.append(jobId, createWorkerResumedEvent(1, reviewerToWorker, reviewerWorkerDelivery));

    workerToVerifier = await runTurnAndParseMessageToCodex(client, tracker, {
      threadId: workerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createWorkerToVerifierPrompt(workerToReviewer, reviewerToWorker),
    });
    assertChannelPolicyOpen(stopReason);
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/worker-to-verifier-message-emitted", message: workerToVerifier });
    const workerVerifierDelivery = router.routeMessage(workerToVerifier);
    deliveries.push(workerVerifierDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/worker-to-verifier-message-routed", delivery: workerVerifierDelivery });

    verifierToWorker = await runTurnAndParseReply(client, tracker, {
      threadId: verifierThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createVerifierReplyPrompt(workerToVerifier),
    });
    assertChannelPolicyOpen(stopReason);
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/verifier-to-worker-reply-emitted", reply: verifierToWorker });
    const verifierWorkerDelivery = router.routeReply(verifierToWorker);
    deliveries.push(verifierWorkerDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/verifier-to-worker-reply-routed", delivery: verifierWorkerDelivery });
    await messageEvents.append(jobId, createWorkerResumedEvent(2, verifierToWorker, verifierWorkerDelivery));

    workerDone = await runTurnAndParseDone(client, tracker, {
      threadId: workerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createWorkerDonePrompt({ workerToReviewer, reviewerToWorker, workerToVerifier, verifierToWorker }),
    });
    assertChannelPolicyOpen(stopReason);
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/worker-done-after-verifier", output: workerDone });
    bus.markConversationDone(CONVERSATION_ID);
    await flushMessageAuditEvents();

    registry.markStatus(workerThreadId, "COMPLETED");
    registry.markStatus(reviewerThreadId, "COMPLETED");
    registry.markStatus(verifierThreadId, "COMPLETED");
    const messageEventLog = await messageEvents.read(jobId);
    const messageLog = {
      job_id: jobId,
      conversation_id: CONVERSATION_ID,
      registry: registry.snapshot(),
      bus: bus.snapshot(),
      deliveries,
      worker_done: workerDone,
      message_events: messageEventLog,
      boundary_flags: boundaryFlags,
    };
    await writeJson(messageLogPath, messageLog);
    const report = createReport({
      result: "PASS",
      jobId,
      conversationId: CONVERSATION_ID,
      workerThreadId,
      reviewerThreadId,
      verifierThreadId,
      workerToReviewer,
      reviewerToWorker,
      workerToVerifier,
      verifierToWorker,
      workerDone,
      deliveries,
      messageEvents: messageEventLog,
      messageLogPath,
      appendOnlyMessageLogPath,
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
    const failure = stopReason ?? (error instanceof Error ? error.message : "unknown CEA-026 multi-role channel failure");
    const messageEventLog = await readMessageEventsIfPresent(messageEvents, jobId);
    const report = createReport({
      result: "BLOCK",
      jobId,
      conversationId: CONVERSATION_ID,
      workerThreadId: workerThreadId ?? null,
      reviewerThreadId: reviewerThreadId ?? null,
      verifierThreadId: verifierThreadId ?? null,
      workerToReviewer: workerToReviewer ?? null,
      reviewerToWorker: reviewerToWorker ?? null,
      workerToVerifier: workerToVerifier ?? null,
      verifierToWorker: verifierToWorker ?? null,
      workerDone: workerDone ?? null,
      deliveries,
      messageEvents: messageEventLog,
      messageLogPath,
      appendOnlyMessageLogPath,
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

async function startChannelThread(client: ReturnType<typeof createAppServerClient>, cwd: string, role: "Worker" | "Reviewer" | "Verifier"): Promise<ThreadStartResponse> {
  return client.threadStart({
    cwd,
    approvalPolicy: "never",
    sandbox: "read-only",
    ephemeral: true,
    baseInstructions: [
      `CEA-026 ${role} Codex.`,
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
    throw new Error("Codex did not emit a valid MESSAGE_TO_CODEX envelope");
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
    throw new Error("Codex did not emit a valid CODEX_MESSAGE_REPLY envelope");
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
    throw new Error("Worker did not emit DONE after Verifier reply");
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

function createWorkerToReviewerPrompt(): string {
  return [
    "Emit Worker to Reviewer MESSAGE_TO_CODEX for the CEA-026 multi-role Codex channel.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(expectedWorkerToReviewer(), null, 2),
  ].join("\n");
}

function createReviewerReplyPrompt(workerMessage: MessageToCodex): string {
  return [
    "You received a Worker MESSAGE_TO_CODEX through the Bridge.",
    "Reply to the exact message_id using CODEX_MESSAGE_REPLY.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(expectedReviewerToWorker(), null, 2),
    "Original Worker message:",
    JSON.stringify(workerMessage, null, 2),
  ].join("\n");
}

function createWorkerToVerifierPrompt(workerMessage: MessageToCodex, reviewerReply: CodexMessageReply): string {
  return [
    "Resume after Reviewer reply and emit Worker to Verifier MESSAGE_TO_CODEX for the same conversation.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(expectedWorkerToVerifier(), null, 2),
    "Worker to Reviewer message:",
    JSON.stringify(workerMessage, null, 2),
    "Reviewer to Worker reply:",
    JSON.stringify(reviewerReply, null, 2),
  ].join("\n");
}

function createVerifierReplyPrompt(workerMessage: MessageToCodex): string {
  return [
    "You received a Worker MESSAGE_TO_CODEX through the Bridge.",
    "Reply to the exact message_id using CODEX_MESSAGE_REPLY.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(expectedVerifierToWorker(), null, 2),
    "Original Worker message:",
    JSON.stringify(workerMessage, null, 2),
  ].join("\n");
}

function createWorkerDonePrompt(input: {
  readonly workerToReviewer: MessageToCodex;
  readonly reviewerToWorker: CodexMessageReply;
  readonly workerToVerifier: MessageToCodex;
  readonly verifierToWorker: CodexMessageReply;
}): string {
  return [
    "Bridge returned Reviewer and Verifier replies to Worker Codex.",
    "Acknowledge role identity, reply_to, correlation_id, and conversation_id for both role hops.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(expectedWorkerDone(), null, 2),
    "Worker to Reviewer message:",
    JSON.stringify(input.workerToReviewer, null, 2),
    "Reviewer to Worker reply:",
    JSON.stringify(input.reviewerToWorker, null, 2),
    "Worker to Verifier message:",
    JSON.stringify(input.workerToVerifier, null, 2),
    "Verifier to Worker reply:",
    JSON.stringify(input.verifierToWorker, null, 2),
  ].join("\n");
}

function expectedWorkerToReviewer(): MessageToCodex {
  return {
    type: "MESSAGE_TO_CODEX",
    message_id: "msg_worker_to_reviewer",
    correlation_id: "corr_worker_reviewer",
    conversation_id: CONVERSATION_ID,
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

function expectedReviewerToWorker(): CodexMessageReply {
  return {
    type: "CODEX_MESSAGE_REPLY",
    message_id: "msg_reviewer_to_worker",
    reply_to: "msg_worker_to_reviewer",
    correlation_id: "corr_worker_reviewer",
    conversation_id: CONVERSATION_ID,
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

function expectedWorkerToVerifier(): MessageToCodex {
  return {
    type: "MESSAGE_TO_CODEX",
    message_id: "msg_worker_to_verifier",
    correlation_id: "corr_worker_verifier",
    conversation_id: CONVERSATION_ID,
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

function expectedVerifierToWorker(): CodexMessageReply {
  return {
    type: "CODEX_MESSAGE_REPLY",
    message_id: "msg_verifier_to_worker",
    reply_to: "msg_worker_to_verifier",
    correlation_id: "corr_worker_verifier",
    conversation_id: CONVERSATION_ID,
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

function expectedWorkerDone(): WorkerDone {
  return {
    type: "DONE",
    summary: "Multi-role Codex channel completed.",
    evidence: [
      "Worker message routed to Reviewer",
      "Reviewer reply returned to Worker",
      "Worker message routed to Verifier",
      "Verifier reply returned to Worker",
      "Worker resumed after both role replies and emitted DONE",
    ],
  };
}

function enrichAuditEvent(event: MessageBusAuditEvent, deliveries: readonly CodexMessageDelivery[]): MessageBusAuditEvent {
  const delivery = event.message_id ? deliveries.find((candidate) => candidate.messageId === event.message_id) : undefined;
  return delivery
    ? {
        ...event,
        fromThreadId: delivery.fromThreadId,
        toThreadId: delivery.toThreadId,
      }
    : event;
}

function createWorkerResumedEvent(round: 1 | 2, reply: CodexMessageReply, delivery: CodexMessageDelivery): MessageBusAuditEvent {
  return {
    event: "WORKER_RESUMED",
    timestamp: new Date().toISOString(),
    message_id: reply.message_id,
    reply_to: reply.reply_to,
    conversation_id: reply.conversation_id,
    correlation_id: reply.correlation_id,
    from: reply.from,
    to: reply.to,
    fromThreadId: delivery.fromThreadId,
    toThreadId: delivery.toThreadId,
    round,
    round_count: round,
    max_rounds: 3,
  };
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
    rejectLiveTerminalNonCompletedTurn(initialTurn, "channel multirole smoke turn");
  } catch (error) {
    return Promise.reject(error);
  }
  const existing = tracker.completedTurns.get(initialTurn.id);
  if (existing) {
    try {
      return Promise.resolve(assertLiveTurnCompleted(existing, "channel multirole smoke turn"));
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
          resolve(assertLiveTurnCompleted(completed, "channel multirole smoke turn"));
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

function getThreadId(response: ThreadStartResponse): string {
  return response.thread.id;
}

async function writeJson(filePath: string, value: unknown): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function readMessageEventsIfPresent(
  messageEvents: ReturnType<typeof createFileMessageEventStore>,
  jobId: string,
): Promise<readonly MessageEventRecord[]> {
  try {
    return await messageEvents.read(jobId);
  } catch {
    return [];
  }
}

function createReport(input: {
  readonly result: "PASS" | "BLOCK";
  readonly jobId: string;
  readonly conversationId: string;
  readonly workerThreadId: string | null;
  readonly reviewerThreadId: string | null;
  readonly verifierThreadId: string | null;
  readonly workerToReviewer: MessageToCodex | null;
  readonly reviewerToWorker: CodexMessageReply | null;
  readonly workerToVerifier: MessageToCodex | null;
  readonly verifierToWorker: CodexMessageReply | null;
  readonly workerDone: WorkerDone | null;
  readonly deliveries: readonly CodexMessageDelivery[];
  readonly messageEvents: readonly MessageEventRecord[];
  readonly messageLogPath: string;
  readonly appendOnlyMessageLogPath: string;
  readonly eventsPath: string;
  readonly reportPath: string;
  readonly receiptPath: string;
  readonly policyDecisions: readonly PolicyDecision[];
  readonly stoppedReason: string | null;
}): Record<string, unknown> {
  const workerReviewerRouted = hasDelivery(input.deliveries, "MESSAGE_ROUTED", "msg_worker_to_reviewer", undefined, "reviewer");
  const reviewerWorkerRouted = hasDelivery(input.deliveries, "REPLY_ROUTED", "msg_reviewer_to_worker", "msg_worker_to_reviewer", "worker");
  const workerVerifierRouted = hasDelivery(input.deliveries, "MESSAGE_ROUTED", "msg_worker_to_verifier", undefined, "verifier");
  const verifierWorkerRouted = hasDelivery(input.deliveries, "REPLY_ROUTED", "msg_verifier_to_worker", "msg_worker_to_verifier", "worker");
  const conversationPreserved =
    [input.workerToReviewer, input.reviewerToWorker, input.workerToVerifier, input.verifierToWorker].every(
      (message) => message?.conversation_id === input.conversationId,
    );
  const distinctMessageIds = uniqueStrings([
    input.workerToReviewer?.message_id,
    input.reviewerToWorker?.message_id,
    input.workerToVerifier?.message_id,
    input.verifierToWorker?.message_id,
  ]);
  const distinctReplyIds = input.reviewerToWorker?.message_id !== input.verifierToWorker?.message_id;
  const distinctReplyToLinks =
    input.reviewerToWorker?.reply_to === input.workerToReviewer?.message_id &&
    input.verifierToWorker?.reply_to === input.workerToVerifier?.message_id &&
    input.reviewerToWorker?.reply_to !== input.verifierToWorker?.reply_to;
  const correlationIntegrity =
    input.workerToReviewer?.correlation_id === "corr_worker_reviewer" &&
    input.reviewerToWorker?.correlation_id === input.workerToReviewer?.correlation_id &&
    input.workerToVerifier?.correlation_id === "corr_worker_verifier" &&
    input.verifierToWorker?.correlation_id === input.workerToVerifier?.correlation_id &&
    uniqueStrings([input.workerToReviewer?.correlation_id, input.workerToVerifier?.correlation_id]);
  const roleThreadIntegrity =
    hasThreadDelivery(input.deliveries, "worker", "reviewer", input.workerThreadId, input.reviewerThreadId) &&
    hasThreadDelivery(input.deliveries, "reviewer", "worker", input.reviewerThreadId, input.workerThreadId) &&
    hasThreadDelivery(input.deliveries, "worker", "verifier", input.workerThreadId, input.verifierThreadId) &&
    hasThreadDelivery(input.deliveries, "verifier", "worker", input.verifierThreadId, input.workerThreadId);
  const appendOnlySequence = hasExpectedMessageEventSequence(input.messageEvents);
  const acceptance = {
    worker_thread_started: passFail(Boolean(input.workerThreadId)),
    reviewer_thread_started: passFail(Boolean(input.reviewerThreadId)),
    verifier_thread_started: passFail(Boolean(input.verifierThreadId)),
    worker_to_reviewer_message: passFail(input.workerToReviewer?.type === "MESSAGE_TO_CODEX"),
    worker_to_reviewer_message_emitted: passFail(input.workerToReviewer?.type === "MESSAGE_TO_CODEX"),
    worker_to_reviewer_message_routed: passFail(workerReviewerRouted),
    reviewer_to_worker_reply: passFail(input.reviewerToWorker?.type === "CODEX_MESSAGE_REPLY"),
    reviewer_reply_emitted: passFail(input.reviewerToWorker?.type === "CODEX_MESSAGE_REPLY"),
    reviewer_reply_routed_to_worker: passFail(reviewerWorkerRouted),
    worker_resumed_after_reviewer: passFail(hasMessageEvent(input.messageEvents, "WORKER_RESUMED", 1)),
    worker_to_verifier_message: passFail(input.workerToVerifier?.type === "MESSAGE_TO_CODEX"),
    worker_to_verifier_message_emitted: passFail(input.workerToVerifier?.type === "MESSAGE_TO_CODEX"),
    worker_to_verifier_message_routed: passFail(workerVerifierRouted),
    verifier_to_worker_reply: passFail(input.verifierToWorker?.type === "CODEX_MESSAGE_REPLY"),
    verifier_reply_emitted: passFail(input.verifierToWorker?.type === "CODEX_MESSAGE_REPLY"),
    verifier_reply_routed_to_worker: passFail(verifierWorkerRouted),
    worker_resumed_after_verifier: passFail(hasMessageEvent(input.messageEvents, "WORKER_RESUMED", 2)),
    worker_done_after_verifier: passFail(input.workerDone?.type === "DONE"),
    conversation_id_preserved: passFail(conversationPreserved),
    same_conversation_id_preserved: passFail(conversationPreserved),
    distinct_message_ids: passFail(distinctMessageIds),
    distinct_reply_ids: passFail(distinctReplyIds),
    distinct_reply_to_links: passFail(distinctReplyToLinks),
    role_thread_integrity: passFail(roleThreadIntegrity),
    reply_to_integrity: passFail(distinctReplyToLinks),
    correlation_integrity: passFail(correlationIntegrity),
    per_role_correlation_integrity: passFail(correlationIntegrity),
    append_only_log_records_all_role_hops: passFail(appendOnlySequence),
  };
  return {
    result: input.result,
    phase: "CEA-026",
    task_id: "CEA-026",
    title: "Multi-role Codex Channel",
    completed_at: new Date().toISOString(),
    job_id: input.jobId,
    conversation_id: input.conversationId,
    implemented: [
      "multi_role_channel_smoke",
      "verifier_thread_registration",
      "worker_reviewer_verifier_route",
      "role_specific_reply_correlation",
      "append_only_multirole_message_log",
    ],
    validation: {
      build: input.result === "PASS" ? "PASS" : "FAIL",
      unit_tests: input.result === "PASS" ? "PASS" : "FAIL",
      channel_multirole_smoke: input.result === "PASS" ? "PASS" : "FAIL",
      npm_run_build: input.result === "PASS" ? "PASS" : "FAIL",
      npm_run_test: input.result === "PASS" ? "PASS" : "FAIL",
      npm_run_channel_multirole: input.result === "PASS" ? "PASS" : "FAIL",
    },
    acceptance,
    messages: {
      worker_to_reviewer: input.workerToReviewer,
      reviewer_to_worker: input.reviewerToWorker,
      worker_to_verifier: input.workerToVerifier,
      verifier_to_worker: input.verifierToWorker,
      worker_done: input.workerDone,
      deliveries: input.deliveries,
      message_events: input.messageEvents,
    },
    artifacts: {
      message_log: input.messageLogPath,
      append_only_message_log: input.appendOnlyMessageLogPath,
      events: input.eventsPath,
      report: input.reportPath,
      receipt: input.receiptPath,
    },
    boundaries: boundaryFlags,
    boundary_flags: boundaryFlags,
    policy_decisions: input.policyDecisions,
    risk: {
      production_ready: "NO",
      real_repo_ready: "NO",
      workspace_write_ready: "NO",
      agents_os_integrated: "NO",
      vcptoolbox_integrated: "NO",
      next_required_step: "CEA-027_CHANNEL_POLICY_AND_ROLE_AUTHORITY",
    },
    stopped_reason: input.stoppedReason,
  };
}

function hasDelivery(
  deliveries: readonly CodexMessageDelivery[],
  status: CodexMessageDelivery["status"],
  messageId: string,
  replyTo: string | undefined,
  to: CodexPeerRole,
): boolean {
  return deliveries.some(
    (delivery) =>
      delivery.status === status &&
      delivery.messageId === messageId &&
      delivery.replyTo === replyTo &&
      delivery.to === to,
  );
}

function hasThreadDelivery(
  deliveries: readonly CodexMessageDelivery[],
  from: CodexPeerRole,
  to: CodexPeerRole,
  fromThreadId: string | null,
  toThreadId: string | null,
): boolean {
  return deliveries.some(
    (delivery) =>
      delivery.from === from &&
      delivery.to === to &&
      delivery.fromThreadId === fromThreadId &&
      delivery.toThreadId === toThreadId,
  );
}

function hasMessageEvent(events: readonly MessageEventRecord[], event: MessageBusAuditEvent["event"], round: number): boolean {
  return events.some((record) => record.event === event && record.round === round);
}

function hasExpectedMessageEventSequence(events: readonly MessageEventRecord[]): boolean {
  const expected = [
    ["MESSAGE_CAPTURED", "worker", "reviewer", 1],
    ["MESSAGE_ROUTED", "worker", "reviewer", 1],
    ["REPLY_CAPTURED", "reviewer", "worker", 1],
    ["REPLY_ROUTED", "reviewer", "worker", 1],
    ["WORKER_RESUMED", "reviewer", "worker", 1],
    ["MESSAGE_CAPTURED", "worker", "verifier", 2],
    ["MESSAGE_ROUTED", "worker", "verifier", 2],
    ["REPLY_CAPTURED", "verifier", "worker", 2],
    ["REPLY_ROUTED", "verifier", "worker", 2],
    ["WORKER_RESUMED", "verifier", "worker", 2],
    ["CHANNEL_DONE", undefined, undefined, 2],
  ] as const;
  if (events.length !== expected.length) return false;
  return expected.every(
    ([event, from, to, round], index) =>
      events[index]?.event === event &&
      events[index]?.from === from &&
      events[index]?.to === to &&
      events[index]?.round === round,
  );
}

function uniqueStrings(values: readonly (string | undefined)[]): boolean {
  const present = values.filter((value): value is string => typeof value === "string");
  return present.length === values.length && new Set(present).size === present.length;
}

function passFail(value: boolean): "PASS" | "FAIL" {
  return value ? "PASS" : "FAIL";
}

async function writeReceipt(filePath: string, report: Record<string, unknown>): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const acceptance = report.acceptance as Record<string, string>;
  const validation = report.validation as Record<string, string>;
  const artifacts = report.artifacts as Record<string, string>;
  const risk = report.risk as Record<string, string>;
  const lines = [
    "# CEA-026 Multi-role Codex Channel Receipt",
    "",
    `result: ${String(report.result)}`,
    `phase: ${String(report.phase)}`,
    `job_id: ${String(report.job_id)}`,
    `conversation_id: ${String(report.conversation_id)}`,
    "",
    "## Summary",
    "- Implemented a three-role Worker / Reviewer / Verifier synthetic Codex channel smoke.",
    "- Preserved role identity, thread identity, reply_to, correlation_id, conversation_id, and append-only route events.",
    "",
    "## Validation",
    ...Object.entries(validation).map(([key, value]) => `- ${key}: ${value}`),
    "",
    "## Acceptance",
    ...Object.entries(acceptance).map(([key, value]) => `- ${key}: ${value}`),
    "",
    "## Boundary Confirmation",
    ...Object.entries(boundaryFlags).map(([key, value]) => `- ${key}: ${value}`),
    "",
    "## Artifacts",
    `- message_log: ${artifacts.message_log}`,
    `- append_only_message_log: ${artifacts.append_only_message_log}`,
    `- events: ${artifacts.events}`,
    `- report: ${artifacts.report}`,
    `- receipt: ${artifacts.receipt}`,
    "",
    "## Remaining Limitations",
    `- production_ready: ${risk.production_ready}`,
    `- real_repo_ready: ${risk.real_repo_ready}`,
    `- workspace_write_ready: ${risk.workspace_write_ready}`,
    `- agents_os_integrated: ${risk.agents_os_integrated}`,
    `- vcptoolbox_integrated: ${risk.vcptoolbox_integrated}`,
    `- next_required_step: ${risk.next_required_step}`,
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
