import type { ContextLedgerEntry, ContextLedgerEventType, ContextLedgerRole } from "./context_ledger.js";

export type ContextPromotionStatus = "BLOCKED_BY_DEFAULT" | "APPROVED_FOR_PACKET_USE";
export type WorkerPromptUse = "BLOCKED" | "APPROVED_PACKET_ONLY";
export type PromotionApproverRole = "commander" | "reviewer";

export interface ContextPromotionQuery {
  readonly taskId?: string;
  readonly snapshotId?: string;
  readonly role?: ContextLedgerRole;
  readonly tag?: string;
  readonly artifactRef?: string;
  readonly contentHash?: string;
  readonly eventType?: ContextLedgerEventType;
}

export interface ContextPacketEntryRef {
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
  readonly tags: readonly string[];
}

export interface ContextPromotionApproval {
  readonly approvedByRole: PromotionApproverRole;
  readonly approvedByAgentId: string;
  readonly approvedAt: string;
  readonly reason: string;
  readonly evidence: readonly string[];
}

export interface ContextPromotionPacket {
  readonly packetVersion: 1;
  readonly packetId: string;
  readonly createdAt: string;
  readonly sourceLedgerTaskId: string;
  readonly query: ContextPromotionQuery;
  readonly status: ContextPromotionStatus;
  readonly workerPromptUse: WorkerPromptUse;
  readonly autoInject: false;
  readonly rawContentIncluded: false;
  readonly entryRefs: readonly ContextPacketEntryRef[];
  readonly artifactRefs: readonly string[];
  readonly snapshotIds: readonly string[];
  readonly approval?: ContextPromotionApproval;
  readonly boundary: {
    readonly approvalRequired: true;
    readonly defaultDecision: "BLOCKED_BY_DEFAULT";
    readonly autoInjection: "DISABLED";
    readonly directRealRepo: "BLOCKED";
    readonly workerCwd: "SNAPSHOT_ONLY";
  };
}

export interface BuildContextPromotionPacketInput {
  readonly packetId: string;
  readonly sourceLedgerTaskId: string;
  readonly entries: readonly ContextLedgerEntry[];
  readonly query: ContextPromotionQuery;
  readonly createdAt?: string;
}

export interface ApproveContextPromotionPacketInput {
  readonly approvedByRole: PromotionApproverRole;
  readonly approvedByAgentId: string;
  readonly reason: string;
  readonly evidence: readonly string[];
  readonly approvedAt?: string;
}

const allowedPacketKeys = [
  "packetVersion",
  "packetId",
  "createdAt",
  "sourceLedgerTaskId",
  "query",
  "status",
  "workerPromptUse",
  "autoInject",
  "rawContentIncluded",
  "entryRefs",
  "artifactRefs",
  "snapshotIds",
  "approval",
  "boundary",
] as const;

const rawContentFieldNames = new Set(["content", "raw", "rawContent", "message", "messages", "prompt", "response", "text"]);

export function queryContextLedger(
  entries: readonly ContextLedgerEntry[],
  query: ContextPromotionQuery,
): readonly ContextLedgerEntry[] {
  assertSafePromotionQuery(query);
  return entries.filter((entry) => {
    if (query.taskId !== undefined && entry.taskId !== query.taskId) return false;
    if (query.snapshotId !== undefined && entry.snapshotId !== query.snapshotId) return false;
    if (query.role !== undefined && entry.role !== query.role) return false;
    if (query.tag !== undefined && !entry.tags.includes(query.tag)) return false;
    if (query.artifactRef !== undefined && entry.artifactRef !== query.artifactRef) return false;
    if (query.contentHash !== undefined && entry.contentHash !== query.contentHash) return false;
    if (query.eventType !== undefined && entry.eventType !== query.eventType) return false;
    return true;
  });
}

