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
    return { receiptPath: expectedReceiptPath, boundaryValid: true };
  }

  try {
    const verifiedReceiptPath = assertProjectArtifactPathBoundary(
      input.projectRoot,
      input.reportReceiptPath,
      "data/receipts",
      `${input.taskId} receipt artifact`,
    );
    assertAllowedArtifactFilename(verifiedReceiptPath, [path.basename(expectedReceiptPath)], `${input.taskId} receipt artifact`);
    if (verifiedReceiptPath !== expectedReceiptPath) {
      throw new Error(`${input.taskId} receipt artifact must match the expected receipt path`);
    }
    return { receiptPath: verifiedReceiptPath, boundaryValid: true };
  } catch {
    return { receiptPath: expectedReceiptPath, boundaryValid: false };
  }
}
