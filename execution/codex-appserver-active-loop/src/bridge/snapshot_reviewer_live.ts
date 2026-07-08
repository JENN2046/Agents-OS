import { validateStructuredLoopOutput, type WorkerDone } from "./event_contracts.js";
import { assertPromptAnnex, type PromptAnnex } from "./prompt_annex.js";
import { assertSnapshotBoundWorkerPlan, type SnapshotBoundWorkerPlan } from "./snapshot_worker_pilot.js";

export interface SnapshotWorkerLiveEvidence {
  readonly result: string;
  readonly job_id: string;
  readonly worker_thread_id: string;
  readonly worker_turn_id: string;
  readonly snapshot_id: string;
  readonly worker_cwd: string;
  readonly app_server_process_cwd: string;
  readonly annex_id: string;
  readonly output: WorkerDone;
  readonly boundary_flags: {
    readonly app_server_process_cwd_snapshot: string;
    readonly worker_thread_cwd_snapshot: string;
    readonly worker_turn_cwd_snapshot: string;
    readonly sandbox_read_only_network_off: string;
    readonly context_auto_injection: string;
    readonly direct_real_repo: string;
    readonly managed_worker_started: string;
    readonly managed_reviewer_started: string;
    readonly command_exec: string;
    readonly file_write: string;
    readonly secrets_read: string;
    readonly commit_push_deploy_release_tag: string;
  };
}

export interface SnapshotReviewerLivePromptInput {
  readonly plan: SnapshotBoundWorkerPlan;
  readonly annex: PromptAnnex;
  readonly workerEvidence: SnapshotWorkerLiveEvidence;
}

