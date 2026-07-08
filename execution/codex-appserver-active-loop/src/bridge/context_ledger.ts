import { createHash } from "node:crypto";

export const contextLedgerEventTypes = [
  "TASK_OPENED",
  "MESSAGE_RECORDED",
  "SNAPSHOT_BOUND",
  "REVIEW_REQUESTED",
  "FINDING_RECORDED",
  "RECEIPT_BOUND",
  "TASK_CLOSED",
  "BLOCKED",
] as const;

export const contextLedgerRoles = ["commander", "bridge", "worker", "reviewer", "user", "system"] as const;

export type ContextLedgerEventType = (typeof contextLedgerEventTypes)[number];
export type ContextLedgerRole = (typeof contextLedgerRoles)[number];

export interface ContextLedgerEntry {
  readonly ledgerVersion: 1;
  readonly taskId: string;
  readonly eventId: string;
  readonly eventType: ContextLedgerEventType;
  readonly at: string;
  readonly agentId: string;
  readonly role: ContextLedgerRole;
  readonly source: string;
  readonly frontendOrSession: string;
  readonly contentHash: string;
  readonly contentBytes: number;
  readonly artifactRef?: string;
  readonly snapshotId?: string;
  readonly visibility: "record_only";
  readonly autoInject: false;
  readonly contextPatch: "disabled";
  readonly tags: readonly string[];
}

export interface CreateContextLedgerEntryInput {
  readonly taskId: string;
  readonly eventId: string;
  readonly eventType: ContextLedgerEventType;
  readonly agentId: string;
  readonly role: ContextLedgerRole;
  readonly source: string;
  readonly frontendOrSession: string;
  readonly content: string;
  readonly artifactRef?: string;
  readonly snapshotId?: string;
  readonly tags?: readonly string[];
  readonly at?: string;
}

const allowedContextLedgerKeys = [
  "ledgerVersion",
  "taskId",
  "eventId",
  "eventType",
  "at",
  "agentId",
  "role",
  "source",
  "frontendOrSession",
  "contentHash",
  "contentBytes",
  "artifactRef",
  "snapshotId",
  "visibility",
  "autoInject",
  "contextPatch",
  "tags",
] as const;

const rawContentFieldNames = new Set(["content", "raw", "rawContent", "message", "messages", "prompt", "response", "text"]);

const rawSecretPatterns = [
  /\bBearer\s+[A-Za-z0-9._~+/=-]+/i,
  /\bsk-[A-Za-z0-9._-]+/,
  /\bOPENAI_API_KEY\s*=/i,
  /\bAuthorization\s*:/i,
  /BEGIN [A-Z ]*PRIVATE KEY/i,
] as const;

export function createContextLedgerEntry(input: CreateContextLedgerEntryInput): ContextLedgerEntry {
  assertSafeLedgerId(input.taskId, "taskId");
  assertSafeLedgerId(input.eventId, "eventId");
  assertSafeLedgerText(input.agentId, "agentId");
  assertSafeLedgerText(input.source, "source");
  assertSafeLedgerText(input.frontendOrSession, "frontendOrSession");
  assertSafeLedgerText(input.content, "content");
  if (input.artifactRef !== undefined) {
    assertSafeLedgerText(input.artifactRef, "artifactRef");
  }
  if (input.snapshotId !== undefined) {
    assertSafeLedgerId(input.snapshotId, "snapshotId");
  }

  const entry: ContextLedgerEntry = {
    ledgerVersion: 1,
    taskId: input.taskId,
    eventId: input.eventId,
    eventType: input.eventType,
    at: input.at ?? new Date().toISOString(),
    agentId: input.agentId,
    role: input.role,
    source: input.source,
    frontendOrSession: input.frontendOrSession,
    contentHash: hashLedgerContent(input.content),
    contentBytes: Buffer.byteLength(input.content, "utf8"),
    artifactRef: input.artifactRef,
    snapshotId: input.snapshotId,
    visibility: "record_only",
    autoInject: false,
    contextPatch: "disabled",
    tags: [...(input.tags ?? [])],
  };

  assertRecordOnlyContextLedgerEntry(entry);
  return entry;
}

