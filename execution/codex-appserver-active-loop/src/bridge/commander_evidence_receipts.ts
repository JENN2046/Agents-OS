import path from "node:path";
import { assertAllowedArtifactFilename, assertProjectArtifactPathBoundary } from "./artifact_path_boundary.js";

export interface CommanderReceiptResolution {
  readonly receiptPath: string;
  readonly boundaryValid: boolean;
}

export function resolveCommanderEvidenceReceiptPath(input: {
  readonly projectRoot: string;
  readonly taskId: string;
  readonly reportReceiptPath: string | undefined;
  readonly expectedReceiptRelativePath: string;
}): CommanderReceiptResolution {
  const expectedReceiptPath = path.resolve(input.projectRoot, input.expectedReceiptRelativePath);
  if (!input.reportReceiptPath) {
    return { receiptPath: expectedReceiptPath, boundaryValid: false };
  }

  try {
    const verifiedReceiptPath = assertProjectArtifactPathBoundary(
      input.projectRoot,
      input.reportReceiptPath,
      "data/receipts",
      `${input.taskId} receipt artifact`,
    );
    assertAllowedReceiptFilename(input.taskId, verifiedReceiptPath, expectedReceiptPath);
    if (!isAllowedReceiptPath(input.projectRoot, input.taskId, verifiedReceiptPath, expectedReceiptPath)) {
      throw new Error(`${input.taskId} receipt artifact must match the expected receipt path`);
    }
    return { receiptPath: verifiedReceiptPath, boundaryValid: true };
  } catch {
    return { receiptPath: expectedReceiptPath, boundaryValid: false };
  }
}

function assertAllowedReceiptFilename(taskId: string, receiptPath: string, expectedReceiptPath: string): void {
  if (taskId !== "CEA-021") {
    assertAllowedArtifactFilename(receiptPath, [path.basename(expectedReceiptPath)], `${taskId} receipt artifact`);
    return;
  }
  const filename = path.basename(receiptPath);
  if (filename !== path.basename(expectedReceiptPath) && !/^\d{4}-\d{2}-\d{2}-cea-021-snapshot-review-package-publisher\.receipt\.md$/.test(filename)) {
    throw new Error(`${taskId} receipt artifact filename is not allowed: ${filename}`);
  }
}

function isAllowedReceiptPath(projectRoot: string, taskId: string, receiptPath: string, expectedReceiptPath: string): boolean {
  if (taskId !== "CEA-021") {
    return receiptPath === expectedReceiptPath;
  }
  const receiptsRoot = path.resolve(projectRoot, "data", "receipts");
  if (path.dirname(receiptPath) !== receiptsRoot) {
    return false;
  }
  const filename = path.basename(receiptPath);
  return (
    filename === path.basename(expectedReceiptPath) ||
    /^\d{4}-\d{2}-\d{2}-cea-021-snapshot-review-package-publisher\.receipt\.md$/.test(filename)
  );
}
