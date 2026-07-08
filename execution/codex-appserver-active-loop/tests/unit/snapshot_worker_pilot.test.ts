import { mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { createSnapshotBoundWorkerPlan, validateSnapshotBoundWorkerPlan } from "../../src/bridge/snapshot_worker_pilot.js";
import type { SnapshotManifest } from "../../src/bridge/repo_snapshot.js";
import type { PromptAnnex } from "../../src/bridge/prompt_annex.js";
import { createFileSnapshotWorkerPlanStore } from "../../src/stores/snapshot_worker_plan_store.js";

const tmpRoot = path.join(process.cwd(), "data", "tmp", "snapshot-worker-pilot");

describe("snapshot-bound Worker pilot prep", () => {
  it("builds a prep-only Worker plan pinned to snapshot cwd", () => {
    const plan = createSnapshotBoundWorkerPlan({
      planId: "cea-016-worker-plan-1",
      manifest: sampleManifest(),
      manifestPath: "data/snapshots/cea-011-safe-snapshot-20260707080426/_snapshot/manifest.json",
      annex: sampleAnnex(),
      annexRef: "data/prompt-annexes/annex.json",
      createdAt: "2026-07-07T00:00:00.000Z",
    });

    expect(plan.mode).toBe("PREP_ONLY");
    expect(plan.workerCwd).toBe(plan.snapshotRoot);
    expect(plan.sandboxPolicy).toEqual({ type: "readOnly", networkAccess: false });
    expect(plan.boundary.managedWorkerStarted).toBe(false);
    expect(plan.boundary.directRealRepo).toBe("BLOCKED");
    expect(plan.validation.workerCwdIsSnapshotRoot).toBe("PASS");
    expect(validateSnapshotBoundWorkerPlan(plan)).toBe(true);
  });

  it("rejects annex and manifest snapshot mismatch", () => {
    const annex = { ...sampleAnnex(), snapshotIds: ["different-snapshot"] };
    expect(() =>
      createSnapshotBoundWorkerPlan({
        planId: "cea-016-worker-plan-2",
        manifest: sampleManifest(),
        manifestPath: "manifest.json",
        annex,
        annexRef: "annex.json",
      }),
    ).toThrow("snapshot id");
  });

  it("rejects non-snapshot worker cwd and raw fields", () => {
    const manifest = { ...sampleManifest(), workerCwd: "A:/real/repo" };
    expect(() =>
      createSnapshotBoundWorkerPlan({
        planId: "cea-016-worker-plan-3",
        manifest,
        manifestPath: "manifest.json",
        annex: sampleAnnex(),
        annexRef: "annex.json",
      }),
    ).toThrow("manifest boundary");

    const plan = createSnapshotBoundWorkerPlan({
      planId: "cea-016-worker-plan-4",
      manifest: sampleManifest(),
      manifestPath: "manifest.json",
      annex: sampleAnnex(),
      annexRef: "annex.json",
    });
    expect(validateSnapshotBoundWorkerPlan({ ...plan, prompt: "raw prompt" })).toBe(false);
  });

  it("writes and reads Worker prep plans safely", async () => {
    const root = path.join(tmpRoot, `case-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });
    const store = createFileSnapshotWorkerPlanStore(root);
    const plan = createSnapshotBoundWorkerPlan({
      planId: "cea-016-worker-plan-store",
      manifest: sampleManifest(),
      manifestPath: "manifest.json",
      annex: sampleAnnex(),
      annexRef: "annex.json",
    });

    const planPath = await store.write(plan);
    expect(planPath.endsWith("cea-016-worker-plan-store.worker-plan.json")).toBe(true);
    await expect(store.read("cea-016-worker-plan-store")).resolves.toEqual(plan);
    await expect(store.write({ ...plan, mode: "LIVE" } as never)).rejects.toThrow("snapshot-only");
  });
});

function sampleManifest(): SnapshotManifest {
  return {
    snapshotVersion: 1,
    createdAt: "2026-07-07T00:00:00.000Z",
    sourceRoot: "A:/repo",
    snapshotRoot: "A:/repo/data/snapshots/cea-011-safe-snapshot-20260707080426",
    workerCwd: "A:/repo/data/snapshots/cea-011-safe-snapshot-20260707080426",
    allowlist: ["src"],
    includedFiles: [],
    excludedFiles: [],
    boundary: {
      bridgeExporterReadSource: true,
      managedSessionsReadSource: false,
      workerCwdSnapshotOnly: true,
      phase8DirectRealRepo: "BLOCKED",
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
    summary: "Approved context packet.",
    artifactRefs: ["docs/CONTEXT_PROMOTION_GATE.md"],
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
