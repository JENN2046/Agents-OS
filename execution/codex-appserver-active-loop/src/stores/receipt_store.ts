import { mkdir, writeFile } from "node:fs/promises";
import { assertSafeJobId, safeJoin } from "./safe_path.js";

export interface ReceiptInput {
  readonly jobId: string;
  readonly result: "PASS" | "BLOCK" | "FAIL";
  readonly finalState: string;
  readonly validation: readonly string[];
  readonly artifacts: readonly string[];
  readonly boundaryFlags: Record<string, string>;
  readonly risks?: readonly string[];
}

export interface ReceiptStore {
  write(input: ReceiptInput): Promise<string>;
  pathFor(jobId: string): string;
}

export function createFileReceiptStore(rootDir: string): ReceiptStore {
  return new FileReceiptStore(rootDir);
}

class FileReceiptStore implements ReceiptStore {
  constructor(readonly rootDir: string) {}

  pathFor(jobId: string): string {
    assertSafeJobId(jobId);
    return safeJoin(this.rootDir, `${jobId}.receipt.md`);
  }

  async write(input: ReceiptInput): Promise<string> {
    await mkdir(this.rootDir, { recursive: true });
    const target = this.pathFor(input.jobId);
    await writeFile(target, renderReceipt(input), "utf8");
    return target;
  }
}

function renderReceipt(input: ReceiptInput): string {
  const boundaryLines = Object.entries(input.boundaryFlags)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `- ${key}: ${value}`);
  return [
    `# Active Loop Receipt ${input.jobId}`,
    "",
    `result: ${input.result}`,
    `final_state: ${input.finalState}`,
    "",
    "## Validation",
    ...input.validation.map((item) => `- ${item}`),
    "",
    "## Artifacts",
    ...input.artifacts.map((item) => `- ${item}`),
    "",
    "## Boundary Flags",
    ...boundaryLines,
    "",
    "## Risks",
    ...(input.risks?.length ? input.risks.map((item) => `- ${item}`) : ["- none recorded"]),
    "",
  ].join("\n");
}
