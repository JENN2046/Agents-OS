import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { createCommanderReadinessMatrix, type CommanderEvidenceItem } from "../bridge/commander_readiness_matrix.js";
import { safeJoin } from "../stores/safe_path.js";

const expectedEvidence = [
  ["CEA-011", "data/reports/cea-011_safe_repo_snapshot_pilot.json", "data/receipts/2026-07-07-cea-011-safe-repo-snapshot-pilot.receipt.md"],
  ["CEA-012", "data/reports/cea-012_context_ledger_pilot.json", "data/receipts/2026-07-07-cea-012-context-ledger-pilot.receipt.md"],
  ["CEA-013", "data/reports/cea-013_context_promotion_gate.json", "data/receipts/2026-07-07-cea-013-context-promotion-gate.receipt.md"],
  ["CEA-014", "data/reports/cea-014_promotion_approval_receipt.json", "data/receipts/2026-07-07-cea-014-promotion-approval-receipt.receipt.md"],
  ["CEA-015", "data/reports/cea-015_prompt_packet_compiler.json", "data/receipts/2026-07-07-cea-015-prompt-packet-compiler.receipt.md"],
  ["CEA-016", "data/reports/cea-016_snapshot_bound_worker_prep.json", "data/receipts/2026-07-07-cea-016-snapshot-bound-worker-prep.receipt.md"],
  ["CEA-016-LIVE", "data/reports/cea-016_live_snapshot_worker_run.json", "data/receipts/2026-07-07-cea-016-live-snapshot-worker-run.receipt.md"],
  ["CEA-017", "data/reports/cea-017_snapshot_bound_reviewer_pilot.json", "data/receipts/2026-07-07-cea-017-snapshot-bound-reviewer-pilot.receipt.md"],
  ["CEA-018", "data/reports/cea-018_e2e_safe_review_loop.json", "data/receipts/2026-07-07-cea-018-e2e-safe-review-loop.receipt.md"],
  ["CEA-019", "data/reports/cea-019_e2e_evidence_verification_gate.json", "data/receipts/2026-07-07-cea-019-e2e-evidence-verification-gate.receipt.md"],
  ["CEA-020", "data/reports/cea-020_phase8_schema_gate.json", "data/receipts/2026-07-07-cea-020-phase8-schema-gate.receipt.md"],
  ["CEA-021", "data/reports/cea-021_snapshot_review_package_publisher.json", "data/receipts/2026-07-08-cea-021-snapshot-review-package-publisher.receipt.md"],
] as const;

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const completedAt = new Date().toISOString();
  const reportPath = path.join(projectRoot, "data", "reports", "cea-022_commander_closeout_readiness_matrix.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", `${formatDateForReceipt(new Date(completedAt))}-cea-022-commander-closeout-readiness-matrix.receipt.md`);
  const evidence = await Promise.all(
    expectedEvidence.map(async ([fallbackTaskId, reportRelativePath, receiptRelativePath]) => {
      return readEvidenceItem(projectRoot, fallbackTaskId, reportRelativePath, receiptRelativePath);
    }),
  );
  const matrix = createCommanderReadinessMatrix(evidence);
  const report = {
    task_id: "CEA-022",
    title: "Commander Closeout / Readiness Matrix",
    result: matrix.summary.safeSnapshotReviewLane === "READY" && matrix.summary.commanderReviewPackage === "READY" ? "PASS" : "PARTIAL",
    completed_at: completedAt,
    evidence_range: "CEA-011..CEA-021",
    matrix,
    commander_decision: {
      safe_snapshot_review_lane: matrix.summary.safeSnapshotReviewLane,
      commander_external_review_package: matrix.summary.commanderReviewPackage,
      phase8_direct_real_repo_pilot: matrix.summary.phase8DirectRealRepo,
      final_note:
        matrix.summary.phase8DirectRealRepo === "BLOCKED_BY_SCHEMA"
          ? "Snapshot-bound safe review is ready; direct real-repository Phase 8 remains blocked pending restricted readable-root schema support."
          : "Readable-root schema support may exist; human semantic review and fresh authorization are required before Phase 8.",
    },
    boundary_flags: {
      app_server_started: "NOT_STARTED",
      managed_worker_started: "NOT_STARTED",
      managed_reviewer_started: "NOT_STARTED",
      direct_real_repo: "BLOCKED",
      raw_events_read: "NOT_USED",
      secrets_read: "NOT_USED",
      command_exec_api: "NOT_USED",
      file_write_scope: "REPORT_AND_RECEIPT_ONLY",
      commit_push_deploy_release_tag: "NOT_USED",
    },
    artifacts: {
      report: reportPath,
      receipt: receiptPath,
    },
  };

  await writeJson(reportPath, report);
  await writeReceipt(receiptPath, report);
  console.log(JSON.stringify(report, null, 2));
}

