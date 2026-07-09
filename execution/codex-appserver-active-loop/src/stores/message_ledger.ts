import { createHash } from "node:crypto";
import type { CodexMessageReply, MessageToCodex } from "../types/messages.js";

export type MessageLedgerEntryKind = "MESSAGE" | "ROUTE" | "REPLY" | "REJECTION" | "CONVERSATION";

export type MessageLedgerState =
  | "CAPTURED"
  | "ROUTED"
  | "REPLIED"
  | "OBSERVED"
  | "EXPIRED"
  | "FAILED"
  | "REJECTED"
  | "ACTIVE"
  | "DONE"
  | "BLOCKED";

export interface MessageLedgerEntry {
  readonly entry_id: string;
  readonly kind: MessageLedgerEntryKind;
  readonly at: string;
  readonly message_id?: string;
  readonly reply_to?: string;
  readonly conversation_id?: string;
  readonly correlation_id?: string;
  readonly from?: string;
  readonly to?: string;
  readonly fromThreadId?: string;
  readonly toThreadId?: string;
  readonly message_kind?: string;
  readonly state: MessageLedgerState;
  readonly round?: number;
  readonly round_count?: number;
  readonly max_rounds?: number;
  readonly payload_hash?: string;
  readonly delivery_fingerprint: string;
  readonly message_ids?: readonly string[];
  readonly reply_ids?: readonly string[];
  readonly failure_reason?: string;
}

export interface MessageLedgerSnapshot {
  readonly entries: readonly MessageLedgerEntry[];
  readonly messages: readonly MessageLedgerEntry[];
  readonly routes: readonly MessageLedgerEntry[];
  readonly replies: readonly MessageLedgerEntry[];
  readonly rejections: readonly MessageLedgerEntry[];
  readonly conversations: readonly MessageLedgerEntry[];
}

export interface ConversationSnapshotTrailEntry {
  readonly round?: number;
  readonly message_id?: string;
  readonly reply_to?: string;
  readonly conversation_id: string;
  readonly correlation_id?: string;
  readonly from?: string;
  readonly to?: string;
  readonly fromThreadId?: string;
  readonly toThreadId?: string;
  readonly payload_hash?: string;
  readonly state: MessageLedgerState;
  readonly timestamp: string;
}

export interface ConversationIdempotencyGuardSnapshot {
  readonly accepted_message_ids: readonly string[];
  readonly reply_to_ids: readonly string[];
  readonly correlation_ids: readonly string[];
  readonly duplicate_message_ids: readonly string[];
  readonly duplicate_reply_to_ids: readonly string[];
  readonly duplicate_correlation_ids: readonly string[];
  readonly in_flight_message_id?: string;
  readonly idempotency_ok: boolean;
  readonly ordering_ok: boolean;
  readonly guard_ok: boolean;
}

export interface ConversationDeliverySnapshot {
  readonly conversation_id: string;
  readonly status?: MessageLedgerState;
  readonly round_count?: number;
  readonly max_rounds?: number;
  readonly trail: readonly ConversationSnapshotTrailEntry[];
  readonly idempotency: ConversationIdempotencyGuardSnapshot;
}

export interface ConversationSnapshotIndex {
  readonly conversations: readonly ConversationDeliverySnapshot[];
  readonly by_conversation_id: Readonly<Record<string, ConversationDeliverySnapshot>>;
}

export interface ConversationSnapshotOptions {
  readonly recentTrailLimit?: number;
}

export interface MessageLedgerStore {
  record(entry: Omit<MessageLedgerEntry, "entry_id"> & { readonly entry_id?: string }): MessageLedgerEntry;
  snapshot(): MessageLedgerSnapshot;
}

export function createInMemoryMessageLedgerStore(): MessageLedgerStore {
  return new InMemoryMessageLedgerStore();
}

export function hashMessagePayload(envelope: MessageToCodex | CodexMessageReply): string {
  return hashCanonicalJson(envelope.payload);
}

export function createDeliveryFingerprint(value: unknown): string {
  return hashCanonicalJson(value);
}

