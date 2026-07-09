import {
  validateCodexMessageReply,
  validateMessageToCodex,
  type CodexMessageReply,
  type CodexPeerRole,
  type MessageToCodex,
} from "../types/messages.js";
import {
  buildConversationSnapshot,
  createDeliveryFingerprint,
  createInMemoryMessageLedgerStore,
  hashMessagePayload,
  type ConversationDeliverySnapshot,
  type ConversationSnapshotIndex,
  type MessageLedgerEntry,
  type MessageLedgerSnapshot,
  type MessageLedgerState,
  type MessageLedgerStore,
} from "../stores/message_ledger.js";

// Enforces delivery integrity only; role/workspace authority belongs to AGENTS.md and working context.

export type MessageBusMode = "normal" | "observe_only";
export type MessageBusRecordState = "CAPTURED" | "ROUTED" | "REPLIED" | "OBSERVED" | "EXPIRED" | "FAILED";
export type ConversationRouteStatus = "ACTIVE" | "DONE" | "BLOCKED" | "FAILED";
export type MessageBusAuditEventName =
  | "MESSAGE_CAPTURED"
  | "MESSAGE_ROUTED"
  | "MESSAGE_OBSERVED"
  | "REPLY_CAPTURED"
  | "REPLY_ROUTED"
  | "REPLY_OBSERVED"
  | "MESSAGE_EXPIRED"
  | "MESSAGE_REJECTED"
  | "CONVERSATION_BLOCKED"
  | "WORKER_RESUMED"
  | "CHANNEL_DONE";

export interface MessageBusOptions {
  readonly mode?: MessageBusMode;
  readonly messageTtlMs?: number;
  readonly maxRounds?: number;
  readonly ledger?: MessageLedgerStore;
}

export interface MessageBusAuditEvent {
  readonly event: MessageBusAuditEventName;
  readonly timestamp: string;
  readonly message_id?: string;
  readonly reply_to?: string;
  readonly conversation_id?: string;
  readonly correlation_id?: string;
  readonly from?: string;
  readonly to?: string;
  readonly fromThreadId?: string;
  readonly toThreadId?: string;
  readonly message_kind?: string;
  readonly state?: MessageBusRecordState;
  readonly reason?: string;
  readonly round?: number;
  readonly round_count?: number;
  readonly max_rounds?: number;
  readonly payload_hash?: string;
  readonly delivery_fingerprint?: string;
}

export interface ConversationRoundState {
  readonly conversation_id: string;
  readonly round_count: number;
  readonly max_rounds: number;
  readonly message_ids: readonly string[];
  readonly reply_ids: readonly string[];
  readonly status: ConversationRouteStatus;
  readonly blocked_reason?: string;
  readonly failure_reason?: string;
  readonly done_at?: string;
}

export type ConversationRouteState = ConversationRoundState;

export interface MessageBusMessageRecord {
  readonly envelope: MessageToCodex;
  readonly state: MessageBusRecordState;
  readonly created_at: string;
  readonly expires_at: string;
  readonly routed_at?: string;
  readonly observed_at?: string;
  readonly replied_at?: string;
  readonly expired_at?: string;
  readonly failed_at?: string;
  readonly targetThreadId?: string;
  readonly fromThreadId?: string;
  readonly toThreadId?: string;
  readonly replyMessageId?: string;
  readonly failure_reason?: string;
  readonly payload_hash: string;
  readonly delivery_fingerprint: string;
}

export interface MessageBusReplyRecord {
  readonly envelope: CodexMessageReply;
  readonly state: "REPLIED" | "OBSERVED";
  readonly captured_at: string;
  readonly observed_at?: string;
  readonly targetThreadId?: string;
  readonly fromThreadId?: string;
  readonly toThreadId?: string;
  readonly payload_hash: string;
  readonly delivery_fingerprint: string;
}

export interface MessageBusSnapshot {
  readonly messages: readonly MessageBusMessageRecord[];
  readonly replies: readonly MessageBusReplyRecord[];
  readonly conversations: readonly ConversationRouteState[];
  readonly audit_events: readonly MessageBusAuditEvent[];
  readonly ledger: MessageLedgerSnapshot;
  readonly conversation_snapshots: ConversationSnapshotIndex;
}

