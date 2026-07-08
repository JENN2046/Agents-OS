import { validateStructuredLoopOutput } from "./event_contracts.js";

export interface E2eEvidenceVerificationInput {
  readonly report: unknown;
  readonly artifactExists: Readonly<Record<string, boolean>>;
  readonly includedPaths: readonly string[];
  readonly excludedPaths: readonly string[];
  readonly eventMethodCounts: Readonly<Record<string, number>>;
  readonly eventTypeCounts: Readonly<Record<string, number>>;
  readonly stderrErrorCount: number;
}

export interface E2eEvidenceCheck {
  readonly name: string;
  readonly passed: boolean;
  readonly detail: string;
}

export interface E2eEvidenceVerificationResult {
  readonly result: "PASS" | "FAIL";
  readonly checks: readonly E2eEvidenceCheck[];
  readonly failures: readonly string[];
  readonly counts: {
    readonly artifacts: number;
    readonly includedPaths: number;
    readonly excludedPaths: number;
    readonly eventMethods: number;
  };
}

const forbiddenIncludedPathTerms = [".git", "node_modules", "dist", "state-private", ".env", "config.env", "secrets"] as const;

export function verifyE2eSafeReviewEvidence(input: E2eEvidenceVerificationInput): E2eEvidenceVerificationResult {
  const checks: E2eEvidenceCheck[] = [];
  const add = (name: string, passed: boolean, detail: string): void => {
    checks.push({ name, passed, detail });
  };

  const report = isRecord(input.report) ? input.report : {};
  add("report_result_pass", report.result === "PASS", `result=${String(report.result)}`);
  add("task_id_cea_018", report.task_id === "CEA-018", `task_id=${String(report.task_id)}`);

  const workerOutput = isRecord(report.worker_output) ? report.worker_output : undefined;
  const reviewerOutput = isRecord(report.reviewer_output) ? report.reviewer_output : undefined;
  add(
    "worker_done_output",
    Boolean(workerOutput && validateStructuredLoopOutput(workerOutput) && workerOutput.type === "DONE"),
    `worker_type=${String(workerOutput?.type)}`,
  );
  add(
    "reviewer_continue_output",
    Boolean(
      reviewerOutput &&
        validateStructuredLoopOutput(reviewerOutput) &&
        reviewerOutput.type === "REVIEWER_DECISION" &&
        reviewerOutput.decision === "continue",
    ),
    `reviewer_type=${String(reviewerOutput?.type)} decision=${String(reviewerOutput?.decision)}`,
  );

  const summary = isRecord(report.boundary_summary) ? report.boundary_summary : {};
  add("app_server_cwd_snapshot", summary.appServerProcessCwdSnapshot === true, `value=${String(summary.appServerProcessCwdSnapshot)}`);
  add("worker_cwd_snapshot", summary.workerCwdSnapshot === true, `value=${String(summary.workerCwdSnapshot)}`);
  add("reviewer_cwd_snapshot", summary.reviewerCwdSnapshot === true, `value=${String(summary.reviewerCwdSnapshot)}`);
  add("direct_real_repo_blocked", summary.directRealRepo === "BLOCKED", `value=${String(summary.directRealRepo)}`);
  add("managed_sessions_started", summary.managedWorkerStarted === "STARTED" && summary.managedReviewerStarted === "STARTED", "worker+reviewer");

  const boundaryFlags = isRecord(report.boundary_flags) ? report.boundary_flags : {};
  add("boundary_flags_snapshot", boundaryFlags.app_server_process_cwd_snapshot === "YES", `value=${String(boundaryFlags.app_server_process_cwd_snapshot)}`);
  add("boundary_flags_direct_repo_blocked", boundaryFlags.direct_real_repo === "BLOCKED", `value=${String(boundaryFlags.direct_real_repo)}`);
  add("boundary_flags_no_side_effects", hasNoForbiddenSideEffects(boundaryFlags), "command/file/secrets/git delivery not used");

  const counts = isRecord(report.counts) ? report.counts : {};
  const policyDecisionCount = typeof counts.policy_decisions === "number" ? counts.policy_decisions : undefined;
  const policyDecisions = Array.isArray(report.policy_decisions) ? report.policy_decisions : [];
  add("policy_decisions_zero", policyDecisionCount === 0 && policyDecisions.length === 0, `count=${String(policyDecisionCount)} array=${policyDecisions.length}`);

  const missingArtifacts = Object.entries(input.artifactExists)
    .filter(([, exists]) => !exists)
    .map(([name]) => name);
  add("artifacts_exist", missingArtifacts.length === 0, missingArtifacts.length === 0 ? "all artifacts exist" : `missing=${missingArtifacts.join(",")}`);

  const forbiddenIncluded = input.includedPaths.filter((relativePath) => {
    const lower = relativePath.toLowerCase();
    return forbiddenIncludedPathTerms.some((term) => lower.includes(term));
  });
  add("forbidden_paths_not_included", forbiddenIncluded.length === 0, forbiddenIncluded.length === 0 ? "none" : forbiddenIncluded.join(","));

  add("snapshot_manifest_counts_match", countsMatch(counts.snapshot_included_files, input.includedPaths.length), `included=${input.includedPaths.length}`);
  add("snapshot_exclusion_counts_match", countsMatch(counts.snapshot_excluded_files, input.excludedPaths.length), `excluded=${input.excludedPaths.length}`);
  add("exclusion_report_present", input.excludedPaths.length > 0, `excluded=${input.excludedPaths.length}`);

  add("event_snapshot_exported", countAtLeast(input.eventMethodCounts, "snapshot/exported", 1), `count=${countOf(input.eventMethodCounts, "snapshot/exported")}`);
  add("event_worker_reviewer_threads_started", countAtLeast(input.eventMethodCounts, "thread/start/result", 2), `count=${countOf(input.eventMethodCounts, "thread/start/result")}`);
  add("event_worker_reviewer_turns_started", countAtLeast(input.eventMethodCounts, "turn/start/result", 2), `count=${countOf(input.eventMethodCounts, "turn/start/result")}`);
  add("event_worker_reviewer_turns_completed", countAtLeast(input.eventMethodCounts, "turn/completed", 2), `count=${countOf(input.eventMethodCounts, "turn/completed")}`);
  add("event_structured_outputs_parsed", countAtLeast(input.eventMethodCounts, "structured-output/parsed", 2), `count=${countOf(input.eventMethodCounts, "structured-output/parsed")}`);
  add("event_report_receipt_written", countAtLeast(input.eventTypeCounts, "REPORT_WRITTEN", 1) && countAtLeast(input.eventTypeCounts, "RECEIPT_WRITTEN", 1), "report+receipt");
  add("stderr_no_error_flag", input.stderrErrorCount === 0, `stderr_error_count=${input.stderrErrorCount}`);

  const failures = checks.filter((check) => !check.passed).map((check) => `${check.name}: ${check.detail}`);
  return {
    result: failures.length === 0 ? "PASS" : "FAIL",
    checks,
    failures,
    counts: {
      artifacts: Object.keys(input.artifactExists).length,
      includedPaths: input.includedPaths.length,
      excludedPaths: input.excludedPaths.length,
      eventMethods: Object.keys(input.eventMethodCounts).length,
    },
  };
}

function hasNoForbiddenSideEffects(flags: Readonly<Record<string, unknown>>): boolean {
  return (
    flags.command_exec === "NOT_USED" &&
    flags.file_write === "NOT_USED" &&
    flags.secrets_read === "NOT_USED" &&
    flags.commit_push_deploy_release_tag === "NOT_USED"
  );
}

function countsMatch(reportCount: unknown, actual: number): boolean {
  return typeof reportCount === "number" && reportCount === actual;
}

function countAtLeast(counts: Readonly<Record<string, number>>, key: string, minimum: number): boolean {
  return countOf(counts, key) >= minimum;
}

function countOf(counts: Readonly<Record<string, number>>, key: string): number {
  return counts[key] ?? 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
