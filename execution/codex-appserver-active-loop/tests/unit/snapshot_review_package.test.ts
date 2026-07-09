import { describe, expect, it } from "vitest";
import {
  createSnapshotReviewPackagePlan,
  isAllowedSnapshotReviewPackageEntry,
  validateSnapshotReviewPackageArtifacts,
  type SnapshotReviewPackageArtifact,
} from "../../src/bridge/snapshot_review_package.js";

describe("snapshot review package publisher", () => {
  it("selects only CEA-018/019/020 manifest, report, and receipt artifacts", () => {
    const plan = createSnapshotReviewPackagePlan({
      cea018Report: cea018Report(),
      cea019Report: cea019Report(),
      cea020Report: cea020Report(),
    });

    expect(plan.artifacts).toHaveLength(8);
    expect(plan.contentPolicy.excludesRawEvents).toBe(true);
    expect(plan.artifacts.map((artifact) => artifact.kind)).toEqual([
      "manifest",
      "report",
      "report",
      "receipt",
      "report",
      "receipt",
      "report",
      "receipt",
    ]);
    expect(plan.artifacts.map((artifact) => artifact.entryPath)).not.toEqual(expect.arrayContaining([expect.stringContaining("events")]));
  });

  it("allows only manifest, report, and receipt package entries", () => {
    expect(isAllowedSnapshotReviewPackageEntry("MANIFEST.json")).toBe(true);
    expect(isAllowedSnapshotReviewPackageEntry("cea-018/manifest/snapshot-manifest.json")).toBe(true);
    expect(isAllowedSnapshotReviewPackageEntry("cea-019/report/report.json")).toBe(true);
    expect(isAllowedSnapshotReviewPackageEntry("cea-020/receipt/receipt.md")).toBe(true);
    expect(isAllowedSnapshotReviewPackageEntry("cea-018/events/events.jsonl")).toBe(false);
    expect(isAllowedSnapshotReviewPackageEntry("cea-018/report/data/snapshots/raw.ts")).toBe(false);
    expect(isAllowedSnapshotReviewPackageEntry("cea-018/report/.env")).toBe(false);
  });

  it("rejects invalid package artifact paths", () => {
    const invalid: SnapshotReviewPackageArtifact = {
      taskId: "CEA-018",
      kind: "report",
      label: "events",
      sourcePath: "A:/repo/data/events/cea-018.events.jsonl",
      entryPath: "cea-018/events/cea-018.events.jsonl",
    };

    expect(() => validateSnapshotReviewPackageArtifacts([invalid])).toThrow("kind mismatch");
  });
});

function cea018Report(): Record<string, unknown> {
  return {
    task_id: "CEA-018",
    artifacts: {
      snapshot_manifest: "A:/repo/data/snapshots/cea-018/_snapshot/manifest.json",
      snapshot_exclusions: "A:/repo/data/snapshots/cea-018/_snapshot/exclusions.json",
      report: "A:/repo/data/reports/cea-018_e2e_safe_review_loop.json",
      receipt: "A:/repo/data/receipts/2026-07-07-cea-018-e2e-safe-review-loop.receipt.md",
      events: "A:/repo/data/events/cea-018.events.jsonl",
      annex: "A:/repo/data/prompt-annexes/annex.json",
    },
  };
}

function cea019Report(): Record<string, unknown> {
  return {
    task_id: "CEA-019",
    artifacts: {
      report: "A:/repo/data/reports/cea-019_e2e_evidence_verification_gate.json",
      receipt: "A:/repo/data/receipts/2026-07-07-cea-019-e2e-evidence-verification-gate.receipt.md",
      cea018_events: "A:/repo/data/events/cea-018.events.jsonl",
    },
  };
}

function cea020Report(): Record<string, unknown> {
  return {
    task_id: "CEA-020",
    artifacts: {
      report: "A:/repo/data/reports/cea-020_phase8_schema_gate.json",
      receipt: "A:/repo/data/receipts/2026-07-07-cea-020-phase8-schema-gate.receipt.md",
    },
  };
}
