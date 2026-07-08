import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  assertSyntheticWorkspaceRoot,
  blockedOutputSchema,
  createReadOnlySyntheticSandboxPolicy,
  createSyntheticTurnStartParams,
  reviewerDecisionSchema,
  validateStructuredLoopOutput,
  workerDoneSchema,
  workerNeedReviewerSchema,
} from "../../src/bridge/event_contracts.js";

describe("event contracts", () => {
  it("encodes required structured output schemas", () => {
    expect(workerNeedReviewerSchema.required).toContain("recommended_next_action");
    expect(reviewerDecisionSchema.properties.decision).toEqual({
      enum: ["continue", "revise", "block", "request_human_gate"],
    });
    expect(workerDoneSchema.properties.type).toEqual({ type: "string", const: "DONE" });
    expect(blockedOutputSchema.properties.type).toEqual({ type: "string", const: "BLOCKED" });
  });

  it("validates structured loop outputs strictly", () => {
    expect(
      validateStructuredLoopOutput({
        type: "NEED_REVIEWER",
        problem_type: "architecture",
        question: "Which route?",
        evidence: ["sample.txt"],
        proposed_options: ["continue"],
        recommended_next_action: "ask reviewer",
      }),
    ).toBe(true);
    expect(
      validateStructuredLoopOutput({
        type: "REVIEWER_DECISION",
        decision: "continue",
        reason: "safe",
        next_instruction: "finish",
        constraints: ["read-only"],
        evidence_used: ["sample.txt"],
      }),
    ).toBe(true);
    expect(validateStructuredLoopOutput({ type: "DONE", summary: "ok", evidence: ["receipt"] })).toBe(true);
    expect(validateStructuredLoopOutput({ type: "DONE", summary: "ok", evidence: [], extra: true })).toBe(false);
  });

  it("builds read-only synthetic turn params", () => {
    const root = path.join(process.cwd(), "data", "synthetic-workspace");
    const params = createSyntheticTurnStartParams({
      threadId: "thread-1",
      syntheticWorkspaceRoot: root,
      prompt: "inspect",
      outputSchema: workerNeedReviewerSchema,
    });

    expect(params.cwd).toBe(root);
    expect(params.sandboxPolicy).toEqual({ type: "readOnly", networkAccess: false });
    expect(params.outputSchema).toBe(workerNeedReviewerSchema);
  });

  it("rejects non-synthetic readable roots", () => {
    expect(() => assertSyntheticWorkspaceRoot(path.join(process.cwd(), "src"))).toThrow("synthetic-workspace");
  });

  it("keeps synthetic workspace harmless", async () => {
    const root = path.join(process.cwd(), "data", "synthetic-workspace");
    const files = await listFiles(root);
    expect(files.map((file) => path.relative(root, file).replaceAll("\\", "/")).sort()).toEqual([
      ".gitkeep",
      "README.md",
      "sample.txt",
      "src/example.ts",
    ]);
    for (const file of files) {
      const relative = path.relative(root, file).replaceAll("\\", "/").toLowerCase();
      expect(relative).not.toMatch(/\.env|secret|credential|token|cookie|\.ssh|state-private/);
      const content = await readFile(file, "utf8");
      expect(content.toLowerCase()).not.toMatch(/bearer\s+[a-z0-9]|sk-[a-z0-9]/);
    }
  });

  it("creates the exact read-only sandbox policy", () => {
    expect(createReadOnlySyntheticSandboxPolicy()).toEqual({ type: "readOnly", networkAccess: false });
  });
});

async function listFiles(root: string): Promise<string[]> {
  const entries = await readdir(root, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map(async (entry) => {
      const fullPath = path.join(root, entry.name);
      return entry.isDirectory() ? listFiles(fullPath) : [fullPath];
    }),
  );
  return nested.flat();
}
