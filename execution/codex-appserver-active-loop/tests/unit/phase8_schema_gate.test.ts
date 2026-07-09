import { describe, expect, it } from "vitest";
import { evaluatePhase8SchemaGate } from "../../src/bridge/phase8_schema_gate.js";

describe("Phase 8 schema gate", () => {
  it("keeps Phase 8 blocked when generated types lack readable roots", () => {
    const result = evaluatePhase8SchemaGate([
      {
        path: "src/generated/appserver/v2/SandboxPolicy.ts",
        kind: "generated_type",
        text: 'export type SandboxPolicy = { "type": "readOnly", networkAccess: boolean } | { "type": "workspaceWrite", writableRoots: Array<string> };',
      },
      {
        path: "src/generated/appserver/v2/TurnStartParams.ts",
        kind: "generated_type",
        text: "export type TurnStartParams = { cwd?: string | null, sandboxPolicy?: SandboxPolicy | null };",
      },
    ]);

    expect(result.status).toBe("BLOCKED");
    expect(result.phase8Decision).toBe("BLOCK");
    expect(result.readableRootSupported).toBe(false);
    expect(result.unlockCandidates).toEqual([]);
    expect(result.nonUnlockFindings.map((finding) => finding.field)).toEqual(
      expect.arrayContaining(["readOnly", "networkAccess", "writableRoots", "cwd", "sandboxPolicy"]),
    );
  });

  it("does not treat writable roots as a readable-root unlock", () => {
    const result = evaluatePhase8SchemaGate([
      {
        path: "schemas/appserver/v2/TurnStartParams.json",
        kind: "json_schema",
        text: JSON.stringify({
          properties: {
            sandboxPolicy: {
              definitions: {
                SandboxPolicy: {
                  properties: {
                    writableRoots: { type: "array" },
                  },
                },
              },
            },
          },
        }),
      },
    ]);

    expect(result.status).toBe("BLOCKED");
    expect(result.unlockCandidates).toHaveLength(0);
  });

  it("marks readableRoots as an unlock candidate requiring review", () => {
    const result = evaluatePhase8SchemaGate([
      {
        path: "schemas/appserver/v2/TurnStartParams.json",
        kind: "json_schema",
        text: JSON.stringify({
          properties: {
            sandboxPolicy: {
              properties: {
                readableRoots: { type: "array", items: { type: "string" } },
              },
            },
          },
        }),
      },
    ]);

    expect(result.status).toBe("UNLOCK_CANDIDATE");
    expect(result.phase8Decision).toBe("REVIEW_REQUIRED");
    expect(result.readableRootSupported).toBe(true);
    expect(result.unlockCandidates[0]?.field).toBe("readableRoots");
  });
});
