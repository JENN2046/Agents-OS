import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { resolveCommanderEvidenceReceiptPath } from "../../src/bridge/commander_evidence_receipts.js";

const tmpRoot = path.join(process.cwd(), "data", "tmp", "commander-evidence-receipts");

describe("Commander evidence receipt boundaries", () => {
  it("accepts only the expected receipt artifact path", async () => {
    const projectRoot = path.join(tmpRoot, `case-${Date.now()}`);
    const expectedRelative = "data/receipts/2026-07-07-cea-018-e2e-safe-review-loop.receipt.md";
    const expectedPath = path.join(projectRoot, expectedRelative);
    const outsidePath = path.join(tmpRoot, `outside-${Date.now()}.receipt.md`);
    await rm(projectRoot, { force: true, recursive: true });
    await mkdir(path.dirname(expectedPath), { recursive: true });
    await writeFile(expectedPath, "ok\n", "utf8");
    await writeFile(outsidePath, "outside\n", "utf8");

    expect(
      resolveCommanderEvidenceReceiptPath({
        projectRoot,
        taskId: "CEA-018",
        reportReceiptPath: expectedPath,
        expectedReceiptRelativePath: expectedRelative,
      }),
    ).toEqual({ receiptPath: expectedPath, boundaryValid: true });

    expect(
      resolveCommanderEvidenceReceiptPath({
        projectRoot,
        taskId: "CEA-018",
        reportReceiptPath: outsidePath,
        expectedReceiptRelativePath: expectedRelative,
      }),
    ).toEqual({ receiptPath: expectedPath, boundaryValid: false });
  });
});