export interface CodexMessageBus {
  readonly mode: MessageBusMode;
  readonly messageTtlMs: number;
  readonly maxRounds: number;
  captureMessage(message: unknown, at?: string): MessageBusMessageRecord;
  markRouted(messageId: string, targetThreadId: string, at?: string, fromThreadId?: string): MessageBusMessageRecord;
  observeMessage(messageId: string, targetThreadId: string, at?: string, fromThreadId?: string): MessageBusMessageRecord;
  captureReply(reply: unknown, targetThreadId?: string, at?: string, fromThreadId?: string): MessageBusReplyRecord;
  observeReply(reply: unknown, targetThreadId?: string, at?: string, fromThreadId?: string): MessageBusReplyRecord;
  expireMessage(messageId: string, at?: string): MessageBusMessageRecord;
  expireDueMessages(at?: string): readonly MessageBusMessageRecord[];
  getMessage(messageId: string): MessageBusMessageRecord | undefined;
  getReplyFor(messageId: string): MessageBusReplyRecord | undefined;
  getConversationState(conversationId: string): ConversationRouteState | undefined;
  markConversationDone(conversationId: string, at?: string): ConversationRouteState;
  pendingFor(role: CodexPeerRole): readonly MessageBusMessageRecord[];
  conversation(conversationId: string): MessageBusSnapshot;
  auditEvents(): readonly MessageBusAuditEvent[];
  ledgerSnapshot(): MessageLedgerSnapshot;
  conversationSnapshots(): ConversationSnapshotIndex;
  conversationSnapshot(conversationId: string): ConversationDeliverySnapshot | undefined;
  snapshot(): MessageBusSnapshot;
}

const defaultMessageTtlMs = 300_000;
const defaultMaxRounds = 3;

export function createMessageBus(options: MessageBusOptions = {}): CodexMessageBus {
  return new InMemoryMessageBus(
    options.mode ?? "normal",
    options.messageTtlMs ?? defaultMessageTtlMs,
    options.maxRounds ?? defaultMaxRounds,
    options.ledger ?? createInMemoryMessageLedgerStore(),
  );
}

class InMemoryMessageBus implements CodexMessageBus {
  readonly #messages = new Map<string, MessageBusMessageRecord>();
  readonly #replies = new Map<string, MessageBusReplyRecord>();
  readonly #replyIdByMessageId = new Map<string, string>();
  readonly #conversationStates = new Map<string, ConversationRouteState>();
  readonly #auditEvents: MessageBusAuditEvent[] = [];

  constructor(
    readonly mode: MessageBusMode,
    readonly messageTtlMs: number,
    readonly maxRounds: number,
    readonly ledger: MessageLedgerStore,
  ) {
    if (mode !== "normal" && mode !== "observe_only") {
      throw new Error(`unsupported message bus mode: ${mode}`);
    }
    if (!Number.isInteger(messageTtlMs) || messageTtlMs <= 0) {
      throw new Error("message TTL must be a positive integer");
    }
    if (!Number.isInteger(maxRounds) || maxRounds < 0) {
      throw new Error("max rounds must be a non-negative integer");
    }
  }

