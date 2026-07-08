import type { JsonValue } from "../generated/appserver/serde_json/JsonValue";
import type { JsonSchema } from "../bridge/event_contracts.js";

export type ThreadRoleId = string;
export type CodexPeerRole = ThreadRoleId;

export const codexGenericMessageKinds = [
  "question",
  "answer",
  "request_review",
  "request_verification",
  "request_decision",
  "decision",
  "notice",
  "status",
  "block_notice",
  "clarification",
  "block",
] as const;
export type CodexGenericMessageKind = (typeof codexGenericMessageKinds)[number];

export const codexOutboundMessageKinds = codexGenericMessageKinds;
export type CodexOutboundMessageKind = (typeof codexOutboundMessageKinds)[number];

export const codexReplyKinds = codexGenericMessageKinds;
export type CodexReplyKind = (typeof codexReplyKinds)[number];
export const rolePattern = /^[A-Za-z][A-Za-z0-9_-]{0,63}$/;

export interface MessagePayload {
  readonly question: string;
  readonly context: readonly string[];
  readonly expected_response: string;
}

export interface ReplyPayload {
  readonly decision: string;
  readonly reason: string;
  readonly next_instruction: string;
}

export interface MessageToCodex {
  readonly type: "MESSAGE_TO_CODEX";
  readonly message_id: string;
  readonly correlation_id: string;
  readonly conversation_id: string;
  readonly from: CodexPeerRole;
  readonly to: CodexPeerRole;
  readonly kind: CodexOutboundMessageKind;
  readonly payload: MessagePayload;
}

export interface CodexMessageReply {
  readonly type: "CODEX_MESSAGE_REPLY";
  readonly message_id: string;
  readonly reply_to: string;
  readonly correlation_id: string;
  readonly conversation_id: string;
  readonly from: CodexPeerRole;
  readonly to: CodexPeerRole;
  readonly kind: CodexReplyKind;
  readonly payload: ReplyPayload;
}

export type CodexChannelMessage = MessageToCodex | CodexMessageReply;

export type MessageValidationResult<TValue> =
  | { readonly ok: true; readonly value: TValue }
  | { readonly ok: false; readonly error: string };

const stringArraySchema = {
  type: "array",
  items: { type: "string" },
} satisfies JsonSchema;

const messagePayloadSchema = {
  type: "object",
  additionalProperties: false,
  required: ["question", "context", "expected_response"],
  properties: {
    question: { type: "string" },
    context: stringArraySchema,
    expected_response: { type: "string" },
  },
} satisfies JsonSchema;

const replyPayloadSchema = {
  type: "object",
  additionalProperties: false,
  required: ["decision", "reason", "next_instruction"],
  properties: {
    decision: { type: "string" },
    reason: { type: "string" },
    next_instruction: { type: "string" },
  },
} satisfies JsonSchema;

export const messageToCodexSchema = {
  type: "object",
  additionalProperties: false,
  required: ["type", "message_id", "correlation_id", "conversation_id", "from", "to", "kind", "payload"],
  properties: {
    type: { type: "string", const: "MESSAGE_TO_CODEX" },
    message_id: { type: "string" },
    correlation_id: { type: "string" },
    conversation_id: { type: "string" },
    from: { type: "string", pattern: rolePattern.source },
    to: { type: "string", pattern: rolePattern.source },
    kind: { enum: [...codexOutboundMessageKinds] },
    payload: messagePayloadSchema,
  },
} satisfies JsonSchema;

export const codexMessageReplySchema = {
  type: "object",
  additionalProperties: false,
  required: ["type", "message_id", "reply_to", "correlation_id", "conversation_id", "from", "to", "kind", "payload"],
  properties: {
    type: { type: "string", const: "CODEX_MESSAGE_REPLY" },
    message_id: { type: "string" },
    reply_to: { type: "string" },
    correlation_id: { type: "string" },
    conversation_id: { type: "string" },
    from: { type: "string", pattern: rolePattern.source },
    to: { type: "string", pattern: rolePattern.source },
    kind: { enum: [...codexReplyKinds] },
    payload: replyPayloadSchema,
  },
} satisfies JsonSchema;

export function isMessagePayload(value: unknown): value is MessagePayload {
  return validateMessagePayload(value).ok;
}

export function isReplyPayload(value: unknown): value is ReplyPayload {
  return validateReplyPayload(value).ok;
}

export function isMessageToCodex(value: unknown): value is MessageToCodex {
  return validateMessageToCodex(value).ok;
}

export function isCodexMessageReply(value: unknown): value is CodexMessageReply {
  return validateCodexMessageReply(value).ok;
}

export function validateMessageToCodex(value: unknown): MessageValidationResult<MessageToCodex> {
  if (!isRecord(value)) return fail("MESSAGE_TO_CODEX must be an object");
  const keyError = validateAllowedKeys(value, baseMessageKeys, "MESSAGE_TO_CODEX");
  if (keyError) return fail(keyError);
  if (value.type !== "MESSAGE_TO_CODEX") return fail("MESSAGE_TO_CODEX type must be MESSAGE_TO_CODEX");
  const messageId = validateRequiredId(value, "message_id");
  if (messageId) return fail(messageId);
  const correlationId = validateRequiredId(value, "correlation_id");
  if (correlationId) return fail(correlationId);
  const conversationId = validateRequiredId(value, "conversation_id");
  if (conversationId) return fail(conversationId);
  const from = validateRole(value.from, "from");
  if (from) return fail(from);
  const to = validateRole(value.to, "to");
  if (to) return fail(to);
  if (value.from === value.to) return fail("message endpoints must not be identical");
  if (!isOneOf(value.kind, codexOutboundMessageKinds)) {
    return fail(`unknown outbound message kind: ${String(value.kind)}`);
  }
  const payload = validateMessagePayload(value.payload);
  if (!payload.ok) return fail(payload.error);
  return { ok: true, value: value as unknown as MessageToCodex };
}

