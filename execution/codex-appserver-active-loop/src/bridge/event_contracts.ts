import path from "node:path";
import type { SandboxPolicy } from "../generated/appserver/v2/SandboxPolicy";
import type { TurnStartParams } from "../generated/appserver/v2/TurnStartParams";
import type { JsonValue } from "../generated/appserver/serde_json/JsonValue";

export const problemTypes = ["architecture", "policy", "test_failure", "diff_review", "unclear_intent"] as const;
export type ProblemType = (typeof problemTypes)[number];

export const reviewerDecisions = ["continue", "revise", "block", "request_human_gate"] as const;
export type ReviewerDecisionKind = (typeof reviewerDecisions)[number];

export interface WorkerNeedReviewer {
  readonly type: "NEED_REVIEWER";
  readonly problem_type: ProblemType;
  readonly question: string;
  readonly evidence: readonly string[];
  readonly proposed_options: readonly string[];
  readonly recommended_next_action: string;
}

export interface ReviewerDecision {
  readonly type: "REVIEWER_DECISION";
  readonly decision: ReviewerDecisionKind;
  readonly reason: string;
  readonly next_instruction: string;
  readonly constraints: readonly string[];
  readonly evidence_used: readonly string[];
}

export interface WorkerDone {
  readonly type: "DONE";
  readonly summary: string;
  readonly evidence: readonly string[];
}

export interface BlockedOutput {
  readonly type: "BLOCKED";
  readonly reason: string;
  readonly evidence: readonly string[];
}

export type StructuredLoopOutput = WorkerNeedReviewer | ReviewerDecision | WorkerDone | BlockedOutput;

export type JsonSchema = Record<string, JsonValue>;

const stringArraySchema = {
  type: "array",
  items: { type: "string" },
} satisfies JsonSchema;

export const workerNeedReviewerSchema = {
  type: "object",
  additionalProperties: false,
  required: ["type", "problem_type", "question", "evidence", "proposed_options", "recommended_next_action"],
  properties: {
    type: { type: "string", const: "NEED_REVIEWER" },
    problem_type: { enum: [...problemTypes] },
    question: { type: "string" },
    evidence: stringArraySchema,
    proposed_options: stringArraySchema,
    recommended_next_action: { type: "string" },
  },
} satisfies JsonSchema;

export const reviewerDecisionSchema = {
  type: "object",
  additionalProperties: false,
  required: ["type", "decision", "reason", "next_instruction", "constraints", "evidence_used"],
  properties: {
    type: { type: "string", const: "REVIEWER_DECISION" },
    decision: { enum: [...reviewerDecisions] },
    reason: { type: "string" },
    next_instruction: { type: "string" },
    constraints: stringArraySchema,
    evidence_used: stringArraySchema,
  },
} satisfies JsonSchema;

export const workerDoneSchema = {
  type: "object",
  additionalProperties: false,
  required: ["type", "summary", "evidence"],
  properties: {
    type: { type: "string", const: "DONE" },
    summary: { type: "string" },
    evidence: stringArraySchema,
  },
} satisfies JsonSchema;

export const blockedOutputSchema = {
  type: "object",
  additionalProperties: false,
  required: ["type", "reason", "evidence"],
  properties: {
    type: { type: "string", const: "BLOCKED" },
    reason: { type: "string" },
    evidence: stringArraySchema,
  },
} satisfies JsonSchema;

export function validateStructuredLoopOutput(value: unknown): value is StructuredLoopOutput {
  if (!isRecord(value) || typeof value.type !== "string") {
    return false;
  }
  switch (value.type) {
    case "NEED_REVIEWER":
      return (
        isOneOf(value.problem_type, problemTypes) &&
        typeof value.question === "string" &&
        isStringArray(value.evidence) &&
        isStringArray(value.proposed_options) &&
        typeof value.recommended_next_action === "string" &&
        hasOnlyKeys(value, ["type", "problem_type", "question", "evidence", "proposed_options", "recommended_next_action"])
      );
    case "REVIEWER_DECISION":
      return (
        isOneOf(value.decision, reviewerDecisions) &&
        typeof value.reason === "string" &&
        typeof value.next_instruction === "string" &&
        isStringArray(value.constraints) &&
        isStringArray(value.evidence_used) &&
        hasOnlyKeys(value, ["type", "decision", "reason", "next_instruction", "constraints", "evidence_used"])
      );
    case "DONE":
      return (
        typeof value.summary === "string" &&
        isStringArray(value.evidence) &&
        hasOnlyKeys(value, ["type", "summary", "evidence"])
      );
    case "BLOCKED":
      return (
        typeof value.reason === "string" &&
        isStringArray(value.evidence) &&
        hasOnlyKeys(value, ["type", "reason", "evidence"])
      );
    default:
      return false;
  }
}

export function createReadOnlySyntheticSandboxPolicy(): SandboxPolicy {
  return { type: "readOnly", networkAccess: false };
}

export function createSyntheticTurnStartParams(input: {
  readonly threadId: string;
  readonly syntheticWorkspaceRoot: string;
  readonly prompt: string;
  readonly outputSchema: JsonSchema;
}): TurnStartParams {
  assertSyntheticWorkspaceRoot(input.syntheticWorkspaceRoot);
  return {
    threadId: input.threadId,
    input: [{ type: "text", text: input.prompt, text_elements: [] }],
    cwd: input.syntheticWorkspaceRoot,
    sandboxPolicy: createReadOnlySyntheticSandboxPolicy(),
    outputSchema: input.outputSchema,
  };
}

export function assertSyntheticWorkspaceRoot(root: string): void {
  const normalized = path.normalize(root).replaceAll("\\", "/");
  if (!normalized.endsWith("data/synthetic-workspace")) {
    throw new Error("MVP smoke readable root must be data/synthetic-workspace");
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isOneOf<T extends readonly string[]>(value: unknown, allowed: T): value is T[number] {
  return typeof value === "string" && (allowed as readonly string[]).includes(value);
}

function hasOnlyKeys(value: Record<string, unknown>, allowed: readonly string[]): boolean {
  const allowedSet = new Set(allowed);
  return Object.keys(value).every((key) => allowedSet.has(key));
}