export function buildContextPromotionPacket(input: BuildContextPromotionPacketInput): ContextPromotionPacket {
  assertSafePromotionId(input.packetId, "packetId");
  assertSafePromotionId(input.sourceLedgerTaskId, "sourceLedgerTaskId");
  assertSafePromotionQuery(input.query);

  const matches = queryContextLedger(input.entries, input.query);
  if (matches.length === 0) {
    throw new Error("context promotion packet requires at least one ledger entry");
  }

  const entryRefs = matches.map(toEntryRef).sort((a, b) => a.at.localeCompare(b.at) || a.eventId.localeCompare(b.eventId));
  const packet: ContextPromotionPacket = {
    packetVersion: 1,
    packetId: input.packetId,
    createdAt: input.createdAt ?? new Date().toISOString(),
    sourceLedgerTaskId: input.sourceLedgerTaskId,
    query: normalizeQuery(input.query),
    status: "BLOCKED_BY_DEFAULT",
    workerPromptUse: "BLOCKED",
    autoInject: false,
    rawContentIncluded: false,
    entryRefs,
    artifactRefs: uniqueSorted(entryRefs.flatMap((entry) => (entry.artifactRef ? [entry.artifactRef] : []))),
    snapshotIds: uniqueSorted(entryRefs.flatMap((entry) => (entry.snapshotId ? [entry.snapshotId] : []))),
    boundary: {
      approvalRequired: true,
      defaultDecision: "BLOCKED_BY_DEFAULT",
      autoInjection: "DISABLED",
      directRealRepo: "BLOCKED",
      workerCwd: "SNAPSHOT_ONLY",
    },
  };

  assertContextPromotionPacket(packet);
  return packet;
}

export function approveContextPromotionPacket(
  packet: ContextPromotionPacket,
  input: ApproveContextPromotionPacketInput,
): ContextPromotionPacket {
  assertContextPromotionPacket(packet);
  assertPromotionApprovalInput(input);
  const approved: ContextPromotionPacket = {
    ...packet,
    status: "APPROVED_FOR_PACKET_USE",
    workerPromptUse: "APPROVED_PACKET_ONLY",
    autoInject: false,
    rawContentIncluded: false,
    approval: {
      approvedByRole: input.approvedByRole,
      approvedByAgentId: input.approvedByAgentId,
      approvedAt: input.approvedAt ?? new Date().toISOString(),
      reason: input.reason,
      evidence: [...input.evidence],
    },
  };
  assertContextPromotionPacket(approved);
  return approved;
}

export function validateContextPromotionPacket(value: unknown): value is ContextPromotionPacket {
  if (!isRecord(value) || containsRawContentField(value) || !hasOnlyKeys(value, allowedPacketKeys)) {
    return false;
  }
  if (value.packetVersion !== 1 || !isSafePromotionId(value.packetId) || !isIsoTimestamp(value.createdAt)) return false;
  if (!isSafePromotionId(value.sourceLedgerTaskId) || !isPromotionQuery(value.query)) return false;
  if (value.status !== "BLOCKED_BY_DEFAULT" && value.status !== "APPROVED_FOR_PACKET_USE") return false;
  if (value.workerPromptUse !== "BLOCKED" && value.workerPromptUse !== "APPROVED_PACKET_ONLY") return false;
  if (value.autoInject !== false || value.rawContentIncluded !== false) return false;
  if (!Array.isArray(value.entryRefs) || !value.entryRefs.every(isEntryRef)) return false;
  if (!isSafeStringArray(value.artifactRefs) || !isSafeStringArray(value.snapshotIds)) return false;
  if (!isBoundary(value.boundary)) return false;

  if (value.status === "BLOCKED_BY_DEFAULT") {
    return value.workerPromptUse === "BLOCKED" && value.approval === undefined;
  }
  return value.workerPromptUse === "APPROVED_PACKET_ONLY" && isPromotionApproval(value.approval);
}

export function assertContextPromotionPacket(value: unknown): asserts value is ContextPromotionPacket {
  if (!validateContextPromotionPacket(value)) {
    throw new Error("context promotion packet must be blocked by default and metadata-only");
  }
}

function toEntryRef(entry: ContextLedgerEntry): ContextPacketEntryRef {
  return {
    eventId: entry.eventId,
    eventType: entry.eventType,
    at: entry.at,
    agentId: entry.agentId,
    role: entry.role,
    source: entry.source,
    frontendOrSession: entry.frontendOrSession,
    contentHash: entry.contentHash,
    contentBytes: entry.contentBytes,
    artifactRef: entry.artifactRef,
    snapshotId: entry.snapshotId,
    tags: [...entry.tags],
  };
}

function normalizeQuery(query: ContextPromotionQuery): ContextPromotionQuery {
  return Object.fromEntries(Object.entries(query).filter(([, value]) => value !== undefined)) as ContextPromotionQuery;
}

function assertSafePromotionQuery(query: ContextPromotionQuery): void {
  if (!isPromotionQuery(query)) {
    throw new Error("unsafe context promotion query");
  }
}

