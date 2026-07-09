import { assertPromptAnnex, type PromptAnnex } from "./prompt_annex.js";
import { assertSnapshotBoundWorkerPlan, type SnapshotBoundWorkerPlan } from "./snapshot_worker_pilot.js";

export interface SnapshotWorkerLivePromptInput {
  readonly plan: SnapshotBoundWorkerPlan;
  readonly annex: PromptAnnex;
}

export const snapshotWorkerLiveOutputType = "DONE" as const;

export function createSnapshotWorkerLivePrompt(input: SnapshotWorkerLivePromptInput): string {
  assertSnapshotBoundWorkerPlan(input.plan);
  assertPromptAnnex(input.annex);
  if (input.plan.annexId !== input.annex.annexId) {
    throw new Error("live Worker prompt requires the plan annex id to match the annex");
  }
  if (input.plan.workerCwd !== input.plan.snapshotRoot || input.plan.boundary.workerCwdPolicy !== "SNAPSHOT_ONLY") {
    throw new Error("live Worker prompt requires snapshot-only cwd");
  }

  const safePayload = {
    planId: input.plan.planId,
    snapshotId: input.plan.snapshotId,
    workerCwd: input.plan.workerCwd,
    annexId: input.annex.annexId,
    workerPromptUse: input.annex.workerPromptUse,
    artifactRefs: input.annex.artifactRefs,
    snapshotIds: input.annex.snapshotIds,
    entrySummaries: input.annex.entrySummaries,
    constraints: input.annex.constraints,
    boundary: {
      workerCwdPolicy: input.plan.boundary.workerCwdPolicy,
      sandboxPolicy: input.plan.sandboxPolicy,
      directRealRepo: input.plan.boundary.directRealRepo,
      autoInjection: input.plan.boundary.autoInjection,
      rawContentIncluded: input.plan.boundary.rawContentIncluded,
    },
  };

  return [
    "Snapshot-bound Worker live pilot.",
    "You are running with cwd set to the generated safe snapshot path.",
    "Use only the metadata in this message and the snapshot cwd boundary.",
    "Do not call tools, run commands, request approvals, use network, edit files, or access private state.",
    "Do not attempt to read the real repository path.",
    "Return only a JSON object matching this shape: {\"type\":\"DONE\",\"summary\":\"string\",\"evidence\":[\"string\"]}.",
    "The summary must state whether the snapshot-bound Worker launch boundary is acceptable for the next Reviewer pilot.",
    "Evidence must mention snapshot cwd, read-only network-off sandbox, approved packet-only annex, and Phase 8 direct real repo blocked.",
    "Safe metadata payload:",
    JSON.stringify(safePayload, null, 2),
  ].join("\n");
}
