import { describe, expect, it } from "vitest";
import { createCommanderReadinessMatrix, type CommanderEvidenceItem } from "../../src/bridge/commander_readiness_matrix.js";

describe("Commander closeout readiness matrix", () => {
  it("marks the snapshot review lane ready while Phase 8 direct real repo remains schema-blocked", () => {
    const matrix = createCommanderReadinessMatrix(allEvidence());

    expect(matrix.rows).toHaveLength(11);
    expect(matrix.summary).toMatchObject({
      safeSnapshotReviewLane: "READY",
      commanderReviewPackage: "READY",
      phase8DirectRealRepo: "BLOCKED_BY_SCHEMA",
      availableRows: 11,
      partialRows: 0,
      missingRows: 0,
    });
    expect(matrix.blockingItems).toEqual([
      "Phase 8 direct real repository managed-session pilot remains blocked because restricted readable roots are absent.",
    ]);
  });

  it("does not auto-unlock Phase 8 when a readable-root candidate appears", () => {
    const matrix = createCommanderReadinessMatrix(
      allEvidence({
        "CEA-020": {
          result: "PASS_WITH_REVIEW_REQUIRED",
          gateStatus: "UNLOCK_CANDIDATE",
          phase8Decision: "REVIEW_REQUIRED",
          readableRootSupported: true,
        },
      }),
    );

    expect(matrix.summary.phase8DirectRealRepo).toBe("REVIEW_REQUIRED");
    expect(matrix.blockingItems).toEqual([
      "Phase 8 is not automatically unlocked; human review and fresh authorization are still required.",
    ]);
    expect(matrix.phase8UnlockConditions).toEqual(
      expect.arrayContaining([
        "Human semantic review confirms the field constrains readable roots and is not merely cwd, readOnly, sandboxPolicy, writableRoots, or a write-only boundary.",
        "A new explicit Phase 8 authorization package names the target root, readable roots, denylist, evidence location, and stop conditions.",
      ]),
    );
  });

  it("keeps the safe snapshot review lane partial when CEA-016 live Worker evidence is missing", () => {
    const matrix = createCommanderReadinessMatrix(allEvidence().filter((item) => item.taskId !== "CEA-016-LIVE"));
    const row = matrix.rows.find((candidate) => candidate.taskId === "CEA-016");

    expect(row?.status).toBe("MISSING");
    expect(row?.notes).toEqual(expect.arrayContaining(["Missing evidence for: CEA-016-LIVE"]));
    expect(matrix.summary.safeSnapshotReviewLane).toBe("PARTIAL");
    expect(matrix.summary.missingRows).toBe(1);
  });

  it("keeps a row partial when its receipt is missing", () => {
    const matrix = createCommanderReadinessMatrix(
      allEvidence({
        "CEA-021": {
          receiptExists: false,
        },
      }),
    );
    const row = matrix.rows.find((candidate) => candidate.taskId === "CEA-021");

    expect(row?.status).toBe("PARTIAL");
    expect(row?.notes).toEqual(expect.arrayContaining(["One or more receipts are missing."]));
    expect(matrix.summary.commanderReviewPackage).toBe("PARTIAL");
    expect(matrix.summary.partialRows).toBe(1);
  });
});

function allEvidence(overrides: Partial<Record<string, Partial<CommanderEvidenceItem>>> = {}): CommanderEvidenceItem[] {
  return [
    evidence("CEA-011"),
    evidence("CEA-012"),
    evidence("CEA-013"),
    evidence("CEA-014"),
    evidence("CEA-015"),
    evidence("CEA-016"),
    evidence("CEA-016-LIVE", { title: "CEA-016 live Worker run" }),
    evidence("CEA-017"),
    evidence("CEA-018"),
    evidence("CEA-019"),
    evidence("CEA-020", {
      result: "PASS_WITH_PHASE8_BLOCKED",
      gateStatus: "BLOCKED",
      phase8Decision: "BLOCK",
      readableRootSupported: false,
    }),
    evidence("CEA-021"),
  ].map((item) => ({ ...item, ...overrides[item.taskId] }));
}

function evidence(taskId: string, overrides: Partial<CommanderEvidenceItem> = {}): CommanderEvidenceItem {
  return {
    taskId,
    title: taskId,
    result: "PASS",
    reportPath: `A:/repo/data/reports/${taskId}.json`,
    receiptPath: `A:/repo/data/receipts/${taskId}.receipt.md`,
    receiptExists: true,
    ...overrides,
  };
}