function isPromotionQuery(value: unknown): value is ContextPromotionQuery {
  if (!isRecord(value) || containsRawContentField(value)) return false;
  const allowed = ["taskId", "snapshotId", "role", "tag", "artifactRef", "contentHash", "eventType"];
  if (!hasOnlyKeys(value, allowed)) return false;
  return (
    (value.taskId === undefined || isSafePromotionId(value.taskId)) &&
    (value.snapshotId === undefined || isSafePromotionId(value.snapshotId)) &&
    (value.role === undefined || isSafeString(value.role)) &&
    (value.tag === undefined || isSafePromotionId(value.tag)) &&
    (value.artifactRef === undefined || isSafeString(value.artifactRef)) &&
    (value.contentHash === undefined || (typeof value.contentHash === "string" && /^sha256:[A-F0-9]{64}$/.test(value.contentHash))) &&
    (value.eventType === undefined || isSafeString(value.eventType))
  );
}

function assertPromotionApprovalInput(input: ApproveContextPromotionPacketInput): void {
  if (input.approvedByRole !== "commander" && input.approvedByRole !== "reviewer") {
    throw new Error("context promotion approval requires commander or reviewer");
  }
  if (!isSafeString(input.approvedByAgentId) || !isSafeString(input.reason) || !isSafeStringArray(input.evidence) || input.evidence.length === 0) {
    throw new Error("context promotion approval requires safe approver, reason, and evidence");
  }
  if (input.approvedAt !== undefined && !isIsoTimestamp(input.approvedAt)) {
    throw new Error("context promotion approval timestamp is invalid");
  }
}

function isPromotionApproval(value: unknown): value is ContextPromotionApproval {
  return (
    isRecord(value) &&
    hasOnlyKeys(value, ["approvedByRole", "approvedByAgentId", "approvedAt", "reason", "evidence"]) &&
    (value.approvedByRole === "commander" || value.approvedByRole === "reviewer") &&
    isSafeString(value.approvedByAgentId) &&
    isIsoTimestamp(value.approvedAt) &&
    isSafeString(value.reason) &&
    isSafeStringArray(value.evidence) &&
    value.evidence.length > 0
  );
}

function isEntryRef(value: unknown): value is ContextPacketEntryRef {
  return (
    isRecord(value) &&
    !containsRawContentField(value) &&
    hasOnlyKeys(value, [
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
      "tags",
    ]) &&
    isSafePromotionId(value.eventId) &&
    isSafeString(value.eventType) &&
    isIsoTimestamp(value.at) &&
    isSafeString(value.agentId) &&
    isSafeString(value.role) &&
    isSafeString(value.source) &&
    isSafeString(value.frontendOrSession) &&
    typeof value.contentHash === "string" &&
    /^sha256:[A-F0-9]{64}$/.test(value.contentHash) &&
    typeof value.contentBytes === "number" &&
    Number.isInteger(value.contentBytes) &&
    value.contentBytes >= 0 &&
    (value.artifactRef === undefined || isSafeString(value.artifactRef)) &&
    (value.snapshotId === undefined || isSafePromotionId(value.snapshotId)) &&
    isSafeStringArray(value.tags)
  );
}

function isBoundary(value: unknown): value is ContextPromotionPacket["boundary"] {
  return (
    isRecord(value) &&
    hasOnlyKeys(value, ["approvalRequired", "defaultDecision", "autoInjection", "directRealRepo", "workerCwd"]) &&
    value.approvalRequired === true &&
    value.defaultDecision === "BLOCKED_BY_DEFAULT" &&
    value.autoInjection === "DISABLED" &&
    value.directRealRepo === "BLOCKED" &&
    value.workerCwd === "SNAPSHOT_ONLY"
  );
}

function containsRawContentField(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.some((item) => containsRawContentField(item));
  }
  if (!isRecord(value)) {
    return false;
  }
  return Object.entries(value).some(([key, nested]) => rawContentFieldNames.has(key) || containsRawContentField(nested));
}

function assertSafePromotionId(value: string, fieldName: string): void {
  if (!isSafePromotionId(value)) {
    throw new Error(`unsafe context promotion ${fieldName}`);
  }
}

function isSafePromotionId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9._:-]{1,180}$/.test(value);
}

function isSafeString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= 1000 && !value.includes("\0");
}

function isSafeStringArray(value: unknown): value is readonly string[] {
  return Array.isArray(value) && value.every(isSafeString);
}

function isIsoTimestamp(value: unknown): value is string {
  return typeof value === "string" && !Number.isNaN(Date.parse(value));
}

function uniqueSorted(values: readonly string[]): readonly string[] {
  return [...new Set(values)].sort();
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(value: Record<string, unknown>, allowed: readonly string[]): boolean {
  const allowedSet = new Set(allowed);
  return Object.keys(value).every((key) => allowedSet.has(key));
}