  captureMessage(message: unknown, at = nowIso()): MessageBusMessageRecord {
    const validation = validateMessageToCodex(message);
    if (!validation.ok) {
      this.#recordRejection(at, validation.error, message);
      throw new Error(validation.error);
    }
    const envelope = validation.value;
    if (this.#messages.has(envelope.message_id) || this.#replies.has(envelope.message_id)) {
      const reason = `duplicate message id: ${envelope.message_id}`;
      this.#recordMessageEvent("MESSAGE_REJECTED", at, envelope, { reason });
      throw new Error(reason);
    }
    const conversation = this.#ensureConversation(envelope.conversation_id);
    if (conversation.status !== "ACTIVE") {
      const reason = conversationClosedReason(conversation);
      this.#recordMessageEvent("MESSAGE_REJECTED", at, envelope, {
        reason,
        round: nextRound(conversation),
        round_count: conversation.round_count,
        max_rounds: conversation.max_rounds,
      });
      throw new Error(reason);
    }
    if (this.#hasDuplicateCorrelationId(envelope)) {
      const reason = `duplicate correlation id in conversation: ${envelope.correlation_id}`;
      this.#recordMessageEvent("MESSAGE_REJECTED", at, envelope, {
        reason,
        round: nextRound(conversation),
        round_count: conversation.round_count,
        max_rounds: conversation.max_rounds,
      });
      throw new Error(reason);
    }
    const inFlight = this.#findInFlightMessage(envelope.conversation_id);
    if (inFlight) {
      const reason = `conversation has in-flight message: ${inFlight.envelope.message_id}`;
      this.#recordMessageEvent("MESSAGE_REJECTED", at, envelope, {
        reason,
        round: nextRound(conversation),
        round_count: conversation.round_count,
        max_rounds: conversation.max_rounds,
      });
      throw new Error(reason);
    }
    const payload_hash = hashMessagePayload(envelope);
    const delivery_fingerprint = createEnvelopeFingerprint(envelope, payload_hash);
    const record: MessageBusMessageRecord = {
      envelope,
      state: "CAPTURED",
      created_at: at,
      expires_at: addMsIso(at, this.messageTtlMs),
      payload_hash,
      delivery_fingerprint,
    };
    this.#messages.set(envelope.message_id, record);
    const nextConversation: ConversationRouteState = {
      ...conversation,
      message_ids: [...conversation.message_ids, envelope.message_id],
    };
    this.#conversationStates.set(envelope.conversation_id, nextConversation);
    this.#recordConversationLedgerState(nextConversation, at);
    this.#recordMessageEvent("MESSAGE_CAPTURED", at, envelope, {
      state: record.state,
      round: nextRound(conversation),
      round_count: conversation.round_count,
      max_rounds: conversation.max_rounds,
    });
    return record;
  }

  markRouted(messageId: string, targetThreadId: string, at = nowIso(), fromThreadId?: string): MessageBusMessageRecord {
    if (this.mode === "observe_only") {
      throw new Error("observe-only message bus cannot mark live routes; use observeMessage");
    }
    const record = this.#messages.get(messageId);
    if (!record) {
      const reason = `cannot route unknown message: ${messageId}`;
      this.#recordBareEvent("MESSAGE_REJECTED", at, { message_id: messageId, reason });
      throw new Error(reason);
    }
    if (record.state !== "CAPTURED") {
      const reason = `message is not routable from state: ${record.state}`;
      this.#recordMessageEvent("MESSAGE_REJECTED", at, record.envelope, { reason, state: record.state });
      throw new Error(reason);
    }
    if (isExpired(record, at)) {
      const expired = this.#markExpired(record, at);
      throw new Error(`message expired: ${expired.envelope.message_id}`);
    }
    const conversation = this.#ensureConversation(record.envelope.conversation_id);
    if (conversation.status !== "ACTIVE") {
      const reason = conversationClosedReason(conversation);
      this.#recordMessageEvent("MESSAGE_REJECTED", at, record.envelope, {
        reason,
        state: record.state,
        round: nextRound(conversation),
        round_count: conversation.round_count,
        max_rounds: conversation.max_rounds,
      });
      throw new Error(reason);
    }
    if (conversation.round_count >= conversation.max_rounds) {
      const reason = `conversation max rounds exceeded: ${conversation.conversation_id}`;
      const blocked = { ...conversation, status: "BLOCKED" as const, blocked_reason: reason };
      this.#conversationStates.set(conversation.conversation_id, blocked);
      this.#messages.set(messageId, {
        ...record,
        state: "FAILED",
        failed_at: at,
        failure_reason: reason,
      });
      this.#recordConversationLedgerState(blocked, at);
      this.#recordMessageEvent("CONVERSATION_BLOCKED", at, record.envelope, {
        reason,
        state: "FAILED",
        round: nextRound(conversation),
        round_count: blocked.round_count,
        max_rounds: blocked.max_rounds,
      });
      throw new Error(reason);
    }
    const next: MessageBusMessageRecord = {
      ...record,
      state: "ROUTED",
      routed_at: at,
      targetThreadId,
      fromThreadId,
      toThreadId: targetThreadId,
    };
    this.#messages.set(messageId, next);
    this.#recordMessageEvent("MESSAGE_ROUTED", at, next.envelope, {
      state: next.state,
      fromThreadId,
      toThreadId: targetThreadId,
      round: nextRound(conversation),
      round_count: conversation.round_count,
      max_rounds: conversation.max_rounds,
    });
    return next;
  }

  observeMessage(messageId: string, targetThreadId: string, at = nowIso(), fromThreadId?: string): MessageBusMessageRecord {
    if (this.mode !== "observe_only") {
      throw new Error("observeMessage requires observe-only message bus mode");
    }
    const record = this.#messages.get(messageId);
    if (!record) {
      const reason = `cannot observe unknown message: ${messageId}`;
      this.#recordBareEvent("MESSAGE_REJECTED", at, { message_id: messageId, reason });
      throw new Error(reason);
    }
    if (record.state !== "CAPTURED") {
      const reason = `message is not observable from state: ${record.state}`;
      this.#recordMessageEvent("MESSAGE_REJECTED", at, record.envelope, { reason, state: record.state });
      throw new Error(reason);
    }
    if (isExpired(record, at)) {
      const expired = this.#markExpired(record, at);
      throw new Error(`message expired: ${expired.envelope.message_id}`);
    }
    const conversation = this.#ensureConversation(record.envelope.conversation_id);
    if (conversation.status !== "ACTIVE") {
      const reason = conversationClosedReason(conversation);
      this.#recordMessageEvent("MESSAGE_REJECTED", at, record.envelope, {
        reason,
        state: record.state,
        round: nextRound(conversation),
        round_count: conversation.round_count,
        max_rounds: conversation.max_rounds,
      });
      throw new Error(reason);
    }
    if (conversation.round_count >= conversation.max_rounds) {
      const reason = `conversation max rounds exceeded: ${conversation.conversation_id}`;
      const blocked = { ...conversation, status: "BLOCKED" as const, blocked_reason: reason };
      this.#conversationStates.set(conversation.conversation_id, blocked);
      this.#messages.set(messageId, {
        ...record,
        state: "FAILED",
        failed_at: at,
        failure_reason: reason,
      });
      this.#recordConversationLedgerState(blocked, at);
      this.#recordMessageEvent("CONVERSATION_BLOCKED", at, record.envelope, {
        reason,
        state: "FAILED",
        round: nextRound(conversation),
        round_count: blocked.round_count,
        max_rounds: blocked.max_rounds,
      });
      throw new Error(reason);
    }
    const next: MessageBusMessageRecord = {
      ...record,
      state: "OBSERVED",
      observed_at: at,
      targetThreadId,
      fromThreadId,
      toThreadId: targetThreadId,
    };
    this.#messages.set(messageId, next);
    this.#recordMessageEvent("MESSAGE_OBSERVED", at, next.envelope, {
      state: next.state,
      fromThreadId,
      toThreadId: targetThreadId,
      round: nextRound(conversation),
      round_count: conversation.round_count,
      max_rounds: conversation.max_rounds,
    });
    return next;
  }

  captureReply(reply: unknown, targetThreadId?: string, at = nowIso(), fromThreadId?: string): MessageBusReplyRecord {
    if (this.mode === "observe_only") {
      throw new Error("observe-only message bus cannot capture live replies; use observeReply");
    }
    const validation = validateCodexMessageReply(reply);
    if (!validation.ok) {
      this.#recordRejection(at, validation.error, reply);
      throw new Error(validation.error);
    }
    const envelope = validation.value;
    if (this.#messages.has(envelope.message_id) || this.#replies.has(envelope.message_id)) {
      const reason = `duplicate message id: ${envelope.message_id}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason });
      throw new Error(reason);
    }
    const original = this.#messages.get(envelope.reply_to);
    if (!original) {
      const reason = `reply_to does not reference a captured message: ${envelope.reply_to}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason });
      throw new Error(reason);
    }
    const conversation = this.#ensureConversation(original.envelope.conversation_id);
    if (conversation.status !== "ACTIVE") {
      const reason = conversationClosedReason(conversation);
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, {
        reason,
        round: nextRound(conversation),
        round_count: conversation.round_count,
        max_rounds: conversation.max_rounds,
      });
      throw new Error(reason);
    }
    if (this.#replyIdByMessageId.has(envelope.reply_to)) {
      const reason = `message already has a reply: ${envelope.reply_to}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason });
      throw new Error(reason);
    }
    if (original.state !== "ROUTED") {
      const reason = `reply before original message is routed: ${envelope.reply_to}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason, state: original.state });
      throw new Error(reason);
    }
    if (isExpired(original, at)) {
      this.#markExpired(original, at);
      const reason = `message expired: ${original.envelope.message_id}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason, state: "EXPIRED" });
      throw new Error(reason);
    }
    assertReplyMatchesOriginal(envelope, original.envelope);
    const payload_hash = hashMessagePayload(envelope);
    const delivery_fingerprint = createEnvelopeFingerprint(envelope, payload_hash, fromThreadId, targetThreadId);
    const record: MessageBusReplyRecord = {
      envelope,
      state: "REPLIED",
      captured_at: at,
      targetThreadId,
      fromThreadId,
      toThreadId: targetThreadId,
      payload_hash,
      delivery_fingerprint,
    };
    this.#replies.set(envelope.message_id, record);
    this.#replyIdByMessageId.set(envelope.reply_to, envelope.message_id);
    this.#messages.set(envelope.reply_to, {
      ...original,
      state: "REPLIED",
      replied_at: at,
      replyMessageId: envelope.message_id,
    });
    const nextConversation = this.#incrementRound(envelope.conversation_id, envelope.message_id);
    this.#recordConversationLedgerState(nextConversation, at);
    this.#recordReplyEvent("REPLY_CAPTURED", at, envelope, {
      fromThreadId,
      toThreadId: targetThreadId,
      round: nextConversation.round_count,
      round_count: nextConversation.round_count,
      max_rounds: nextConversation.max_rounds,
    });
    this.#recordReplyEvent("REPLY_ROUTED", at, envelope, {
      fromThreadId,
      toThreadId: targetThreadId,
      round: nextConversation.round_count,
      round_count: nextConversation.round_count,
      max_rounds: nextConversation.max_rounds,
    });
    return record;
  }

  observeReply(reply: unknown, targetThreadId?: string, at = nowIso(), fromThreadId?: string): MessageBusReplyRecord {
    if (this.mode !== "observe_only") {
      throw new Error("observeReply requires observe-only message bus mode");
    }
    const validation = validateCodexMessageReply(reply);
    if (!validation.ok) {
      this.#recordRejection(at, validation.error, reply);
      throw new Error(validation.error);
    }
    const envelope = validation.value;
    if (this.#messages.has(envelope.message_id) || this.#replies.has(envelope.message_id)) {
      const reason = `duplicate message id: ${envelope.message_id}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason });
      throw new Error(reason);
    }
    const original = this.#messages.get(envelope.reply_to);
    if (!original) {
      const reason = `reply_to does not reference a captured message: ${envelope.reply_to}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason });
      throw new Error(reason);
    }
    const conversation = this.#ensureConversation(original.envelope.conversation_id);
    if (conversation.status !== "ACTIVE") {
      const reason = conversationClosedReason(conversation);
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, {
        reason,
        round: nextRound(conversation),
        round_count: conversation.round_count,
        max_rounds: conversation.max_rounds,
      });
      throw new Error(reason);
    }
    if (this.#replyIdByMessageId.has(envelope.reply_to)) {
      const reason = `message already has a reply: ${envelope.reply_to}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason });
      throw new Error(reason);
    }
    if (original.state !== "OBSERVED") {
      const reason = `reply before original message is observed: ${envelope.reply_to}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason, state: original.state });
      throw new Error(reason);
    }
    if (isExpired(original, at)) {
      this.#markExpired(original, at);
      const reason = `message expired: ${original.envelope.message_id}`;
      this.#recordReplyEvent("MESSAGE_REJECTED", at, envelope, { reason, state: "EXPIRED" });
      throw new Error(reason);
    }
    assertReplyMatchesOriginal(envelope, original.envelope);
    const payload_hash = hashMessagePayload(envelope);
    const delivery_fingerprint = createEnvelopeFingerprint(envelope, payload_hash, fromThreadId, targetThreadId, "OBSERVED");
    const record: MessageBusReplyRecord = {
      envelope,
      state: "OBSERVED",
      captured_at: at,
      observed_at: at,
      targetThreadId,
      fromThreadId,
      toThreadId: targetThreadId,
      payload_hash,
      delivery_fingerprint,
    };
    this.#replies.set(envelope.message_id, record);
    this.#replyIdByMessageId.set(envelope.reply_to, envelope.message_id);
    this.#messages.set(envelope.reply_to, {
      ...original,
      state: "REPLIED",
      replied_at: at,
      replyMessageId: envelope.message_id,
    });
    const nextConversation = this.#incrementRound(envelope.conversation_id, envelope.message_id);
    this.#recordConversationLedgerState(nextConversation, at);
    this.#recordReplyEvent("REPLY_OBSERVED", at, envelope, {
      state: "OBSERVED",
      delivery_fingerprint,
      fromThreadId,
      toThreadId: targetThreadId,
      round: nextConversation.round_count,
      round_count: nextConversation.round_count,
      max_rounds: nextConversation.max_rounds,
    });
    return record;
  }

  expireMessage(messageId: string, at = nowIso()): MessageBusMessageRecord {
    const record = this.#messages.get(messageId);
    if (!record) {
      throw new Error(`cannot expire unknown message: ${messageId}`);
    }
    return this.#markExpired(record, at);
  }

  expireDueMessages(at = nowIso()): readonly MessageBusMessageRecord[] {
    const expired: MessageBusMessageRecord[] = [];
    for (const record of this.#messages.values()) {
      if ((record.state === "CAPTURED" || record.state === "ROUTED" || record.state === "OBSERVED") && isExpired(record, at)) {
        expired.push(this.#markExpired(record, at));
      }
    }
    return expired;
  }

  getMessage(messageId: string): MessageBusMessageRecord | undefined {
    return this.#messages.get(messageId);
  }

  getReplyFor(messageId: string): MessageBusReplyRecord | undefined {
    const replyId = this.#replyIdByMessageId.get(messageId);
    return replyId ? this.#replies.get(replyId) : undefined;
  }

  getConversationState(conversationId: string): ConversationRouteState | undefined {
    return this.#conversationStates.get(conversationId);
  }

  markConversationDone(conversationId: string, at = nowIso()): ConversationRouteState {
    const conversation = this.#ensureConversation(conversationId);
    if (conversation.status === "DONE") return conversation;
    if (conversation.status !== "ACTIVE") {
      const reason = `cannot mark ${conversation.status.toLowerCase()} conversation done: ${conversationId}`;
      this.#recordBareEvent("MESSAGE_REJECTED", at, {
        conversation_id: conversationId,
        reason,
        round: conversation.round_count,
        round_count: conversation.round_count,
        max_rounds: conversation.max_rounds,
      });
      throw new Error(reason);
    }
    const next: ConversationRouteState = {
      ...conversation,
      status: "DONE",
      done_at: at,
    };
    this.#conversationStates.set(conversationId, next);
    this.#recordConversationLedgerState(next, at);
    this.#recordBareEvent("CHANNEL_DONE", at, {
      conversation_id: conversationId,
      round: next.round_count,
      round_count: next.round_count,
      max_rounds: next.max_rounds,
    });
    return next;
  }

  pendingFor(role: CodexPeerRole): readonly MessageBusMessageRecord[] {
    return [...this.#messages.values()].filter(
      (record) => record.envelope.to === role && (record.state === "CAPTURED" || record.state === "ROUTED"),
    );
  }

  conversation(conversationId: string): MessageBusSnapshot {
    const ledger = filterLedgerSnapshot(this.ledger.snapshot(), conversationId);
    return {
      messages: [...this.#messages.values()].filter((record) => record.envelope.conversation_id === conversationId),
      replies: [...this.#replies.values()].filter((record) => record.envelope.conversation_id === conversationId),
      conversations: [...this.#conversationStates.values()].filter((state) => state.conversation_id === conversationId),
      audit_events: this.#auditEvents.filter((event) => event.conversation_id === conversationId),
      ledger,
      conversation_snapshots: buildConversationSnapshot(ledger),
    };
  }

  auditEvents(): readonly MessageBusAuditEvent[] {
    return [...this.#auditEvents];
  }

  ledgerSnapshot(): MessageLedgerSnapshot {
    return this.ledger.snapshot();
  }

  conversationSnapshots(): ConversationSnapshotIndex {
    return buildConversationSnapshot(this.ledgerSnapshot());
  }

  conversationSnapshot(conversationId: string): ConversationDeliverySnapshot | undefined {
    return this.conversationSnapshots().by_conversation_id[conversationId];
  }

  snapshot(): MessageBusSnapshot {
    const ledger = this.ledgerSnapshot();
    return {
      messages: [...this.#messages.values()],
      replies: [...this.#replies.values()],
      conversations: [...this.#conversationStates.values()],
      audit_events: this.auditEvents(),
      ledger,
      conversation_snapshots: buildConversationSnapshot(ledger),
    };
  }

  #ensureConversation(conversationId: string): ConversationRouteState {
    const existing = this.#conversationStates.get(conversationId);
    if (existing) return existing;
    const created: ConversationRouteState = {
      conversation_id: conversationId,
      round_count: 0,
      max_rounds: this.maxRounds,
      message_ids: [],
      reply_ids: [],
      status: "ACTIVE",
    };
    this.#conversationStates.set(conversationId, created);
    return created;
  }

  #incrementRound(conversationId: string, replyMessageId: string): ConversationRouteState {
    const current = this.#ensureConversation(conversationId);
    const next: ConversationRouteState = {
      ...current,
      round_count: current.round_count + 1,
      reply_ids: [...current.reply_ids, replyMessageId],
    };
    this.#conversationStates.set(conversationId, next);
    return next;
  }

  #hasDuplicateCorrelationId(message: MessageToCodex): boolean {
    return [...this.#messages.values()].some(
      (record) =>
        record.envelope.conversation_id === message.conversation_id &&
        record.envelope.correlation_id === message.correlation_id,
    );
  }

  #findInFlightMessage(conversationId: string): MessageBusMessageRecord | undefined {
    return [...this.#messages.values()].find(
      (record) =>
        record.envelope.conversation_id === conversationId &&
        (record.state === "CAPTURED" || record.state === "ROUTED" || record.state === "OBSERVED"),
    );
  }

  #markExpired(record: MessageBusMessageRecord, at: string): MessageBusMessageRecord {
    if (record.state === "REPLIED") return record;
    if (record.state === "EXPIRED") return record;
    const expired: MessageBusMessageRecord = {
      ...record,
      state: "EXPIRED",
      expired_at: at,
    };
    this.#messages.set(record.envelope.message_id, expired);
    this.#recordMessageEvent("MESSAGE_EXPIRED", at, expired.envelope, { state: "EXPIRED" });
    return expired;
  }

  #recordConversationLedgerState(conversation: ConversationRouteState, at: string): void {
    const state = conversation.status;
    this.ledger.record({
      kind: "CONVERSATION",
      at,
      conversation_id: conversation.conversation_id,
      state,
      round_count: conversation.round_count,
      max_rounds: conversation.max_rounds,
      message_ids: conversation.message_ids,
      reply_ids: conversation.reply_ids,
      failure_reason: conversation.blocked_reason ?? conversation.failure_reason,
      delivery_fingerprint: createDeliveryFingerprint({
        type: "CONVERSATION",
        conversation_id: conversation.conversation_id,
        state,
        round_count: conversation.round_count,
        max_rounds: conversation.max_rounds,
        message_ids: conversation.message_ids,
        reply_ids: conversation.reply_ids,
      }),
    });
  }

  #recordRejection(at: string, reason: string, value: unknown): void {
    if (isRecord(value)) {
      this.#recordBareEvent("MESSAGE_REJECTED", at, {
        message_id: safeString(value.message_id),
        reply_to: safeString(value.reply_to),
        conversation_id: safeString(value.conversation_id),
        correlation_id: safeString(value.correlation_id),
        from: safeString(value.from),
        to: safeString(value.to),
        reason,
      });
      return;
    }
    this.#recordBareEvent("MESSAGE_REJECTED", at, { reason });
  }

  #recordMessageEvent(
    event: MessageBusAuditEventName,
    timestamp: string,
    envelope: MessageToCodex,
    extra: Partial<MessageBusAuditEvent> = {},
  ): void {
    const payload_hash = hashMessagePayload(envelope);
    const delivery_fingerprint =
      extra.delivery_fingerprint ??
      createEnvelopeFingerprint(envelope, payload_hash, extra.fromThreadId, extra.toThreadId, extra.state);
    this.#recordBareEvent(event, timestamp, {
      message_id: envelope.message_id,
      conversation_id: envelope.conversation_id,
      correlation_id: envelope.correlation_id,
      from: envelope.from,
      to: envelope.to,
      message_kind: envelope.kind,
      payload_hash,
      delivery_fingerprint,
      ...extra,
    });
  }

  #recordReplyEvent(
    event: MessageBusAuditEventName,
    timestamp: string,
    envelope: CodexMessageReply,
    extra: Partial<MessageBusAuditEvent> = {},
  ): void {
    const payload_hash = hashMessagePayload(envelope);
    const delivery_fingerprint =
      extra.delivery_fingerprint ??
      createEnvelopeFingerprint(envelope, payload_hash, extra.fromThreadId, extra.toThreadId, extra.state);
    this.#recordBareEvent(event, timestamp, {
      message_id: envelope.message_id,
      reply_to: envelope.reply_to,
      conversation_id: envelope.conversation_id,
      correlation_id: envelope.correlation_id,
      from: envelope.from,
      to: envelope.to,
      message_kind: envelope.kind,
      payload_hash,
      delivery_fingerprint,
      ...extra,
    });
  }

  #recordBareEvent(event: MessageBusAuditEventName, timestamp: string, extra: Partial<MessageBusAuditEvent> = {}): void {
    const auditEvent: MessageBusAuditEvent = { event, timestamp, ...extra };
    this.#auditEvents.push(auditEvent);
    this.ledger.record(createLedgerEntryFromAuditEvent(auditEvent));
  }
}

function createEnvelopeFingerprint(
  envelope: MessageToCodex | CodexMessageReply,
  payloadHash: string,
  fromThreadId?: string,
  toThreadId?: string,
  state?: string,
): string {
  return createDeliveryFingerprint({
    type: envelope.type,
    message_id: envelope.message_id,
    reply_to: "reply_to" in envelope ? envelope.reply_to : null,
    conversation_id: envelope.conversation_id,
    correlation_id: envelope.correlation_id,
    from: envelope.from,
    to: envelope.to,
    fromThreadId,
    toThreadId,
    kind: envelope.kind,
    state,
    payload_hash: payloadHash,
  });
}

function createLedgerEntryFromAuditEvent(event: MessageBusAuditEvent): Omit<MessageLedgerEntry, "entry_id"> {
  const state = ledgerStateFromAuditEvent(event);
  return {
    kind: ledgerKindFromAuditEvent(event),
    at: event.timestamp,
    message_id: event.message_id,
    reply_to: event.reply_to,
    conversation_id: event.conversation_id,
    correlation_id: event.correlation_id,
    from: event.from,
    to: event.to,
    fromThreadId: event.fromThreadId,
    toThreadId: event.toThreadId,
    message_kind: event.message_kind,
    state,
    round: event.round,
    round_count: event.round_count,
    max_rounds: event.max_rounds,
    payload_hash: event.payload_hash,
    delivery_fingerprint:
      event.delivery_fingerprint ??
      createDeliveryFingerprint({
        event: event.event,
        message_id: event.message_id,
        reply_to: event.reply_to,
        conversation_id: event.conversation_id,
        correlation_id: event.correlation_id,
        from: event.from,
        to: event.to,
        fromThreadId: event.fromThreadId,
        toThreadId: event.toThreadId,
        state,
        reason: event.reason,
      }),
    failure_reason: event.reason,
  };
}

function ledgerKindFromAuditEvent(event: MessageBusAuditEvent): MessageLedgerEntry["kind"] {
  switch (event.event) {
    case "MESSAGE_CAPTURED":
    case "MESSAGE_EXPIRED":
    case "MESSAGE_OBSERVED":
      return "MESSAGE";
    case "MESSAGE_ROUTED":
    case "REPLY_ROUTED":
    case "WORKER_RESUMED":
      return "ROUTE";
    case "REPLY_CAPTURED":
    case "REPLY_OBSERVED":
      return "REPLY";
    case "MESSAGE_REJECTED":
      return "REJECTION";
    case "CONVERSATION_BLOCKED":
    case "CHANNEL_DONE":
      return "CONVERSATION";
  }
}

function ledgerStateFromAuditEvent(event: MessageBusAuditEvent): MessageLedgerState {
  switch (event.event) {
    case "MESSAGE_CAPTURED":
      return "CAPTURED";
    case "MESSAGE_ROUTED":
      return "ROUTED";
    case "MESSAGE_OBSERVED":
    case "REPLY_OBSERVED":
      return "OBSERVED";
    case "REPLY_CAPTURED":
    case "REPLY_ROUTED":
    case "WORKER_RESUMED":
      return "REPLIED";
    case "MESSAGE_EXPIRED":
      return "EXPIRED";
    case "MESSAGE_REJECTED":
      return "REJECTED";
    case "CONVERSATION_BLOCKED":
      return "BLOCKED";
    case "CHANNEL_DONE":
      return "DONE";
  }
}

function filterLedgerSnapshot(snapshot: MessageLedgerSnapshot, conversationId: string): MessageLedgerSnapshot {
  const entries = snapshot.entries.filter((entry) => entry.conversation_id === conversationId);
  return {
    entries,
    messages: entries.filter((entry) => entry.kind === "MESSAGE"),
    routes: entries.filter((entry) => entry.kind === "ROUTE"),
    replies: entries.filter((entry) => entry.kind === "REPLY"),
    rejections: entries.filter((entry) => entry.kind === "REJECTION"),
    conversations: entries.filter((entry) => entry.kind === "CONVERSATION"),
  };
}

function assertReplyMatchesOriginal(reply: CodexMessageReply, original: MessageToCodex): void {
  if (reply.conversation_id !== original.conversation_id) {
    throw new Error("reply conversation_id does not match original message");
  }
  if (reply.correlation_id !== original.correlation_id) {
    throw new Error("reply correlation_id does not match original message");
  }
  if (reply.from !== original.to || reply.to !== original.from) {
    throw new Error("reply endpoints do not invert original message endpoints");
  }
}

function conversationClosedReason(conversation: ConversationRouteState): string {
  switch (conversation.status) {
    case "BLOCKED":
      return `conversation is blocked: ${conversation.conversation_id}`;
    case "DONE":
      return `conversation is done: ${conversation.conversation_id}`;
    case "FAILED":
      return `conversation is failed: ${conversation.conversation_id}`;
    case "ACTIVE":
      return `conversation is active: ${conversation.conversation_id}`;
  }
}

function nextRound(conversation: ConversationRouteState): number {
  return conversation.round_count + 1;
}

function isExpired(record: MessageBusMessageRecord, at: string): boolean {
  return Date.parse(at) >= Date.parse(record.expires_at);
}

function addMsIso(at: string, ms: number): string {
  return new Date(Date.parse(at) + ms).toISOString();
}

function nowIso(): string {
  return new Date().toISOString();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}
