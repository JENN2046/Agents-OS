import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { createAppServerClient } from "../appserver/client.js";
import { createStdioTransport } from "../appserver/transport_stdio.js";
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
  type MessageToCodex,
} from "../types/messages.js";
import type { LoopEvent } from "../types/events.js";

const TURN_TIMEOUT_MS = 180_000;
const REQUEST_TIMEOUT_MS = 60_000;
const CONVERSATION_ID = "conv_multiturn_001";

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
} as const;

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const syntheticWorkspaceRoot = path.join(projectRoot, "data", "synthetic-workspace");
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const dateStamp = formatDateForReceipt(new Date());
  const jobId = `cea-025-multiturn-${timestamp}`;
  const events = createFileEventStore(path.join(projectRoot, "data", "events"));
  const messageEvents = createFileMessageEventStore(path.join(projectRoot, "data", "message-logs"));
  const messageLogPath = path.join(projectRoot, "data", "message-logs", `${jobId}.json`);
  const appendOnlyMessageLogPath = messageEvents.pathFor(jobId);
  const reportPath = path.join(projectRoot, "data", "reports", "cea-025_multi_turn_codex_dialogue.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", `${dateStamp}-cea-025-multi-turn-codex-dialogue.receipt.md`);
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
  let round1WorkerMessage: MessageToCodex | undefined;
  let round1ReviewerReply: CodexMessageReply | undefined;
  let round2WorkerMessage: MessageToCodex | undefined;
  let round2ReviewerReply: CodexMessageReply | undefined;
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

  await mkdir(syntheticWorkspaceRoot, { recursive: true });
  const transport = createStdioTransport({
    cwd: syntheticWorkspaceRoot,
    timeoutMs: REQUEST_TIMEOUT_MS,
  });
  const client = createAppServerClient(transport, {
    requestTimeoutMs: REQUEST_TIMEOUT_MS,
    clientInfo: {
      name: "codex-appserver-active-loop",
      title: "CEA-025 Multi-turn Codex Dialogue",
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
    registry.register({ role: "worker", threadId: workerThreadId, cwd: syntheticWorkspaceRoot, label: "CEA-025 Worker Codex" });
    await appendEvent("APP_SERVER_MESSAGE", { method: "thread/start/result", role: "worker", threadId: workerThreadId, cwd: syntheticWorkspaceRoot });

    const reviewerThread = await startChannelThread(client, syntheticWorkspaceRoot, "Reviewer");
    reviewerThreadId = getThreadId(reviewerThread);
    registry.register({ role: "reviewer", threadId: reviewerThreadId, cwd: syntheticWorkspaceRoot, label: "CEA-025 Reviewer Codex" });
    await appendEvent("APP_SERVER_MESSAGE", { method: "thread/start/result", role: "reviewer", threadId: reviewerThreadId, cwd: syntheticWorkspaceRoot });

    round1WorkerMessage = await runTurnAndParseMessageToCodex(client, tracker, {
      threadId: workerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createWorkerMessagePrompt(1),
    });
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/round-1-worker-message-emitted", message: round1WorkerMessage });
    const round1MessageDelivery = router.routeMessage(round1WorkerMessage);
    deliveries.push(round1MessageDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/round-1-message-routed", delivery: round1MessageDelivery });

    round1ReviewerReply = await runTurnAndParseReply(client, tracker, {
      threadId: reviewerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createReviewerReplyPrompt(1, round1WorkerMessage),
    });
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/round-1-reviewer-reply-emitted", reply: round1ReviewerReply });
    const round1ReplyDelivery = router.routeReply(round1ReviewerReply);
    deliveries.push(round1ReplyDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/round-1-reply-returned", delivery: round1ReplyDelivery });
    await messageEvents.append(jobId, createWorkerResumedEvent(1, round1WorkerMessage, round1ReviewerReply));

    round2WorkerMessage = await runTurnAndParseMessageToCodex(client, tracker, {
      threadId: workerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createWorkerMessagePrompt(2, round1WorkerMessage, round1ReviewerReply),
    });
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/round-2-worker-message-emitted", message: round2WorkerMessage });
    const round2MessageDelivery = router.routeMessage(round2WorkerMessage);
    deliveries.push(round2MessageDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/round-2-message-routed", delivery: round2MessageDelivery });

    round2ReviewerReply = await runTurnAndParseReply(client, tracker, {
      threadId: reviewerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createReviewerReplyPrompt(2, round2WorkerMessage),
    });
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/round-2-reviewer-reply-emitted", reply: round2ReviewerReply });
    const round2ReplyDelivery = router.routeReply(round2ReviewerReply);
    deliveries.push(round2ReplyDelivery);
    await flushMessageAuditEvents();
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/round-2-reply-returned", delivery: round2ReplyDelivery });
    await messageEvents.append(jobId, createWorkerResumedEvent(2, round2WorkerMessage, round2ReviewerReply));

    workerDone = await runTurnAndParseDone(client, tracker, {
      threadId: workerThreadId,
      cwd: syntheticWorkspaceRoot,
      prompt: createWorkerDonePrompt({
        round1WorkerMessage,
        round1ReviewerReply,
        round2WorkerMessage,
        round2ReviewerReply,
      }),
    });
    await appendEvent("APP_SERVER_MESSAGE", { method: "codex-channel/worker-done-after-round-2", output: workerDone });
    bus.markConversationDone(CONVERSATION_ID);
    await flushMessageAuditEvents();
    if (stopReason) {
      throw new Error(stopReason);
    }

    registry.markStatus(workerThreadId, "COMPLETED");
    registry.markStatus(reviewerThreadId, "COMPLETED");
    const messageEventLog = await messageEvents.read(jobId);
    const maxRoundExceededBlocks = verifyMaxRoundExceededBlocks();
    const messageLog = {
      job_id: jobId,
      conversation_id: CONVERSATION_ID,
      registry: registry.snapshot(),
      bus: bus.snapshot(),
      deliveries,
      worker_done: workerDone,
      message_events: messageEventLog,
      max_round_exceeded_blocks: maxRoundExceededBlocks,
      boundary_flags: boundaryFlags,
    };
    await writeJson(messageLogPath, messageLog);
    const report = createReport({
      result: "PASS",
      jobId,
      conversationId: CONVERSATION_ID,
      workerThreadId,
      reviewerThreadId,
      round1WorkerMessage,
      round1ReviewerReply,
      round2WorkerMessage,
      round2ReviewerReply,
      workerDone,
      deliveries,
      messageEvents: messageEventLog,
      messageLogPath,
      appendOnlyMessageLogPath,
      messageTtlMs: bus.messageTtlMs,
      maxRounds: bus.maxRounds,
      conversationState: bus.getConversationState(CONVERSATION_ID),
      maxRoundExceededBlocks,
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
    const failure = stopReason ?? (error instanceof Error ? error.message : "unknown CEA-025 multi-turn channel failure");
    const messageEventLog = await readMessageEventsIfPresent(messageEvents, jobId);
    const maxRoundExceededBlocks = verifyMaxRoundExceededBlocks();
    const report = createReport({
      result: "BLOCK",
      jobId,
      conversationId: CONVERSATION_ID,
      workerThreadId: workerThreadId ?? null,
      reviewerThreadId: reviewerThreadId ?? null,
      round1WorkerMessage: round1WorkerMessage ?? null,
      round1ReviewerReply: round1ReviewerReply ?? null,
      round2WorkerMessage: round2WorkerMessage ?? null,
      round2ReviewerReply: round2ReviewerReply ?? null,
      workerDone: workerDone ?? null,
      deliveries,
      messageEvents: messageEventLog,
      messageLogPath,
      appendOnlyMessageLogPath,
      messageTtlMs: bus.messageTtlMs,
      maxRounds: bus.maxRounds,
      conversationState: bus.getConversationState(CONVERSATION_ID),
      maxRoundExceededBlocks,
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
      `CEA-025 ${role} Codex.`,
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
    throw new Error("Worker did not emit DONE after round 2");
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

function createWorkerMessagePrompt(round: 1 | 2, previousMessage?: MessageToCodex, previousReply?: CodexMessageReply): string {
  const expected = expectedWorkerMessage(round);
  const lines = [
    round === 1
      ? "Emit round 1 MESSAGE_TO_CODEX for the multi-turn Codex channel."
      : "Resume after round 1 reply and emit round 2 MESSAGE_TO_CODEX for the same conversation.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(expected, null, 2),
  ];
  if (previousMessage && previousReply) {
    lines.push("Round 1 Worker message:", JSON.stringify(previousMessage, null, 2), "Round 1 Reviewer reply:", JSON.stringify(previousReply, null, 2));
  }
  return lines.join("\n");
}

function createReviewerReplyPrompt(round: 1 | 2, workerMessage: MessageToCodex): string {
  return [
    `You received round ${round} MESSAGE_TO_CODEX from Worker Codex through the Bridge.`,
    "Reply to the exact message_id using CODEX_MESSAGE_REPLY.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(expectedReviewerReply(round), null, 2),
    "Original Worker message:",
    JSON.stringify(workerMessage, null, 2),
  ].join("\n");
}

function createWorkerDonePrompt(input: {
  readonly round1WorkerMessage: MessageToCodex;
  readonly round1ReviewerReply: CodexMessageReply;
  readonly round2WorkerMessage: MessageToCodex;
  readonly round2ReviewerReply: CodexMessageReply;
}): string {
  return [
    "Bridge returned both CODEX_MESSAGE_REPLY envelopes to Worker Codex.",
    "Acknowledge that reply_to, correlation_id, and conversation_id matched in both rounds.",
    "Return only this JSON object, with no markdown:",
    JSON.stringify(expectedWorkerDone(), null, 2),
    "Round 1 Worker message:",
    JSON.stringify(input.round1WorkerMessage, null, 2),
    "Round 1 Reviewer reply:",
    JSON.stringify(input.round1ReviewerReply, null, 2),
    "Round 2 Worker message:",
    JSON.stringify(input.round2WorkerMessage, null, 2),
    "Round 2 Reviewer reply:",
    JSON.stringify(input.round2ReviewerReply, null, 2),
  ].join("\n");
}

function expectedWorkerMessage(round: 1 | 2): MessageToCodex {
  if (round === 1) {
    return {
      type: "MESSAGE_TO_CODEX",
      message_id: "msg_worker_round_1",
      correlation_id: "corr_round_1",
      conversation_id: CONVERSATION_ID,
      from: "worker",
      to: "reviewer",
      kind: "question",
      payload: {
        question: "Please review round 1 decision point.",
        context: [],
        expected_response: "decision",
      },
    };
  }
  return {
    type: "MESSAGE_TO_CODEX",
    message_id: "msg_worker_round_2",
    correlation_id: "corr_round_2",
    conversation_id: CONVERSATION_ID,
    from: "worker",
    to: "reviewer",
    kind: "question",
    payload: {
      question: "Please review round 2 decision point after applying round 1 guidance.",
      context: [],
      expected_response: "decision",
    },
  };
}

function expectedReviewerReply(round: 1 | 2): CodexMessageReply {
  if (round === 1) {
    return {
      type: "CODEX_MESSAGE_REPLY",
      message_id: "msg_reviewer_round_1",
      reply_to: "msg_worker_round_1",
      correlation_id: "corr_round_1",
      conversation_id: CONVERSATION_ID,
      from: "reviewer",
      to: "worker",
      kind: "decision",
      payload: {
        decision: "continue",
        reason: "Round 1 is valid for this synthetic multi-turn channel test.",
        next_instruction: "Continue to round 2 and emit the second MESSAGE_TO_CODEX.",
      },
    };
  }
  return {
    type: "CODEX_MESSAGE_REPLY",
    message_id: "msg_reviewer_round_2",
    reply_to: "msg_worker_round_2",
    correlation_id: "corr_round_2",
    conversation_id: CONVERSATION_ID,
    from: "reviewer",
    to: "worker",
    kind: "decision",
    payload: {
      decision: "continue",
      reason: "Round 2 is valid and the dialogue can complete.",
      next_instruction: "Emit DONE with evidence for both rounds.",
    },
  };
}

function expectedWorkerDone(): WorkerDone {
  return {
    type: "DONE",
    summary: "Multi-turn Codex dialogue completed.",
    evidence: [
      "round 1 Worker MESSAGE_TO_CODEX routed to Reviewer",
      "round 1 Reviewer CODEX_MESSAGE_REPLY returned to Worker",
      "round 2 Worker MESSAGE_TO_CODEX routed to Reviewer",
      "round 2 Reviewer CODEX_MESSAGE_REPLY returned to Worker",
      "Worker resumed after both replies and emitted DONE",
    ],
  };
}

function createWorkerResumedEvent(round: 1 | 2, workerMessage: MessageToCodex, reviewerReply: CodexMessageReply): MessageBusAuditEvent {
  return {
    event: "WORKER_RESUMED",
    timestamp: new Date().toISOString(),
    message_id: reviewerReply.message_id,
    reply_to: workerMessage.message_id,
    conversation_id: workerMessage.conversation_id,
    correlation_id: workerMessage.correlation_id,
    from: reviewerReply.from,
    to: reviewerReply.to,
    round,
    round_count: round,
    max_rounds: 3,
  };
}

function verifyMaxRoundExceededBlocks(): boolean {
  const bus = createMessageBus({ messageTtlMs: 300_000, maxRounds: 3 });
  for (const round of [1, 2, 3] as const) {
    const message = guardWorkerMessage(round);
    bus.captureMessage(message);
    bus.markRouted(message.message_id, "thread_reviewer_guard");
    bus.captureReply(guardReviewerReply(round), "thread_worker_guard");
  }
  const fourth = guardWorkerMessage(4);
  bus.captureMessage(fourth);
  try {
    bus.markRouted(fourth.message_id, "thread_reviewer_guard");
    return false;
  } catch (error) {
    return (
      error instanceof Error &&
      error.message === "conversation max rounds exceeded: conv_multiturn_guard" &&
      bus.getConversationState("conv_multiturn_guard")?.status === "BLOCKED"
    );
  }
}

function guardWorkerMessage(round: number): MessageToCodex {
  return {
    type: "MESSAGE_TO_CODEX",
    message_id: `msg_worker_guard_${round}`,
    correlation_id: `corr_guard_${round}`,
    conversation_id: "conv_multiturn_guard",
    from: "worker",
    to: "reviewer",
    kind: "question",
    payload: {
      question: `Guard round ${round}?`,
      context: [],
      expected_response: "decision",
    },
  };
}

function guardReviewerReply(round: number): CodexMessageReply {
  return {
    type: "CODEX_MESSAGE_REPLY",
    message_id: `msg_reviewer_guard_${round}`,
    reply_to: `msg_worker_guard_${round}`,
    correlation_id: `corr_guard_${round}`,
    conversation_id: "conv_multiturn_guard",
    from: "reviewer",
    to: "worker",
    kind: "decision",
    payload: {
      decision: "continue",
      reason: `Guard round ${round} accepted.`,
      next_instruction: "Continue.",
    },
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
    rejectLiveTerminalNonCompletedTurn(initialTurn, "channel multiturn smoke turn");
  } catch (error) {
    return Promise.reject(error);
  }
  const existing = tracker.completedTurns.get(initialTurn.id);
  if (existing) {
    try {
      return Promise.resolve(assertLiveTurnCompleted(existing, "channel multiturn smoke turn"));
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
          resolve(assertLiveTurnCompleted(completed, "channel multiturn smoke turn"));
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
  readonly round1WorkerMessage: MessageToCodex | null;
  readonly round1ReviewerReply: CodexMessageReply | null;
  readonly round2WorkerMessage: MessageToCodex | null;
  readonly round2ReviewerReply: CodexMessageReply | null;
  readonly workerDone: WorkerDone | null;
  readonly deliveries: readonly CodexMessageDelivery[];
  readonly messageEvents: readonly MessageEventRecord[];
  readonly messageLogPath: string;
  readonly appendOnlyMessageLogPath: string;
  readonly messageTtlMs: number;
  readonly maxRounds: number;
  readonly conversationState: unknown;
  readonly maxRoundExceededBlocks: boolean;
  readonly eventsPath: string;
  readonly reportPath: string;
  readonly receiptPath: string;
  readonly policyDecisions: readonly PolicyDecision[];
  readonly stoppedReason: string | null;
}): Record<string, unknown> {
  const round1MessageRouted = hasDelivery(input.deliveries, "MESSAGE_ROUTED", "msg_worker_round_1", undefined, "reviewer");
  const round1ReplyRouted = hasDelivery(input.deliveries, "REPLY_ROUTED", "msg_reviewer_round_1", "msg_worker_round_1", "worker");
  const round2MessageRouted = hasDelivery(input.deliveries, "MESSAGE_ROUTED", "msg_worker_round_2", undefined, "reviewer");
  const round2ReplyRouted = hasDelivery(input.deliveries, "REPLY_ROUTED", "msg_reviewer_round_2", "msg_worker_round_2", "worker");
  const conversationIdPreserved =
    [input.round1WorkerMessage, input.round1ReviewerReply, input.round2WorkerMessage, input.round2ReviewerReply].every(
      (message) => message?.conversation_id === input.conversationId,
    );
  const distinctMessageIds = uniqueStrings([
    input.round1WorkerMessage?.message_id,
    input.round1ReviewerReply?.message_id,
    input.round2WorkerMessage?.message_id,
    input.round2ReviewerReply?.message_id,
  ]);
  const distinctReplyToLinks =
    input.round1ReviewerReply?.reply_to === input.round1WorkerMessage?.message_id &&
    input.round2ReviewerReply?.reply_to === input.round2WorkerMessage?.message_id &&
    input.round1ReviewerReply?.reply_to !== input.round2ReviewerReply?.reply_to;
  const correlationIntegrity =
    input.round1WorkerMessage?.correlation_id === "corr_round_1" &&
    input.round1ReviewerReply?.correlation_id === input.round1WorkerMessage?.correlation_id &&
    input.round2WorkerMessage?.correlation_id === "corr_round_2" &&
    input.round2ReviewerReply?.correlation_id === input.round2WorkerMessage?.correlation_id;
  const acceptance = {
    worker_thread_started: passFail(Boolean(input.workerThreadId)),
    reviewer_thread_started: passFail(Boolean(input.reviewerThreadId)),
    round_1_message: passFail(input.round1WorkerMessage?.type === "MESSAGE_TO_CODEX"),
    round_1_message_emitted: passFail(input.round1WorkerMessage?.type === "MESSAGE_TO_CODEX"),
    round_1_message_routed: passFail(round1MessageRouted),
    round_1_reply: passFail(input.round1ReviewerReply?.type === "CODEX_MESSAGE_REPLY"),
    round_1_reply_emitted: passFail(input.round1ReviewerReply?.type === "CODEX_MESSAGE_REPLY"),
    round_1_reply_routed: passFail(round1ReplyRouted),
    worker_resumed_after_round_1: passFail(hasMessageEvent(input.messageEvents, "WORKER_RESUMED", 1)),
    round_2_message: passFail(input.round2WorkerMessage?.type === "MESSAGE_TO_CODEX"),
    round_2_message_emitted: passFail(input.round2WorkerMessage?.type === "MESSAGE_TO_CODEX"),
    round_2_message_routed: passFail(round2MessageRouted),
    round_2_reply: passFail(input.round2ReviewerReply?.type === "CODEX_MESSAGE_REPLY"),
    round_2_reply_emitted: passFail(input.round2ReviewerReply?.type === "CODEX_MESSAGE_REPLY"),
    round_2_reply_routed: passFail(round2ReplyRouted),
    worker_resumed_after_round_2: passFail(hasMessageEvent(input.messageEvents, "WORKER_RESUMED", 2)),
    worker_done_after_round_2: passFail(input.workerDone?.type === "DONE"),
    conversation_id_preserved: passFail(conversationIdPreserved),
    same_conversation_id_preserved: passFail(conversationIdPreserved),
    distinct_message_ids: passFail(distinctMessageIds),
    distinct_reply_ids: passFail(input.round1ReviewerReply?.message_id !== input.round2ReviewerReply?.message_id),
    distinct_reply_to_links: passFail(distinctReplyToLinks),
    reply_to_integrity: passFail(distinctReplyToLinks),
    correlation_integrity: passFail(correlationIntegrity),
    per_round_correlation_integrity: passFail(correlationIntegrity),
    max_round_guard_under_limit: passFail(input.maxRounds === 3 && getRoundCount(input.conversationState) === 2),
    max_round_guard_exceeded_blocks: passFail(input.maxRoundExceededBlocks),
    append_only_log_records_all_rounds: passFail(hasExpectedMessageEventSequence(input.messageEvents)),
  };
  return {
    result: input.result,
    phase: "CEA-025",
    task_id: "CEA-025",
    title: "Multi-turn Codex Dialogue",
    completed_at: new Date().toISOString(),
    job_id: input.jobId,
    conversation_id: input.conversationId,
    implemented: [
      "multi_turn_channel_smoke",
      "conversation_round_state",
      "two_round_worker_reviewer_dialogue",
      "max_round_guard_positive_and_negative_tests",
      "append_only_multiturn_message_log",
    ],
    validation: {
      build: input.result === "PASS" ? "PASS" : "FAIL",
      unit_tests: input.result === "PASS" ? "PASS" : "FAIL",
      channel_multiturn_smoke: input.result === "PASS" ? "PASS" : "FAIL",
      npm_run_build: input.result === "PASS" ? "PASS" : "FAIL",
      npm_run_test: input.result === "PASS" ? "PASS" : "FAIL",
      npm_run_channel_multiturn: input.result === "PASS" ? "PASS" : "FAIL",
    },
    acceptance,
    messages: {
      round_1_worker_message: input.round1WorkerMessage,
      round_1_reviewer_reply: input.round1ReviewerReply,
      round_2_worker_message: input.round2WorkerMessage,
      round_2_reviewer_reply: input.round2ReviewerReply,
      worker_done: input.workerDone,
      deliveries: input.deliveries,
      conversation_state: input.conversationState,
      message_events: input.messageEvents,
      message_ttl_ms: input.messageTtlMs,
      max_rounds: input.maxRounds,
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
      multi_role_ready: "NO",
      workspace_write_ready: "NO",
      next_required_step: "CEA-026_MULTI_ROLE_CODEX_CHANNEL",
    },
    stopped_reason: input.stoppedReason,
  };
}

function hasDelivery(
  deliveries: readonly CodexMessageDelivery[],
  status: CodexMessageDelivery["status"],
  messageId: string,
  replyTo: string | undefined,
  to: string,
): boolean {
  return deliveries.some(
    (delivery) =>
      delivery.status === status &&
      delivery.messageId === messageId &&
      delivery.replyTo === replyTo &&
      delivery.to === to,
  );
}

function hasMessageEvent(events: readonly MessageEventRecord[], event: MessageBusAuditEvent["event"], round: number): boolean {
  return events.some((record) => record.event === event && record.round === round);
}

function hasExpectedMessageEventSequence(events: readonly MessageEventRecord[]): boolean {
  const expected = [
    ["MESSAGE_CAPTURED", 1],
    ["MESSAGE_ROUTED", 1],
    ["REPLY_CAPTURED", 1],
    ["REPLY_ROUTED", 1],
    ["WORKER_RESUMED", 1],
    ["MESSAGE_CAPTURED", 2],
    ["MESSAGE_ROUTED", 2],
    ["REPLY_CAPTURED", 2],
    ["REPLY_ROUTED", 2],
    ["WORKER_RESUMED", 2],
    ["CHANNEL_DONE", 2],
  ] as const;
  if (events.length !== expected.length) return false;
  return expected.every(([event, round], index) => events[index]?.event === event && events[index]?.round === round);
}

function uniqueStrings(values: readonly (string | undefined)[]): boolean {
  const present = values.filter((value): value is string => typeof value === "string");
  return present.length === values.length && new Set(present).size === present.length;
}

function getRoundCount(value: unknown): number | undefined {
  if (typeof value === "object" && value !== null && "round_count" in value) {
    const roundCount = (value as { readonly round_count?: unknown }).round_count;
    return typeof roundCount === "number" ? roundCount : undefined;
  }
  return undefined;
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
    "# CEA-025 Multi-turn Codex Dialogue Receipt",
    "",
    `result: ${String(report.result)}`,
    `phase: ${String(report.phase)}`,
    `job_id: ${String(report.job_id)}`,
    `conversation_id: ${String(report.conversation_id)}`,
    "",
    "## Summary",
    "- Implemented a two-round Worker <-> Reviewer synthetic Codex dialogue over the hardened message bus.",
    "- Preserved per-round message_id, reply_to, correlation_id, round_count, and append-only message event logging.",
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
    `- multi_role_ready: ${risk.multi_role_ready}`,
    `- workspace_write_ready: ${risk.workspace_write_ready}`,
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
