import { hashMessagePayload } from "../stores/message_ledger.js";
import type { CodexChannelMessage } from "../types/messages.js";

export interface FuzzyDuplicateAdvisoryInput {
  readonly message: CodexChannelMessage;
  readonly candidates: readonly CodexChannelMessage[];
  readonly threshold?: number;
}

export interface FuzzyDuplicateAdvisory {
  readonly suspected_near_duplicate: boolean;
  readonly similarity: number;
  readonly compared_with?: string;
  readonly message_id: string;
  readonly payload_hash: string;
  readonly compared_with_payload_hash?: string;
  readonly candidate_count: number;
  readonly threshold: number;
  readonly action_taken: "NONE";
  readonly authority: "ADVISORY_ONLY";
}

const defaultThreshold = 0.8;

export function createFuzzyDuplicateAdvisory(input: FuzzyDuplicateAdvisoryInput): FuzzyDuplicateAdvisory {
  const threshold = input.threshold ?? defaultThreshold;
  if (!Number.isFinite(threshold) || threshold < 0 || threshold > 1) {
    throw new Error("fuzzy advisory threshold must be between 0 and 1");
  }
  const messageTokens = tokenizeMessage(input.message);
  const scored = input.candidates
    .filter((candidate) => candidate.message_id !== input.message.message_id)
    .map((candidate) => ({
      candidate,
      similarity: tokenDiceSimilarity(messageTokens, tokenizeMessage(candidate)),
    }))
    .sort((left, right) => right.similarity - left.similarity || left.candidate.message_id.localeCompare(right.candidate.message_id));
  const best = scored[0];
  const similarity = roundSimilarity(best?.similarity ?? 0);
  const suspected = Boolean(best && similarity >= threshold);
  return {
    suspected_near_duplicate: suspected,
    similarity,
    compared_with: suspected ? best?.candidate.message_id : undefined,
    message_id: input.message.message_id,
    payload_hash: hashMessagePayload(input.message),
    compared_with_payload_hash: suspected && best ? hashMessagePayload(best.candidate) : undefined,
    candidate_count: input.candidates.length,
    threshold,
    action_taken: "NONE",
    authority: "ADVISORY_ONLY",
  };
}

function tokenizeMessage(message: CodexChannelMessage): readonly string[] {
  const text =
    message.type === "MESSAGE_TO_CODEX"
      ? [
          message.kind,
          message.from,
          message.to,
          message.payload.question,
          ...message.payload.context,
          message.payload.expected_response,
        ].join(" ")
      : [
          message.kind,
          message.from,
          message.to,
          message.payload.decision,
          message.payload.reason,
          message.payload.next_instruction,
        ].join(" ");
  return normalizeText(text);
}

function normalizeText(text: string): readonly string[] {
  const tokens = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  return [...new Set(tokens)].sort();
}

function tokenDiceSimilarity(left: readonly string[], right: readonly string[]): number {
  if (left.length === 0 && right.length === 0) return 1;
  if (left.length === 0 || right.length === 0) return 0;
  const rightSet = new Set(right);
  const intersection = left.filter((token) => rightSet.has(token)).length;
  return (2 * intersection) / (left.length + right.length);
}

function roundSimilarity(value: number): number {
  return Math.round(value * 100) / 100;
}
