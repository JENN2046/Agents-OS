import { readFile } from "node:fs/promises";
import path from "node:path";
import { createSnapshotBoundWorkerPlan } from "../bridge/snapshot_worker_pilot.js";
import type { SnapshotManifest } from "../bridge/repo_snapshot.js";
import type { PromptAnnex } from "../bridge/prompt_annex.js";
import { createFileSnapshotWorkerPlanStore } from "../stores/snapshot_worker_plan_store.js";

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
  const timestamp = new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14);
  const planId = `cea-016-snapshot-worker-plan-${timestamp}`;
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

  const manifest = JSON.parse(await readFile(manifestPath, "utf8")) as SnapshotManifest;
  const annex = JSON.parse(await readFile(annexPath, "utf8")) as PromptAnnex;
  const store = createFileSnapshotWorkerPlanStore(path.join(projectRoot, "data", "worker-pilots"));
  const plan = createSnapshotBoundWorkerPlan({
    planId,
    manifest,
    manifestPath,
    annex,
    annexRef: annexPath,
  });
  const planPath = await store.write(plan);

  console.log(
    JSON.stringify(
      {
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
      },
      null,
      2,
    ),
  );
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