export function hashCanonicalJson(value: unknown): string {
  return `sha256:${createHash("sha256").update(JSON.stringify(canonicalize(value)), "utf8").digest("hex").toUpperCase()}`;
}

export function buildConversationSnapshot(
  snapshot: MessageLedgerSnapshot,
  options: ConversationSnapshotOptions = {},
): ConversationSnapshotIndex {
  const entriesByConversation = new Map<string, MessageLedgerEntry[]>();
  for (const entry of snapshot.entries) {
    if (!entry.conversation_id) continue;
    const current = entriesByConversation.get(entry.conversation_id) ?? [];
    current.push(entry);
    entriesByConversation.set(entry.conversation_id, current);
  }

  const conversations = [...entriesByConversation.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([conversationId, entries]) => createConversationDeliverySnapshot(conversationId, entries, options));
  return {
    conversations,
    by_conversation_id: Object.fromEntries(conversations.map((conversation) => [conversation.conversation_id, conversation])),
  };
}

class InMemoryMessageLedgerStore implements MessageLedgerStore {
  readonly #entries: MessageLedgerEntry[] = [];

  record(entry: Omit<MessageLedgerEntry, "entry_id"> & { readonly entry_id?: string }): MessageLedgerEntry {
    const recorded: MessageLedgerEntry = {
      ...entry,
      entry_id: entry.entry_id ?? createDeliveryFingerprint(["ledger-entry", this.#entries.length + 1, entry]),
    };
    this.#entries.push(recorded);
    return recorded;
  }

  snapshot(): MessageLedgerSnapshot {
    return createMessageLedgerSnapshot(this.#entries);
  }
}

export function createMessageLedgerSnapshot(entries: readonly MessageLedgerEntry[]): MessageLedgerSnapshot {
  const snapshotEntries = [...entries];
  return {
    entries: snapshotEntries,
    messages: snapshotEntries.filter((entry) => entry.kind === "MESSAGE"),
    routes: snapshotEntries.filter((entry) => entry.kind === "ROUTE"),
    replies: snapshotEntries.filter((entry) => entry.kind === "REPLY"),
    rejections: snapshotEntries.filter((entry) => entry.kind === "REJECTION"),
    conversations: snapshotEntries.filter((entry) => entry.kind === "CONVERSATION"),
  };
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }
  if (!isRecord(value)) {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value)
      .filter(([, child]) => child !== undefined)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, child]) => [key, canonicalize(child)]),
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function createConversationDeliverySnapshot(
  conversationId: string,
  entries: readonly MessageLedgerEntry[],
  options: ConversationSnapshotOptions,
): ConversationDeliverySnapshot {
  const trail = entries.map((entry) => createTrailEntry(entry));
  const latestConversation = [...entries].reverse().find((entry) => entry.kind === "CONVERSATION");
  return {
    conversation_id: conversationId,
    status: latestConversation?.state,
    round_count: latestConversation?.round_count,
    max_rounds: latestConversation?.max_rounds,
    trail: applyRecentLimit(trail, options.recentTrailLimit),
    idempotency: createIdempotencyGuardSnapshot(entries, trail),
  };
}

function createTrailEntry(entry: MessageLedgerEntry): ConversationSnapshotTrailEntry {
  return {
    round: entry.round,
    message_id: entry.message_id,
    reply_to: entry.reply_to,
    conversation_id: entry.conversation_id ?? "",
    correlation_id: entry.correlation_id,
    from: entry.from,
    to: entry.to,
    fromThreadId: entry.fromThreadId,
    toThreadId: entry.toThreadId,
    payload_hash: entry.payload_hash,
    state: entry.state,
    timestamp: entry.at,
  };
}

