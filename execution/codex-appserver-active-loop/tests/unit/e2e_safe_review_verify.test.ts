import { describe, expect, it } from "vitest";
import { verifyE2eSafeReviewEvidence } from "../../src/bridge/e2e_safe_review_verify.js";

describe("E2E evidence verification gate", () => {
  it("passes complete CEA-018 evidence", () => {
    const result = verifyE2eSafeReviewEvidence(validInput());

    expect(result.result).toBe("PASS");
    expect(result.failures).toEqual([]);
  });

  it("fails when forbidden snapshot paths are included", () => {
    const input = validInput();
    const result = verifyE2eSafeReviewEvidence({
      ...input,
      includedPaths: [...input.includedPaths, ".git/config"],
    });

    expect(result.result).toBe("FAIL");
    expect(result.failures.join("\n")).toContain("forbidden_paths_not_included");
  });

  it("requires every CEA-018 artifact to be declared and present", () => {
    const input = validInput();
    const result = verifyE2eSafeReviewEvidence({
      ...input,
      artifactExists: {
        ...input.artifactExists,
        receipt: false,
      },
    });

    expect(result.result).toBe("FAIL");
    expect(result.failures.join("\n")).toContain("artifacts_exist");
    expect(result.failures.join("\n")).toContain("receipt");
  });
});

function validInput(): Parameters<typeof verifyE2eSafeReviewEvidence>[0] {
  return {
    report: {
      task_id: "CEA-018",
      result: "PASS",
      worker_output: { type: "DONE", summary: "ok", evidence: ["snapshot"] },
      reviewer_output: {
        type: "REVIEWER_DECISION",
        decision: "continue",
        reason: "ok",
        next_instruction: "continue",
        constraints: ["snapshot-only"],
        evidence_used: ["worker done"],
      },
      boundary_summary: {
        appServerProcessCwdSnapshot: true,
        workerCwdSnapshot: true,
        reviewerCwdSnapshot: true,
        directRealRepo: "BLOCKED",
        managedWorkerStarted: "STARTED",
        managedReviewerStarted: "STARTED",
      },
      boundary_flags: {
        app_server_process_cwd_snapshot: "YES",
        direct_real_repo: "BLOCKED",
        command_exec: "NOT_USED",
        file_write: "NOT_USED",
        secrets_read: "NOT_USED",
        commit_push_deploy_release_tag: "NOT_USED",
      },
      counts: {
        snapshot_included_files: 2,
        snapshot_excluded_files: 1,
        policy_decisions: 0,
      },
      policy_decisions: [],
    },
    artifactExists: {
      report: true,
      receipt: true,
      events: true,
      snapshot_manifest: true,
      snapshot_exclusions: true,
      ledger: true,
      packet: true,
      approval: true,
      annex: true,
      plan: true,
    },
    includedPaths: ["src/index.ts", "docs/README.md"],
    excludedPaths: ["docs/.gitkeep"],
    eventMethodCounts: {
      "snapshot/exported": 1,
      "thread/start/result": 2,
      "turn/start/result": 2,
      "turn/completed": 2,
      "structured-output/parsed": 2,
    },
    eventTypeCounts: {
      REPORT_WRITTEN: 1,
      RECEIPT_WRITTEN: 1,
    },
    stderrErrorCount: 0,
  };
}
