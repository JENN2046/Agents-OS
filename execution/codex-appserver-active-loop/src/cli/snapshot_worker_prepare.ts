import { readFile } from "node:fs/promises";
import path from "node:path";
import { assertAllowedArtifactFilename, assertProjectArtifactPathBoundary } from "../bridge/artifact_path_boundary.js";
import { createSnapshotBoundWorkerPlan } from "../bridge/snapshot_worker_pilot.js";
import type { SnapshotManifest } from "../bridge/repo_snapshot.js";
import type { PromptAnnex } from "../bridge/prompt_annex.js";
import { createFileSnapshotWorkerPlanStore } from "../stores/snapshot_worker_plan_store.js";
import { writeJsonArtifact, writeReceiptArtifact } from "./pilot_artifacts.js";

interface Cea011Report {
  readonly pilot?: {
    readonly manifest?: unknown;
  };
}

interface Cea015Report {
  readonly pilot?: {
    readonly annex_path?: unknown;
  };
}

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const completedAt = new Date().toISOString();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const planId = `cea-016-snapshot-worker-plan-${timestamp}`;
  const reportPath = path.join(projectRoot, "data", "reports", "cea-016_snapshot_bound_worker_prep.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", "2026-07-07-cea-016-snapshot-bound-worker-prep.receipt.md");
  const cea011 = JSON.parse(
    await readFile(path.join(projectRoot, "data", "reports", "cea-011_safe_repo_snapshot_pilot.json"), "utf8"),
  ) as Cea011Report;
  const cea015 = JSON.parse(
    await readFile(path.join(projectRoot, "data", "reports", "cea-015_prompt_packet_compiler.json"), "utf8"),
  ) as Cea015Report;
  const manifestPath = typeof cea011.pilot?.manifest === "string" ? cea011.pilot.manifest : "";
  const annexPath = typeof cea015.pilot?.annex_path === "string" ? cea015.pilot.annex_path : "";
  if (!manifestPath || !annexPath) {
    throw new Error("CEA-011 manifest path or CEA-015 annex path is missing");
  }
  const verifiedManifestPath = assertProjectArtifactPathBoundary(projectRoot, manifestPath, "data/snapshots", "CEA-011 snapshot manifest");
  assertAllowedArtifactFilename(verifiedManifestPath, ["manifest.json"], "CEA-011 snapshot manifest");
  const verifiedAnnexPath = assertProjectArtifactPathBoundary(projectRoot, annexPath, "data/prompt-annexes", "CEA-015 prompt annex");
  assertPromptAnnexFilename(verifiedAnnexPath);

  const manifest = JSON.parse(await readFile(verifiedManifestPath, "utf8")) as SnapshotManifest;
  const annex = JSON.parse(await readFile(verifiedAnnexPath, "utf8")) as PromptAnnex;
  const store = createFileSnapshotWorkerPlanStore(path.join(projectRoot, "data", "worker-pilots"));
  const plan = createSnapshotBoundWorkerPlan({
    planId,
    manifest,
    manifestPath: verifiedManifestPath,
    annex,
    annexRef: verifiedAnnexPath,
  });
  const planPath = await store.write(plan);

  const pilot = {
    result: "PASS",
    task_id: "CEA-016",
    plan_id: plan.planId,
    plan_path: planPath,
    mode: plan.mode,
    snapshot_id: plan.snapshotId,
    worker_cwd: plan.workerCwd,
    annex_id: plan.annexId,
    sandbox_policy: plan.sandboxPolicy,
    worker_cwd_policy: plan.boundary.workerCwdPolicy,
    direct_real_repo: plan.boundary.directRealRepo,
    auto_injection: plan.boundary.autoInjection,
    managed_worker_started: plan.boundary.managedWorkerStarted,
    managed_reviewer_started: plan.boundary.managedReviewerStarted,
    validation: plan.validation,
  };
  const report = {
    task_id: "CEA-016",
    title: "Snapshot-Bound Worker Prep",
    result: pilot.result,
    completed_at: completedAt,
    pilot,
    boundary_flags: {
      worker_cwd_policy: pilot.worker_cwd_policy,
      direct_real_repo: pilot.direct_real_repo,
      auto_injection: pilot.auto_injection,
      managed_worker_started: pilot.managed_worker_started,
      managed_reviewer_started: pilot.managed_reviewer_started,
      commit_push_deploy_release_tag: "NOT_USED",
    },
    artifacts: {
      report: reportPath,
      receipt: receiptPath,
      plan: pilot.plan_path,
    },
  };
  await writeJsonArtifact(reportPath, report);
  await writeReceiptArtifact(receiptPath, "CEA-016 Snapshot-Bound Worker Prep Receipt", [
    `result: ${report.result}`,
    `plan_id: ${pilot.plan_id}`,
    `plan_path: ${pilot.plan_path}`,
    `snapshot_id: ${pilot.snapshot_id}`,
    `worker_cwd: ${pilot.worker_cwd}`,
    `direct_real_repo: ${pilot.direct_real_repo}`,
    `auto_injection: ${pilot.auto_injection}`,
  ]);
  console.log(JSON.stringify(report, null, 2));
}

function assertPromptAnnexFilename(annexPath: string): void {
  const filename = path.basename(annexPath);
  if (!filename.endsWith(".prompt-annex.json")) {
    throw new Error(`CEA-015 prompt annex filename is not allowed: ${filename}`);
  }
}

void main().catch((error) => {
  console.error(
    JSON.stringify(
      {
        result: "FAIL",
        reason: error instanceof Error ? error.message : "unknown snapshot Worker prep failure",
      },
      null,
      2,
    ),
  );
  process.exitCode = 1;
});
