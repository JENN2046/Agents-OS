import path from "node:path";
import { exportSafeRepoSnapshot, defaultSnapshotAllowlist } from "../bridge/repo_snapshot.js";

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const jobId = `cea-011-safe-snapshot-${timestamp}`;
  const snapshotRoot = path.join(projectRoot, "data", "snapshots", jobId);
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
  console.log(JSON.stringify(output, null, 2));
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