export function hashLedgerContent(content: string): string {
  assertSafeLedgerText(content, "content");
  return `sha256:${createHash("sha256").update(content, "utf8").digest("hex").toUpperCase()}`;
}

export function validateContextLedgerEntry(value: unknown): value is ContextLedgerEntry {
  if (!isRecord(value) || containsRawContentField(value) || !hasOnlyKeys(value, allowedContextLedgerKeys)) {
    return false;
  }

  return (
    value.ledgerVersion === 1 &&
    isSafeLedgerId(value.taskId) &&
    isSafeLedgerId(value.eventId) &&
    isOneOf(value.eventType, contextLedgerEventTypes) &&
    isIsoTimestamp(value.at) &&
    isSafeLedgerText(value.agentId) &&
    isOneOf(value.role, contextLedgerRoles) &&
    isSafeLedgerText(value.source) &&
    isSafeLedgerText(value.frontendOrSession) &&
    typeof value.contentHash === "string" &&
    /^sha256:[A-F0-9]{64}$/.test(value.contentHash) &&
    typeof value.contentBytes === "number" &&
    Number.isInteger(value.contentBytes) &&
    value.contentBytes >= 0 &&
    (value.artifactRef === undefined || isSafeLedgerText(value.artifactRef)) &&
    (value.snapshotId === undefined || isSafeLedgerId(value.snapshotId)) &&
    value.visibility === "record_only" &&
    value.autoInject === false &&
    value.contextPatch === "disabled" &&
    isSafeTagArray(value.tags)
  );
}

export function assertRecordOnlyContextLedgerEntry(entry: unknown): asserts entry is ContextLedgerEntry {
  if (!validateContextLedgerEntry(entry)) {
    throw new Error("context ledger entries must be strict record-only metadata records");
  }
}

export function isDuplicateContextLedgerEntry(left: ContextLedgerEntry, right: ContextLedgerEntry): boolean {
  return (
    left.agentId === right.agentId &&
    left.role === right.role &&
    left.source === right.source &&
    left.frontendOrSession === right.frontendOrSession &&
    left.contentHash === right.contentHash
  );
}

function containsRawContentField(value: Record<string, unknown>): boolean {
  return Object.keys(value).some((key) => rawContentFieldNames.has(key));
}

function assertSafeLedgerId(value: string, fieldName: string): void {
  if (!isSafeLedgerId(value)) {
    throw new Error(`unsafe context ledger ${fieldName}`);
  }
}

function isSafeLedgerId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9._:-]{1,160}$/.test(value);
}

function assertSafeLedgerText(value: string, fieldName: string): void {
  if (!isSafeLedgerText(value)) {
    throw new Error(`unsafe context ledger ${fieldName}`);
  }
}

function isSafeLedgerText(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= 1000 &&
    !value.includes("\0") &&
    rawSecretPatterns.every((pattern) => !pattern.test(value))
  );
}

function isSafeTagArray(value: unknown): value is readonly string[] {
  return (
    Array.isArray(value) &&
    value.every((tag) => typeof tag === "string" && /^[A-Za-z0-9._:-]{1,80}$/.test(tag))
  );
}

function isIsoTimestamp(value: unknown): value is string {
  return typeof value === "string" && !Number.isNaN(Date.parse(value));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isOneOf<T extends readonly string[]>(value: unknown, allowed: T): value is T[number] {
  return typeof value === "string" && (allowed as readonly string[]).includes(value);
}

function hasOnlyKeys(value: Record<string, unknown>, allowed: readonly string[]): boolean {
  const allowedSet = new Set(allowed);
  return Object.keys(value).every((key) => allowedSet.has(key));
}