export function createSnapshotReviewerLivePrompt(input: SnapshotReviewerLivePromptInput): string {
  assertSnapshotBoundWorkerPlan(input.plan);
  assertPromptAnnex(input.annex);
  assertSnapshotWorkerLiveEvidence(input.workerEvidence);
  if (input.plan.annexId !== input.annex.annexId || input.workerEvidence.annex_id !== input.annex.annexId) {
    throw new Error("Reviewer prompt requires matching plan, annex, and Worker evidence annex ids");
  }
  if (input.workerEvidence.worker_cwd !== input.plan.workerCwd || input.workerEvidence.app_server_process_cwd !== input.plan.snapshotRoot) {
    throw new Error("Reviewer prompt requires Worker evidence to be snapshot-bound");
  }
  if (input.workerEvidence.boundary_flags.direct_real_repo !== "BLOCKED") {
    throw new Error("Reviewer prompt requires direct real repo to remain blocked");
  }
  const requiredWorkerFlags = {
    app_server_process_cwd_snapshot: "YES",
    worker_thread_cwd_snapshot: "YES",
    worker_turn_cwd_snapshot: "YES",
    sandbox_read_only_network_off: "YES",
    context_auto_injection: "DISABLED",
    direct_real_repo: "BLOCKED",
    managed_worker_started: "STARTED",
    command_exec: "NOT_USED",
    file_write: "NOT_USED",
    secrets_read: "NOT_USED",
    commit_push_deploy_release_tag: "NOT_USED",
  } satisfies Partial<Record<keyof SnapshotWorkerLiveEvidence["boundary_flags"], string>>;
  for (const [flag, expected] of Object.entries(requiredWorkerFlags)) {
    if (input.workerEvidence.boundary_flags[flag as keyof SnapshotWorkerLiveEvidence["boundary_flags"]] !== expected) {
      throw new Error(`Reviewer prompt requires Worker boundary flag ${flag}=${expected}`);
    }
  }

  const safePayload = {
    reviewerCwd: input.plan.workerCwd,
    snapshotId: input.plan.snapshotId,
    annexId: input.annex.annexId,
    workerJobId: input.workerEvidence.job_id,
    workerThreadId: input.workerEvidence.worker_thread_id,
    workerTurnId: input.workerEvidence.worker_turn_id,
    workerDoneSummary: {
      type: input.workerEvidence.output.type,
      summaryLength: input.workerEvidence.output.summary.length,
      evidenceCount: input.workerEvidence.output.evidence.length,
    },
    annexSummary: {
      artifactRefCount: input.annex.artifactRefs.length,
      snapshotIdCount: input.annex.snapshotIds.length,
      workerPromptUse: input.annex.workerPromptUse,
      autoInject: input.annex.autoInject,
      rawContentIncluded: input.annex.rawContentIncluded,
    },
    requiredProofs: {
      workerDone: input.workerEvidence.output.type === "DONE",
      appServerProcessCwdIsSnapshot: true,
      workerCwdIsSnapshot: true,
      reviewerCwdPolicy: "SNAPSHOT_ONLY",
      approvedPacketOnlyAnnex: input.annex.workerPromptUse === "APPROVED_PACKET_ONLY",
      directRealRepo: input.workerEvidence.boundary_flags.direct_real_repo,
      commandExec: input.workerEvidence.boundary_flags.command_exec,
      fileWrite: input.workerEvidence.boundary_flags.file_write,
      secretsRead: input.workerEvidence.boundary_flags.secrets_read,
    },
    boundary: {
      reviewerCwdPolicy: "SNAPSHOT_ONLY",
      sandboxPolicy: input.plan.sandboxPolicy,
      workerBoundaryFlags: requiredWorkerFlags,
      autoInjection: input.plan.boundary.autoInjection,
    },
    recommendedDecision: {
      type: "REVIEWER_DECISION",
      decision: "continue",
      reason: "Worker DONE evidence confirms snapshot cwd, read-only network-off sandbox, approved packet-only annex, and direct real repo blocked.",
      next_instruction: "Write the CEA-018 receipt and keep Phase 8 direct real repo blocked.",
      constraints: ["Reviewer cwd remains snapshot-only", "No commands, file writes, network, secrets, or direct real repo access"],
      evidence_used: ["worker DONE type", "snapshot cwd flags", "read-only network-off sandbox", "direct real repo BLOCKED"],
    },
  };

  return [
    "Snapshot-bound Reviewer live pilot.",
    "You are running with cwd set to the same generated safe snapshot path as the Worker.",
    "Review only the provided Worker DONE proof summary and metadata payload.",
    "Do not call tools, run commands, request approvals, use network, edit files, inspect private state, or access the real repository path.",
    "Return only one compact JSON object matching REVIEWER_DECISION.",
    "Use decision continue if the Worker evidence proves snapshot cwd, read-only network-off sandbox, approved packet-only annex, and Phase 8 direct real repo blocked.",
    "Use decision block if any required boundary is missing.",
    "When all requiredProofs are satisfied, you may return the recommendedDecision exactly.",
    "Safe metadata payload:",
    JSON.stringify(safePayload, null, 2),
  ].join("\n");
}

export function assertSnapshotWorkerLiveEvidence(value: unknown): asserts value is SnapshotWorkerLiveEvidence {
  if (!isRecord(value) || value.result !== "PASS" || !isSafeString(value.job_id)) {
    throw new Error("invalid Worker live evidence report");
  }
  if (!isSafeString(value.worker_thread_id) || !isSafeString(value.worker_turn_id)) {
    throw new Error("Worker live evidence is missing thread or turn ids");
  }
  if (!isSafeString(value.snapshot_id) || !isSafeString(value.worker_cwd) || !isSafeString(value.app_server_process_cwd)) {
    throw new Error("Worker live evidence is missing snapshot cwd fields");
  }
  if (!isSafeString(value.annex_id) || !validateStructuredLoopOutput(value.output) || value.output.type !== "DONE") {
    throw new Error("Worker live evidence is missing DONE output");
  }
  if (!isRecord(value.boundary_flags)) {
    throw new Error("Worker live evidence is missing boundary flags");
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isSafeString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= 3000 && !value.includes("\0");
}
