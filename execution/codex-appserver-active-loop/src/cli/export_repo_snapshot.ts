import path from "node:path";
import { exportSafeRepoSnapshot, defaultSnapshotAllowlist } from "../bridge/repo_snapshot.js";
import { writeJsonArtifact, writeReceiptArtifact } from "./pilot_artifacts.js";

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const completedAt = new Date().toISOString();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const jobId = `cea-011-safe-snapshot-${timestamp}`;
  const snapshotRoot = path.join(projectRoot, "data", "snapshots", jobId);
  const reportPath = path.join(projectRoot, "data", "reports", "cea-011_safe_repo_snapshot_pilot.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", "2026-07-07-cea-011-safe-repo-snapshot-pilot.receipt.md");
  const result = await exportSafeRepoSnapshot({
    sourceRoot: projectRoot,
    snapshotRoot,
    allowlist: defaultSnapshotAllowlist,
  });

  const output = {
    result: "PASS",
    job_id: jobId,
    snapshot_root: result.snapshotRoot,
    worker_cwd: result.manifest.workerCwd,
    manifest: result.manifestPath,
    exclusions: result.exclusionReportPath,
    included_file_count: result.manifest.includedFiles.length,
    excluded_file_count: result.manifest.excludedFiles.length,
    phase8_direct_real_repo: "BLOCKED",
    managed_sessions_started: false,
  };
  const report = {
    task_id: "CEA-011",
    title: "Safe Repo Snapshot Pilot",
    result: output.result,
    completed_at: completedAt,
    pilot: output,
    boundary_flags: {
      phase8_direct_real_repo: output.phase8_direct_real_repo,
      managed_sessions_started: output.managed_sessions_started,
      commit_push_deploy_release_tag: "NOT_USED",
    },
    artifacts: {
      report: reportPath,
      receipt: receiptPath,
      manifest: output.manifest,
      exclusions: output.exclusions,
    },
  };
  await writeJsonArtifact(reportPath, report);
  await writeReceiptArtifact(receiptPath, "CEA-011 Safe Repo Snapshot Pilot Receipt", [
    `result: ${report.result}`,
    `job_id: ${output.job_id}`,
    `manifest: ${output.manifest}`,
    `exclusions: ${output.exclusions}`,
    `included_file_count: ${output.included_file_count}`,
    `excluded_file_count: ${output.excluded_file_count}`,
    `phase8_direct_real_repo: ${output.phase8_direct_real_repo}`,
  ]);
  console.log(JSON.stringify(report, null, 2));
}

void main().catch((error) => {
  console.error(
    JSON.stringify(
      {
        result: "BLOCK",
        reason: error instanceof Error ? error.message : "unknown snapshot export failure",
      },
      null,
      2,
    ),
  );
  process.exitCode = 1;
});
