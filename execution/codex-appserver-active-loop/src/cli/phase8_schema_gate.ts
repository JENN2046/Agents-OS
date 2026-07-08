import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { evaluatePhase8SchemaGate, type Phase8SchemaGateFile } from "../bridge/phase8_schema_gate.js";
import { safeJoin } from "../stores/safe_path.js";

const scanTargets = [
  { path: "src/generated/appserver/v2/SandboxPolicy.ts", kind: "generated_type" },
  { path: "src/generated/appserver/v2/TurnStartParams.ts", kind: "generated_type" },
  { path: "src/generated/appserver/v2/ThreadStartParams.ts", kind: "generated_type" },
  { path: "src/generated/appserver/v2/CommandExecParams.ts", kind: "generated_type" },
  { path: "schemas/appserver/v2/TurnStartParams.json", kind: "json_schema" },
  { path: "schemas/appserver/v2/ThreadStartParams.json", kind: "json_schema" },
  { path: "schemas/appserver/v2/CommandExecParams.json", kind: "json_schema" },
] as const satisfies readonly { readonly path: string; readonly kind: Phase8SchemaGateFile["kind"] }[];

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const completedAt = new Date().toISOString();
  const timestamp = completedAt.replace(/[-:.TZ]/g, "").slice(0, 14);
  const jobId = `cea-020-phase8-schema-gate-${timestamp}`;
  const reportPath = path.join(projectRoot, "data", "reports", "cea-020_phase8_schema_gate.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", "2026-07-07-cea-020-phase8-schema-gate.receipt.md");

  const scanned = await Promise.all(
    scanTargets.map(async (target) => {
      const absolutePath = path.join(projectRoot, target.path);
      const text = await readFile(absolutePath, "utf8");
      return {
        ...target,
        absolutePath,
        text,
        sha256: sha256(text),
        bytes: Buffer.byteLength(text, "utf8"),
      };
    }),
  );
  const gate = evaluatePhase8SchemaGate(
    scanned.map((file) => ({
      path: file.path,
      kind: file.kind,
      text: file.text,
    })),
  );

  const report = {
    task_id: "CEA-020",
    title: "Phase 8 Unlock Watcher / Schema Gate",
    result: gate.status === "BLOCKED" ? "PASS_WITH_PHASE8_BLOCKED" : "PASS_UNLOCK_CANDIDATE_REVIEW_REQUIRED",
    completed_at: completedAt,
    job_id: jobId,
    gate_status: gate.status,
    phase8_decision: gate.phase8Decision,
    readable_root_supported: gate.readableRootSupported,
    reason: gate.reason,
    scan_scope: scanned.map((file) => ({
      path: file.path,
      kind: file.kind,
      sha256: file.sha256,
      bytes: file.bytes,
    })),
    findings: {
      unlock_candidates: gate.unlockCandidates,
      non_unlock_fields: gate.nonUnlockFindings,
    },
    counts: {
      scanned_files: scanned.length,
      unlock_candidates: gate.unlockCandidates.length,
      non_unlock_fields: gate.nonUnlockFindings.length,
    },
    boundary_flags: {
      app_server_started: "NOT_STARTED",
      managed_worker_started: "NOT_STARTED",
      managed_reviewer_started: "NOT_STARTED",
      direct_real_repo: "BLOCKED",
      schema_files_read_by_gate: "YES",
      managed_real_repo_read: "NOT_USED",
      secrets_read: "NOT_USED",
      command_exec_api: "NOT_USED",
      file_write_scope: "REPORT_AND_RECEIPT_ONLY",
      commit_push_deploy_release_tag: "NOT_USED",
    },
    artifacts: {
      report: reportPath,
      receipt: receiptPath,
    },
    next_recommended_step:
      gate.status === "BLOCKED"
        ? "Continue snapshot-bound safe review only; rerun this gate after App Server schema regeneration or upgrade."
        : "Human review must confirm the candidate field semantics before authorizing any Phase 8 real repository pilot.",
  };

  await writeJson(reportPath, report);
  await writeReceipt(receiptPath, report);
  console.log(JSON.stringify(report, null, 2));
}

function sha256(text: string): string {
  return createHash("sha256").update(text).digest("hex").toUpperCase();
}

async function writeJson(filePath: string, value: unknown): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function writeReceipt(
  filePath: string,
  report: {
    readonly result: string;
    readonly job_id: string;
    readonly gate_status: string;
    readonly phase8_decision: string;
    readonly readable_root_supported: boolean;
    readonly reason: string;
    readonly counts: { readonly scanned_files: number; readonly unlock_candidates: number; readonly non_unlock_fields: number };
    readonly artifacts: { readonly report: string; readonly receipt: string };
    readonly boundary_flags: { readonly direct_real_repo: string; readonly managed_worker_started: string; readonly managed_reviewer_started: string };
  },
): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const lines = [
    "# CEA-020 Phase 8 Schema Gate Receipt",
    "",
    `result: ${report.result}`,
    `job_id: ${report.job_id}`,
    `gate_status: ${report.gate_status}`,
    `phase8_decision: ${report.phase8_decision}`,
    `readable_root_supported: ${report.readable_root_supported}`,
    `reason: ${report.reason}`,
    "",
    "## Counts",
    `- scanned_files: ${report.counts.scanned_files}`,
    `- unlock_candidates: ${report.counts.unlock_candidates}`,
    `- non_unlock_fields: ${report.counts.non_unlock_fields}`,
    "",
    "## Boundary",
    `- direct_real_repo: ${report.boundary_flags.direct_real_repo}`,
    `- managed_worker_started: ${report.boundary_flags.managed_worker_started}`,
    `- managed_reviewer_started: ${report.boundary_flags.managed_reviewer_started}`,
    `- live_sessions_started_by_this_gate: false`,
    "",
    "## Artifacts",
    `- report: ${report.artifacts.report}`,
    `- receipt: ${report.artifacts.receipt}`,
    "",
  ];
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, lines.join("\n"), "utf8");
}

void main();
