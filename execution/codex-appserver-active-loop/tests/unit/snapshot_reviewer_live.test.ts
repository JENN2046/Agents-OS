import { describe, expect, it } from "vitest";
import { createSnapshotReviewerLivePrompt, type SnapshotWorkerLiveEvidence } from "../../src/bridge/snapshot_reviewer_live.js";
import type { PromptAnnex } from "../../src/bridge/prompt_annex.js";
import type { SnapshotBoundWorkerPlan } from "../../src/bridge/snapshot_worker_pilot.js";

describe("snapshot Reviewer live prompt", () => {
  it("builds a snapshot-only Reviewer prompt from Worker DONE evidence", () => {
    const prompt = createSnapshotReviewerLivePrompt({
      plan: samplePlan(),
      annex: sampleAnnex(),
      workerEvidence: sampleWorkerEvidence(),
    });

    expect(prompt).toContain("Snapshot-bound Reviewer live pilot");
    expect(prompt).toContain("REVIEWER_DECISION");
    expect(prompt).toContain("worker-job");
    expect(prompt).toContain("SNAPSHOT_ONLY");
    expect(prompt).toContain("BLOCKED");
  });

  it("rejects Worker evidence that is not snapshot-bound", () => {
    expect(() =>
      createSnapshotReviewerLivePrompt({
        plan: samplePlan(),
        annex: sampleAnnex(),
        workerEvidence: { ...sampleWorkerEvidence(), worker_cwd: "A:/real/repo" },
      }),
    ).toThrow("snapshot-bound");
  });

  it("rejects Worker evidence with unsafe side effect flags", () => {
    expect(() =>
      createSnapshotReviewerLivePrompt({
        plan: samplePlan(),
        annex: sampleAnnex(),
        workerEvidence: {
          ...sampleWorkerEvidence(),
          boundary_flags: { ...sampleWorkerEvidence().boundary_flags, command_exec: "USED" },
        },
      }),
    ).toThrow("command_exec=NOT_USED");
  });
});

function samplePlan(): SnapshotBoundWorkerPlan {
  return {
    planVersion: 1,
    planId: "cea-016-snapshot-worker-plan",
    createdAt: "2026-07-07T00:00:00.000Z",
    mode: "PREP_ONLY",
    snapshotId: "cea-011-safe-snapshot-20260707080426",
    snapshotRoot: "A:/repo/data/snapshots/cea-011-safe-snapshot-20260707080426",
    manifestPath: "A:/repo/data/snapshots/cea-011-safe-snapshot-20260707080426/_snapshot/manifest.json",
    workerCwd: "A:/repo/data/snapshots/cea-011-safe-snapshot-20260707080426",
    annexId: "cea-015-annex",
    annexRef: "A:/repo/data/prompt-annexes/cea-015-annex.prompt-annex.json",
    sandboxPolicy: { type: "readOnly", networkAccess: false },
    turnPreview: {
      cwd: "A:/repo/data/snapshots/cea-011-safe-snapshot-20260707080426",
      usesAnnex: true,
      outputSchema: "WORKER_DONE_OR_NEED_REVIEWER",
      artifactRefs: ["docs/CONTEXT_LEDGER.md"],
      snapshotIds: ["cea-011-safe-snapshot-20260707080426"],
    },
    validation: {
      snapshotManifestBoundary: "PASS",
      annexApprovalVerified: "PASS",
      annexSnapshotMatchesManifest: "PASS",
      workerCwdIsSnapshotRoot: "PASS",
    },
    boundary: {
      managedWorkerStarted: false,
      managedReviewerStarted: false,
      directRealRepo: "BLOCKED",
      workerCwdPolicy: "SNAPSHOT_ONLY",
      autoInjection: "DISABLED",
      rawContentIncluded: false,
    },
  };
}

function sampleAnnex(): PromptAnnex {
  return {
    annexVersion: 1,
    annexId: "cea-015-annex",
    createdAt: "2026-07-07T00:00:00.000Z",
    sourcePacketId: "cea-013-packet",
    approvalReceiptId: "cea-014-approval",
    sourcePacketHash: "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    mode: "DRY_RUN",
    intendedAudience: "worker",
    workerPromptUse: "APPROVED_PACKET_ONLY",
    autoInject: false,
    rawContentIncluded: false,
    summary: "Approved packet.",
    artifactRefs: ["docs/CONTEXT_LEDGER.md"],
    snapshotIds: ["cea-011-safe-snapshot-20260707080426"],
    entrySummaries: [],
    constraints: ["Use snapshot cwd only."],
    boundary: {
      approvalVerified: true,
      sourcePacketHashVerified: true,
      autoInjection: "DISABLED",
      directRealRepo: "BLOCKED",
      workerCwd: "SNAPSHOT_ONLY",
      managedSessionStarted: false,
    },
  };
}

function sampleWorkerEvidence(): SnapshotWorkerLiveEvidence {
  return {
    result: "PASS",
    job_id: "worker-job",
    worker_thread_id: "worker-thread",
    worker_turn_id: "worker-turn",
    snapshot_id: "cea-011-safe-snapshot-20260707080426",
    worker_cwd: "A:/repo/data/snapshots/cea-011-safe-snapshot-20260707080426",
    app_server_process_cwd: "A:/repo/data/snapshots/cea-011-safe-snapshot-20260707080426",
    annex_id: "cea-015-annex",
    output: {
      type: "DONE",
      summary: "snapshot-bound Worker accepted",
      evidence: ["snapshot cwd", "read-only network-off", "direct real repo blocked"],
    },
    boundary_flags: {
      app_server_process_cwd_snapshot: "YES",
      worker_thread_cwd_snapshot: "YES",
      worker_turn_cwd_snapshot: "YES",
      sandbox_read_only_network_off: "YES",
      context_auto_injection: "DISABLED",
      direct_real_repo: "BLOCKED",
      managed_worker_started: "STARTED",
      managed_reviewer_started: "NOT_STARTED",
      command_exec: "NOT_USED",
      file_write: "NOT_USED",
      secrets_read: "NOT_USED",
      commit_push_deploy_release_tag: "NOT_USED",
    },
  };
}
