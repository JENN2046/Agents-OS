import { createHash } from "node:crypto";
import {
  approveContextPromotionPacket,
  assertContextPromotionPacket,
  type ApproveContextPromotionPacketInput,
  type ContextPromotionPacket,
  type PromotionApproverRole,
} from "./context_promotion.js";

export interface PromotionApprovalReceipt {
  readonly receiptVersion: 1;
  readonly receiptId: string;
  readonly createdAt: string;
  readonly packetId: string;
  readonly sourcePacketHash: string;
  readonly statusBefore: "BLOCKED_BY_DEFAULT";
  readonly statusAfter: "APPROVED_FOR_PACKET_USE";
  readonly workerPromptUseAfter: "APPROVED_PACKET_ONLY";
  readonly approvedByRole: PromotionApproverRole;
  readonly approvedByAgentId: string;
  readonly reason: string;
  readonly evidence: readonly string[];
  readonly approvalHash: string;
  readonly boundary: {
    readonly approvalReceiptRequired: true;
    readonly autoInjection: "DISABLED";
    readonly rawContentIncluded: false;
    readonly contextPatch: "DISABLED";
    readonly directRealRepo: "BLOCKED";
    readonly workerCwd: "SNAPSHOT_ONLY";
  };
}

export interface CreatePromotionApprovalReceiptInput extends ApproveContextPromotionPacketInput {
  readonly receiptId: string;
  readonly createdAt?: string;
}

const allowedApprovalReceiptKeys = [
  "receiptVersion",
  "receiptId",
  "createdAt",
  "packetId",
  "sourcePacketHash",
  "statusBefore",
  "statusAfter",
  "workerPromptUseAfter",
  "approvedByRole",
  "approvedByAgentId",
  "reason",
  "evidence",
  "approvalHash",
  "boundary",
] as const;

const rawContentFieldNames = new Set(["content", "raw", "rawContent", "message", "messages", "prompt", "response", "text"]);

export function createPromotionApprovalReceipt(
  packet: ContextPromotionPacket,
  input: CreatePromotionApprovalReceiptInput,
): PromotionApprovalReceipt {
  assertContextPromotionPacket(packet);
  if (packet.status !== "BLOCKED_BY_DEFAULT" || packet.workerPromptUse !== "BLOCKED") {
    throw new Error("promotion approval receipt requires a blocked source packet");
  }
  assertSafeApprovalId(input.receiptId, "receiptId");

  const approved = approveContextPromotionPacket(packet, input);
  const createdAt = input.createdAt ?? new Date().toISOString();
  const receiptWithoutHash = {
    receiptVersion: 1,
    receiptId: input.receiptId,
    createdAt,
    packetId: packet.packetId,
    sourcePacketHash: hashPromotionPacket(packet),
    statusBefore: packet.status,
    statusAfter: "APPROVED_FOR_PACKET_USE",
    workerPromptUseAfter: "APPROVED_PACKET_ONLY",
    approvedByRole: input.approvedByRole,
    approvedByAgentId: input.approvedByAgentId,
    reason: input.reason,
    evidence: [...input.evidence],
    boundary: {
      approvalReceiptRequired: true,
      autoInjection: "DISABLED",
      rawContentIncluded: false,
      contextPatch: "DISABLED",
      directRealRepo: "BLOCKED",
      workerCwd: "SNAPSHOT_ONLY",
    },
  } satisfies Omit<PromotionApprovalReceipt, "approvalHash">;
  const receipt: PromotionApprovalReceipt = {
    ...receiptWithoutHash,
    approvalHash: hashJson(receiptWithoutHash),
  };
  assertPromotionApprovalReceipt(receipt);
  return receipt;
}

export function hashPromotionPacket(packet: ContextPromotionPacket): string {
  assertContextPromotionPacket(packet);
  return hashJson(packet);
}

export function validatePromotionApprovalReceipt(value: unknown): value is PromotionApprovalReceipt {
  if (!isRecord(value) || containsRawContentField(value) || !hasOnlyKeys(value, allowedApprovalReceiptKeys)) {
    return false;
  }
  return (
    value.receiptVersion === 1 &&
    isSafeApprovalId(value.receiptId) &&
    isIsoTimestamp(value.createdAt) &&
    isSafeApprovalId(value.packetId) &&
    isSha256(value.sourcePacketHash) &&
    value.statusBefore === "BLOCKED_BY_DEFAULT" &&
    value.statusAfter === "APPROVED_FOR_PACKET_USE" &&
    value.workerPromptUseAfter === "APPROVED_PACKET_ONLY" &&
    (value.approvedByRole === "commander" || value.approvedByRole === "reviewer") &&
    isSafeString(value.approvedByAgentId) &&
    isSafeString(value.reason) &&
    isSafeStringArray(value.evidence) &&
    value.evidence.length > 0 &&
    isSha256(value.approvalHash) &&
    isApprovalBoundary(value.boundary)
  );
}

export function assertPromotionApprovalReceipt(value: unknown): asserts value is PromotionApprovalReceipt {
  if (!validatePromotionApprovalReceipt(value)) {
    throw new Error("promotion approval receipt must be packet-only and metadata-only");
  }
}

export function verifyPromotionApprovalReceiptForPacket(
  receipt: PromotionApprovalReceipt,
  packet: ContextPromotionPacket,
): boolean {
  assertPromotionApprovalReceipt(receipt);
  assertContextPromotionPacket(packet);
  return receipt.packetId === packet.packetId && receipt.sourcePacketHash === hashPromotionPacket(packet);
}

function hashJson(value: unknown): string {
  return `sha256:${createHash("sha256").update(JSON.stringify(value), "utf8").digest("hex").toUpperCase()}`;
}

function isApprovalBoundary(value: unknown): value is PromotionApprovalReceipt["boundary"] {
  return (
    isRecord(value) &&
    hasOnlyKeys(value, ["approvalReceiptRequired", "autoInjection", "rawContentIncluded", "contextPatch", "directRealRepo", "workerCwd"]) &&
    value.approvalReceiptRequired === true &&
    value.autoInjection === "DISABLED" &&
    value.rawContentIncluded === false &&
    value.contextPatch === "DISABLED" &&
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

function assertSafeApprovalId(value: string, fieldName: string): void {
  if (!isSafeApprovalId(value)) {
    throw new Error(`unsafe promotion approval ${fieldName}`);
  }
}

function isSafeApprovalId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9._:-]{1,200}$/.test(value);
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