async function readEvidenceItem(
  projectRoot: string,
  fallbackTaskId: string,
  reportRelativePath: string,
  receiptRelativePath: string,
): Promise<CommanderEvidenceItem> {
  const reportPath = path.join(projectRoot, reportRelativePath);
  const report = (await readJson(reportPath)) as Record<string, unknown>;
  const receiptFromReport = getReportArtifactPath(report, "receipt");
  const receiptPath = receiptFromReport ?? path.join(projectRoot, receiptRelativePath);
  return {
    taskId: fallbackTaskId,
    title: typeof report.title === "string" ? report.title : fallbackTaskId,
    result: typeof report.result === "string" ? report.result : "UNKNOWN",
    reportPath,
    receiptPath,
    receiptExists: await existsFile(receiptPath),
    gateStatus: typeof report.gate_status === "string" ? report.gate_status : undefined,
    phase8Decision: typeof report.phase8_decision === "string" ? report.phase8_decision : undefined,
    readableRootSupported: typeof report.readable_root_supported === "boolean" ? report.readable_root_supported : undefined,
  };
}

function getReportArtifactPath(report: Record<string, unknown>, key: string): string | undefined {
  const artifacts = report.artifacts;
  if (!artifacts || typeof artifacts !== "object") return undefined;
  const value = (artifacts as Record<string, unknown>)[key];
  return typeof value === "string" ? value : undefined;
}

async function existsFile(filePath: string): Promise<boolean> {
  try {
    const fileStat = await stat(filePath);
    return fileStat.isFile();
  } catch {
    return false;
  }
}

async function readJson(filePath: string): Promise<unknown> {
  return JSON.parse(await readFile(filePath, "utf8")) as unknown;
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
    readonly evidence_range: string;
    readonly matrix: ReturnType<typeof createCommanderReadinessMatrix>;
    readonly commander_decision: {
      readonly safe_snapshot_review_lane: string;
      readonly commander_external_review_package: string;
      readonly phase8_direct_real_repo_pilot: string;
      readonly final_note: string;
    };
    readonly artifacts: { readonly report: string; readonly receipt: string };
  },
): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const lines = [
    "# CEA-022 Commander Closeout / Readiness Matrix Receipt",
    "",
    `result: ${report.result}`,
    `evidence_range: ${report.evidence_range}`,
    "",
    "## Summary",
    `- safe_snapshot_review_lane: ${report.commander_decision.safe_snapshot_review_lane}`,
    `- commander_external_review_package: ${report.commander_decision.commander_external_review_package}`,
    `- phase8_direct_real_repo_pilot: ${report.commander_decision.phase8_direct_real_repo_pilot}`,
    `- available_rows: ${report.matrix.summary.availableRows}`,
    `- partial_rows: ${report.matrix.summary.partialRows}`,
    `- missing_rows: ${report.matrix.summary.missingRows}`,
    "",
    "## Phase 8 Unlock Conditions",
    ...report.matrix.phase8UnlockConditions.map((condition) => `- ${condition}`),
    "",
    "## Final Note",
    report.commander_decision.final_note,
    "",
    "## Artifacts",
    `- report: ${report.artifacts.report}`,
    `- receipt: ${report.artifacts.receipt}`,
    "",
  ];
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, lines.join("\n"), "utf8");
}

function formatDateForReceipt(date: Date): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const year = parts.find((part) => part.type === "year")?.value ?? "0000";
  const month = parts.find((part) => part.type === "month")?.value ?? "00";
  const day = parts.find((part) => part.type === "day")?.value ?? "00";
  return `${year}-${month}-${day}`;
}

void main();