export function validateCodexMessageReply(value: unknown): MessageValidationResult<CodexMessageReply> {
  if (!isRecord(value)) return fail("CODEX_MESSAGE_REPLY must be an object");
  const keyError = validateAllowedKeys(value, [...baseMessageKeys, "reply_to"], "CODEX_MESSAGE_REPLY");
  if (keyError) return fail(keyError);
  if (value.type !== "CODEX_MESSAGE_REPLY") return fail("CODEX_MESSAGE_REPLY type must be CODEX_MESSAGE_REPLY");
  const messageId = validateRequiredId(value, "message_id");
  if (messageId) return fail(messageId);
  const replyTo = validateRequiredId(value, "reply_to");
  if (replyTo) return fail(replyTo);
  const correlationId = validateRequiredId(value, "correlation_id");
  if (correlationId) return fail(correlationId);
  const conversationId = validateRequiredId(value, "conversation_id");
  if (conversationId) return fail(conversationId);
  const from = validateRole(value.from, "from");
  if (from) return fail(from);
  const to = validateRole(value.to, "to");
  if (to) return fail(to);
  if (value.from === value.to) return fail("reply endpoints must not be identical");
  if (!isOneOf(value.kind, codexReplyKinds)) {
    return fail(`unknown reply kind: ${String(value.kind)}`);
  }
  const payload = validateReplyPayload(value.payload);
  if (!payload.ok) return fail(payload.error);
  return { ok: true, value: value as unknown as CodexMessageReply };
}

export function assertMessageToCodex(value: unknown): asserts value is MessageToCodex {
  const result = validateMessageToCodex(value);
  if (!result.ok) throw new Error(result.error);
}

export function assertCodexMessageReply(value: unknown): asserts value is CodexMessageReply {
  const result = validateCodexMessageReply(value);
  if (!result.ok) throw new Error(result.error);
}

function validateMessagePayload(value: unknown): MessageValidationResult<MessagePayload> {
  if (!isRecord(value)) return fail("MESSAGE_TO_CODEX payload must be an object");
  const keyError = validateAllowedKeys(value, ["question", "context", "expected_response"], "MESSAGE_TO_CODEX payload");
  if (keyError) return fail(keyError);
  if (!isNonEmptyString(value.question)) return fail("MESSAGE_TO_CODEX payload.question must be a non-empty string");
  if (!Array.isArray(value.context) || !value.context.every((item) => typeof item === "string")) {
    return fail("MESSAGE_TO_CODEX payload.context must be an array of strings");
  }
  if (!isNonEmptyString(value.expected_response)) {
    return fail("MESSAGE_TO_CODEX payload.expected_response must be a non-empty string");
  }
  return { ok: true, value: value as unknown as MessagePayload };
}

function validateReplyPayload(value: unknown): MessageValidationResult<ReplyPayload> {
  if (!isRecord(value)) return fail("CODEX_MESSAGE_REPLY payload must be an object");
  const keyError = validateAllowedKeys(value, ["decision", "reason", "next_instruction"], "CODEX_MESSAGE_REPLY payload");
  if (keyError) return fail(keyError);
  if (!isNonEmptyString(value.decision)) return fail("CODEX_MESSAGE_REPLY payload.decision must be a non-empty string");
  if (!isNonEmptyString(value.reason)) return fail("CODEX_MESSAGE_REPLY payload.reason must be a non-empty string");
  if (typeof value.next_instruction !== "string") {
    return fail("CODEX_MESSAGE_REPLY payload.next_instruction must be a string");
  }
  return { ok: true, value: value as unknown as ReplyPayload };
}

function validateRequiredId(value: Record<string, unknown>, field: string): string | undefined {
  if (!(field in value)) return `${field} is required`;
  if (typeof value[field] !== "string") return `${field} must be a string`;
  if (value[field].trim() === "") return `${field} must be a non-empty string`;
  if (!/^[A-Za-z0-9._:-]{1,200}$/.test(value[field])) return `${field} contains unsafe characters`;
  return undefined;
}

function validateRole(value: unknown, field: "from" | "to"): string | undefined {
  if (typeof value !== "string") return `${field} must be a role string`;
  if (value.trim() === "") return `${field} must be a non-empty role string`;
  if (!rolePattern.test(value)) return `${field} contains unsafe role characters`;
  return undefined;
}

function validateAllowedKeys(value: Record<string, unknown>, allowed: readonly string[], label: string): string | undefined {
  const allowedSet = new Set(allowed);
  const unsupported = Object.keys(value).find((key) => !allowedSet.has(key));
  return unsupported ? `${label} has unsupported field: ${unsupported}` : undefined;
}

function fail<TValue>(error: string): MessageValidationResult<TValue> {
  return { ok: false, error };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isOneOf<T extends readonly string[]>(value: unknown, allowed: T): value is T[number] {
  return typeof value === "string" && (allowed as readonly string[]).includes(value);
}

export function isJsonValue(value: unknown): value is JsonValue {
  if (value === null) return true;
  switch (typeof value) {
    case "string":
    case "number":
    case "boolean":
      return true;
    case "object":
      return Array.isArray(value)
        ? value.every(isJsonValue)
        : isRecord(value) && Object.values(value).every(isJsonValue);
    default:
      return false;
  }
}

const baseMessageKeys = ["type", "message_id", "correlation_id", "conversation_id", "from", "to", "kind", "payload"] as const;