function createIdempotencyGuardSnapshot(
  entries: readonly MessageLedgerEntry[],
  trail: readonly ConversationSnapshotTrailEntry[],
): ConversationIdempotencyGuardSnapshot {
  const acceptedMessageIds = compactStrings(
    entries
      .filter((entry) => (entry.kind === "MESSAGE" && entry.state === "CAPTURED") || entry.kind === "REPLY")
      .map((entry) => entry.message_id),
  );
  const replyToIds = compactStrings(
    entries
      .filter((entry) => entry.kind === "REPLY")
      .map((entry) => entry.reply_to),
  );
  const correlationIds = compactStrings(
    entries
      .filter((entry) => entry.kind === "MESSAGE" && entry.state === "CAPTURED")
      .map((entry) => entry.correlation_id),
  );
  const duplicateMessageIds = duplicates(acceptedMessageIds);
  const duplicateReplyToIds = duplicates(replyToIds);
  const duplicateCorrelationIds = duplicates(correlationIds);
  const latestMessageStates = latestOutboundMessageStates(entries);
  const inFlight = [...latestMessageStates.entries()].find(([, state]) =>
    state === "CAPTURED" || state === "ROUTED" || state === "OBSERVED"
  )?.[0];
  const idempotencyOk =
    duplicateMessageIds.length === 0 && duplicateReplyToIds.length === 0 && duplicateCorrelationIds.length === 0;
  const orderingOk = isOrderedTrail(trail);
  return {
    accepted_message_ids: acceptedMessageIds,
    reply_to_ids: replyToIds,
    correlation_ids: correlationIds,
    duplicate_message_ids: duplicateMessageIds,
    duplicate_reply_to_ids: duplicateReplyToIds,
    duplicate_correlation_ids: duplicateCorrelationIds,
    in_flight_message_id: inFlight,
    idempotency_ok: idempotencyOk,
    ordering_ok: orderingOk,
    guard_ok: idempotencyOk && orderingOk,
  };
}

function latestOutboundMessageStates(entries: readonly MessageLedgerEntry[]): Map<string, MessageLedgerState> {
  const states = new Map<string, MessageLedgerState>();
  for (const entry of entries) {
    if (entry.kind === "MESSAGE" && entry.message_id) {
      states.set(entry.message_id, entry.state);
    }
    if (entry.kind === "ROUTE" && entry.message_id && !entry.reply_to) {
      states.set(entry.message_id, entry.state);
    }
    if (entry.kind === "REPLY" && entry.reply_to) {
      states.set(entry.reply_to, "REPLIED");
    }
    if (entry.kind === "CONVERSATION" && entry.message_id && entry.state === "BLOCKED") {
      states.set(entry.message_id, "FAILED");
    }
  }
  return states;
}

function isOrderedTrail(trail: readonly ConversationSnapshotTrailEntry[]): boolean {
  let previousTimestamp = Number.NEGATIVE_INFINITY;
  let previousRound = Number.NEGATIVE_INFINITY;
  for (const entry of trail) {
    const timestamp = Date.parse(entry.timestamp);
    if (Number.isFinite(timestamp) && timestamp < previousTimestamp) return false;
    if (Number.isFinite(timestamp)) previousTimestamp = timestamp;
    if (typeof entry.round === "number") {
      if (entry.round < previousRound) return false;
      previousRound = entry.round;
    }
  }
  return true;
}

function applyRecentLimit(
  trail: readonly ConversationSnapshotTrailEntry[],
  recentTrailLimit: number | undefined,
): readonly ConversationSnapshotTrailEntry[] {
  if (recentTrailLimit === undefined) return trail;
  if (!Number.isInteger(recentTrailLimit) || recentTrailLimit <= 0) {
    throw new Error("recentTrailLimit must be a positive integer when provided");
  }
  return trail.slice(-recentTrailLimit);
}

function compactStrings(values: readonly (string | undefined)[]): readonly string[] {
  return values.filter((value): value is string => typeof value === "string" && value.length > 0);
}

function duplicates(values: readonly string[]): readonly string[] {
  const seen = new Set<string>();
  const duplicate = new Set<string>();
  for (const value of values) {
    if (seen.has(value)) {
      duplicate.add(value);
      continue;
    }
    seen.add(value);
  }
  return [...duplicate].sort();
}
