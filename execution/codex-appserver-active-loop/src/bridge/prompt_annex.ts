import type { ContextLedgerEventType, ContextLedgerRole } from "./context_ledger.js";
import { assertContextPromotionPacket, type ContextPromotionPacket } from "./context_promotion.js";
import {
  assertPromotionApprovalReceipt,
  verifyPromotionApprovalReceiptForPacket,
  type PromotionApprovalReceipt,
} from "./promotion_approval.js";

export interface PromptAnnexEntrySummary {
  readonly eventId: string;
  readonly eventType: ContextLedgerEventType;
  readonly role: ContextLedgerRole;
  readonly source: string;
  readonly frontendOrSession: string;
  readonly contentHash: string;
  readonly artifactRef?: string;
  readonly snapshotId?: string;
  readonly tags: readonly string[];
}

export interface PromptAnnex {
  readonly annexVersion: 1;
  readonly annexId: string;
  readonly createdAt: string;
  readonly sourcePacketId: string;
  readonly approvalReceiptId: string;
  readonly sourcePacketHash: string;
  readonly mode: "DRY_RUN";
  readonly intendedAudience: "worker";
  readonly workerPromptUse: "APPROVED_PACKET_ONLY";
  readonly autoInject: false;
  readonly rawContentIncluded: false;
  readonly summary: string;
  readonly artifactRefs: readonly string[];
  readonly snapshotIds: readonly string[];
  readonly entrySummaries: readonly PromptAnnexEntrySummary[];
  readonly constraints: readonly string[];
  readonly boundary: {
    readonly approvalVerified: true;
    readonly sourcePacketHashVerified: true;
    readonly autoInjection: "DISABLED";
    readonly directRealRepo: "BLOCKED";
    readonly workerCwd: "SNAPSHOT_ONLY";
    readonly managedSessionStarted: false;
  };
}

export interface CompilePromptAnnexInput {
  readonly annexId: string;
  readonly createdAt?: string;
}

const allowedAnnexKeys = [
  "annexVersion",
  "annexId",
  "createdAt",
  "sourcePacketId",
  "approvalReceiptId",
  "sourcePacketHash",
  "mode",
  "intendedAudience",
  "workerPromptUse",
  "autoInject",
  "rawContentIncluded",
  "summary",
  "artifactRefs",
  "snapshotIds",
  "entrySummaries",
  "constraints",
  "boundary",
] as const;

const rawContentFieldNames = new Set(["content", "raw", "rawContent", "message", "messages", "prompt", "response", "text"]);

export function compilePromptAnnex(
  packet: ContextPromotionPacket,
  approval: PromotionApprovalReceipt,
  input: CompilePromptAnnexInput,
): PromptAnnex {
  assertContextPromotionPacket(packet);
  assertPromotionApprovalReceipt(approval);
  assertSafeAnnexId(input.annexId, "annexId");
  if (!verifyPromotionApprovalReceiptForPacket(approval, packet)) {
    throw new Error("prompt annex requires approval receipt bound to the source packet");
  }

  const annex: PromptAnnex = {
    annexVersion: 1,
    annexId: input.annexId,
    createdAt: input.createdAt ?? new Date().toISOString(),
    sourcePacketId: packet.packetId,
    approvalReceiptId: approval.receiptId,
    sourcePacketHash: approval.sourcePacketHash,
    mode: "DRY_RUN",
    intendedAudience: "worker",
    workerPromptUse: "APPROVED_PACKET_ONLY",
    autoInject: false,
    rawContentIncluded: false,
    summary: [
      `Approved context packet ${packet.packetId}.`,
      `Use artifact refs and snapshot refs only.`,
      `Do not infer raw message content from hashes.`,
    ].join(" "),
    artifactRefs: [...packet.artifactRefs],
    snapshotIds: [...packet.snapshotIds],
    entrySummaries: packet.entryRefs.map((entry) => ({
      eventId: entry.eventId,
      eventType: entry.eventType,
      role: entry.role,
      source: entry.source,
      frontendOrSession: entry.frontendOrSession,
      contentHash: entry.contentHash,
      artifactRef: entry.artifactRef,
      snapshotId: entry.snapshotId,
      tags: [...entry.tags],
    })),
    constraints: [
      "Use packet artifact references only.",
      "Do not request or reconstruct raw ledger content.",
      "Use snapshot cwd only for managed Worker sessions.",
      "Direct real repository cwd remains blocked.",
      "Automatic context injection remains disabled.",
    ],
    boundary: {
      approvalVerified: true,
      sourcePacketHashVerified: true,
      autoInjection: "DISABLED",
      directRealRepo: "BLOCKED",
      workerCwd: "SNAPSHOT_ONLY",
      managedSessionStarted: false,
    },
  };
  assertPromptAnnex(annex);
  return annex;
}

