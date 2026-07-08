import { describe, expect, it } from "vitest";
import { createSnapshotWorkerLivePrompt } from "../../src/bridge/snapshot_worker_live.js";
import type { PromptAnnex } from "../../src/bridge/prompt_annex.js";
import type { SnapshotBoundWorkerPlan } from "../../src/bridge/snapshot_worker_pilot.js";

describe("snapshot Worker live prompt", () => {
  it("builds a snapshot-only Worker prompt from the approved annex", () => {
    const prompt = createSnapshotWorkerLivePrompt({ plan: samplePlan(), annex: sampleAnnex() });
    expect(prompt).toContain("Snapshot-bound Worker live pilot");
    expect(prompt).toContain("cea-011-safe-snapshot-20260707080426");
    expect(prompt).toContain("APPROVED_PACKET_ONLY");
    expect(prompt).toContain("directRealRepo");
    expect(prompt).not.toContain("raw worker detail");
  });

  it("rejects annex mismatch", () => {
    expect(() =>
      createSnapshotWorkerLivePrompt({
        plan: samplePlan(),
        annex: { ...sampleAnnex(), annexId: "other-annex" },
      }),
    ).toThrow("annex id");
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
