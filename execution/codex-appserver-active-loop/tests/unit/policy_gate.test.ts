import { describe, expect, it } from "vitest";
import {
  containsDeniedPathTerm,
  createServerRequestResponsePlan,
  evaluateClientMethod,
  evaluateServerRequest,
  findDeniedPathTerms,
  isForbiddenAppServerMethod,
} from "../../src/bridge/policy_gate.js";

describe("policy gate", () => {
  it("detects denied path terms", () => {
    expect(containsDeniedPathTerm("project/.env")).toBe(true);
    expect(findDeniedPathTerms("C:/tmp/secrets/token.txt")).toEqual(["secrets"]);
    expect(containsDeniedPathTerm("data/synthetic-workspace/sample.txt")).toBe(false);
  });

  it("blocks forbidden client methods", () => {
    expect(isForbiddenAppServerMethod("thread/shellCommand")).toBe(true);
    expect(isForbiddenAppServerMethod("process/read")).toBe(true);
    expect(evaluateClientMethod("turn/start")).toMatchObject({ kind: "allow" });
    expect(evaluateClientMethod("command/exec")).toMatchObject({ kind: "block" });
  });

  it("declines file change approvals in MVP", () => {
    expect(
      evaluateServerRequest({
        method: "item/fileChange/requestApproval",
        params: { path: "data/synthetic-workspace/sample.txt" },
      }),
    ).toMatchObject({ kind: "decline", reason: "file changes are declined in MVP" });
  });

  it("declines denied path references before method-specific handling", () => {
    expect(
      evaluateServerRequest({
        method: "item/tool/requestUserInput",
        params: { path: "state-private/raw.log" },
      }),
    ).toMatchObject({ kind: "decline", matchedDeniedTerms: ["state-private"] });
  });

  it("routes human input requests to human gate", () => {
    expect(
      evaluateServerRequest({
        method: "mcpServer/elicitation/request",
        params: { prompt: "confirm?" },
      }),
    ).toMatchObject({ kind: "human_gate_required" });
  });

  it("blocks private token refresh and unknown server requests", () => {
    expect(evaluateServerRequest({ method: "account/chatgptAuthTokens/refresh", params: {} })).toMatchObject({
      kind: "block",
    });
    expect(evaluateServerRequest({ method: "unknown/request", params: {} })).toMatchObject({ kind: "block" });
  });

  it("maps approval server requests to protocol-level decline responses", () => {
    expect(createServerRequestResponsePlan({ method: "item/fileChange/requestApproval", params: {} }).response).toEqual({
      kind: "result",
      result: { decision: "decline" },
    });
    expect(
      createServerRequestResponsePlan({ method: "item/commandExecution/requestApproval", params: {} }).response,
    ).toEqual({
      kind: "result",
      result: { decision: "decline" },
    });
    expect(createServerRequestResponsePlan({ method: "applyPatchApproval", params: {} }).response).toEqual({
      kind: "result",
      result: { decision: "denied" },
    });
    expect(createServerRequestResponsePlan({ method: "execCommandApproval", params: {} }).response).toEqual({
      kind: "result",
      result: { decision: "denied" },
    });
  });

  it("maps unsupported or human-gated server requests to fail-closed responses", () => {
    expect(createServerRequestResponsePlan({ method: "mcpServer/elicitation/request", params: {} }).response).toEqual({
      kind: "result",
      result: { action: "decline", content: null, _meta: null },
    });
    expect(createServerRequestResponsePlan({ method: "item/tool/requestUserInput", params: {} }).response).toMatchObject({
      kind: "error",
      code: -32040,
    });
    expect(createServerRequestResponsePlan({ method: "item/permissions/requestApproval", params: {} }).response).toMatchObject({
      kind: "error",
      code: -32040,
    });
    expect(createServerRequestResponsePlan({ method: "item/tool/call", params: {} }).response).toMatchObject({
      kind: "error",
      code: -32041,
    });
    expect(createServerRequestResponsePlan({ method: "attestation/generate", params: {} }).response).toMatchObject({
      kind: "error",
      code: -32041,
    });
    expect(createServerRequestResponsePlan({ method: "unknown/request", params: {} }).response).toMatchObject({
      kind: "error",
      code: -32041,
    });
  });
});