export function validatePromptAnnex(value: unknown): value is PromptAnnex {
  if (!isRecord(value) || containsRawContentField(value) || !hasOnlyKeys(value, allowedAnnexKeys)) {
    return false;
  }
  return (
    value.annexVersion === 1 &&
    isSafeAnnexId(value.annexId) &&
    isIsoTimestamp(value.createdAt) &&
    isSafeAnnexId(value.sourcePacketId) &&
    isSafeAnnexId(value.approvalReceiptId) &&
    isSha256(value.sourcePacketHash) &&
    value.mode === "DRY_RUN" &&
    value.intendedAudience === "worker" &&
    value.workerPromptUse === "APPROVED_PACKET_ONLY" &&
    value.autoInject === false &&
    value.rawContentIncluded === false &&
    isSafeString(value.summary) &&
    isSafeStringArray(value.artifactRefs) &&
    isSafeStringArray(value.snapshotIds) &&
    Array.isArray(value.entrySummaries) &&
    value.entrySummaries.every(isEntrySummary) &&
    isSafeStringArray(value.constraints) &&
    isBoundary(value.boundary)
  );
}

export function assertPromptAnnex(value: unknown): asserts value is PromptAnnex {
  if (!validatePromptAnnex(value)) {
    throw new Error("prompt annex must be approval-bound metadata-only dry run");
  }
}

function isEntrySummary(value: unknown): value is PromptAnnexEntrySummary {
  return (
    isRecord(value) &&
    !containsRawContentField(value) &&
    hasOnlyKeys(value, [
      "eventId",
      "eventType",
      "role",
      "source",
      "frontendOrSession",
      "contentHash",
      "artifactRef",
      "snapshotId",
      "tags",
    ]) &&
    isSafeAnnexId(value.eventId) &&
    isSafeString(value.eventType) &&
    isSafeString(value.role) &&
    isSafeString(value.source) &&
    isSafeString(value.frontendOrSession) &&
    isSha256(value.contentHash) &&
    (value.artifactRef === undefined || isSafeString(value.artifactRef)) &&
    (value.snapshotId === undefined || isSafeAnnexId(value.snapshotId)) &&
    isSafeStringArray(value.tags)
  );
}

function isBoundary(value: unknown): value is PromptAnnex["boundary"] {
  return (
    isRecord(value) &&
    hasOnlyKeys(value, ["approvalVerified", "sourcePacketHashVerified", "autoInjection", "directRealRepo", "workerCwd", "managedSessionStarted"]) &&
    value.approvalVerified === true &&
    value.sourcePacketHashVerified === true &&
    value.autoInjection === "DISABLED" &&
    value.directRealRepo === "BLOCKED" &&
    value.workerCwd === "SNAPSHOT_ONLY" &&
    value.managedSessionStarted === false
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

function assertSafeAnnexId(value: string, fieldName: string): void {
  if (!isSafeAnnexId(value)) {
    throw new Error(`unsafe prompt annex ${fieldName}`);
  }
}

function isSafeAnnexId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9._:-]{1,220}$/.test(value);
}

function isSafeString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= 1200 && !value.includes("\0");
}

function isSafeStringArray(value: unknown): value is readonly string[] {
  return Array.isArray(value) && value.every(isSafeString);
}

function isIsoTimestamp(value: unknown): value is string {
  return typeof value === "string" && !Number.isNaN(Date.parse(value));
}

function isSha256(value: unknown): value is string {
  return typeof value === "string" && /^sha256:[A-F0-9]{64}$/.test(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(value: Record<string, unknown>, allowed: readonly string[]): boolean {
  const allowedSet = new Set(allowed);
  return Object.keys(value).every((key) => allowedSet.has(key));
}
