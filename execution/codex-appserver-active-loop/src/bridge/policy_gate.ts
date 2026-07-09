import type { ServerRequest } from "../generated/appserver/ServerRequest";

export const deniedPathTerms = [
  ".env",
  "secrets",
  "credentials",
  "tokens",
  "cookies",
  ".ssh",
  "state-private",
] as const;

export const forbiddenAppServerMethods = [
  "thread/shellCommand",
  "command/exec",
  "command/exec/write",
  "process/*",
] as const;

export type PolicyDecisionKind = "allow" | "decline" | "block" | "human_gate_required";

export interface PolicyDecision {
  readonly kind: PolicyDecisionKind;
  readonly reason: string;
  readonly matchedDeniedTerms: readonly string[];
  readonly method?: string;
}

export interface ServerRequestResponsePlan {
  readonly policyDecision: PolicyDecision;
  readonly response:
    | {
        readonly kind: "result";
        readonly result: unknown;
      }
    | {
        readonly kind: "error";
        readonly code: number;
        readonly message: string;
        readonly data?: unknown;
      };
}

export const policyDeclineErrorCode = -32040;
export const unsupportedServerRequestErrorCode = -32041;

export function containsDeniedPathTerm(pathText: string): boolean {
  return findDeniedPathTerms(pathText).length > 0;
}

export function findDeniedPathTerms(pathText: string): readonly string[] {
  const normalized = pathText.toLowerCase();
  return deniedPathTerms.filter((term) => normalized.includes(term.toLowerCase()));
}

export function isForbiddenAppServerMethod(method: string): boolean {
  return forbiddenAppServerMethods.some((forbidden) =>
    forbidden.endsWith("/*") ? method.startsWith(forbidden.slice(0, -1)) : method === forbidden,
  );
}

export function evaluateClientMethod(method: string): PolicyDecision {
  if (isForbiddenAppServerMethod(method)) {
    return {
      kind: "block",
      method,
      reason: `forbidden App Server method: ${method}`,
      matchedDeniedTerms: [],
    };
  }

  return {
    kind: "allow",
    method,
    reason: "method is not forbidden",
    matchedDeniedTerms: [],
  };
}

export interface ServerRequestLike {
  readonly method: ServerRequest["method"] | string;
  readonly params: unknown;
}

export function evaluateServerRequest(request: ServerRequestLike): PolicyDecision {
  const serializedParams = safeSerialize(request.params);
  const matchedDeniedTerms = findDeniedPathTerms(serializedParams);
  if (matchedDeniedTerms.length > 0) {
    return {
      kind: "decline",
      method: request.method,
      reason: "request references denied path term",
      matchedDeniedTerms,
    };
  }

  switch (request.method) {
    case "item/fileChange/requestApproval":
    case "applyPatchApproval":
      return {
        kind: "decline",
        method: request.method,
        reason: "file changes are declined in MVP",
        matchedDeniedTerms,
      };
    case "item/commandExecution/requestApproval":
    case "execCommandApproval":
    case "item/permissions/requestApproval":
      return {
        kind: "decline",
        method: request.method,
        reason: "write or execution approval requests are declined in MVP",
        matchedDeniedTerms,
      };
    case "item/tool/requestUserInput":
    case "mcpServer/elicitation/request":
      return {
        kind: "human_gate_required",
        method: request.method,
        reason: "request requires human input",
        matchedDeniedTerms,
      };
    case "account/chatgptAuthTokens/refresh":
      return {
        kind: "block",
        method: request.method,
        reason: "private auth token refresh is outside MVP boundary",
        matchedDeniedTerms,
      };
    case "attestation/generate":
    case "item/tool/call":
      return {
        kind: "block",
        method: request.method,
        reason: "server request shape is unsupported by MVP policy gate",
        matchedDeniedTerms,
      };
    default:
      return {
        kind: "block",
        method: request.method,
        reason: "unknown server request method",
        matchedDeniedTerms,
      };
  }
}

export function createServerRequestResponsePlan(request: ServerRequestLike): ServerRequestResponsePlan {
  const policyDecision = evaluateServerRequest(request);

  switch (request.method) {
    case "item/fileChange/requestApproval":
      return {
        policyDecision,
        response: {
          kind: "result",
          result: { decision: "decline" },
        },
      };
    case "item/commandExecution/requestApproval":
      return {
        policyDecision,
        response: {
          kind: "result",
          result: { decision: "decline" },
        },
      };
    case "applyPatchApproval":
    case "execCommandApproval":
      return {
        policyDecision,
        response: {
          kind: "result",
          result: { decision: "denied" },
        },
      };
    case "mcpServer/elicitation/request":
      return {
        policyDecision,
        response: {
          kind: "result",
          result: { action: "decline", content: null, _meta: null },
        },
      };
    case "item/tool/requestUserInput":
    case "item/permissions/requestApproval":
      return {
        policyDecision,
        response: {
          kind: "error",
          code: policyDeclineErrorCode,
          message: `${request.method} requires a human gate and is declined by MVP policy`,
          data: { policyDecision },
        },
      };
    case "account/chatgptAuthTokens/refresh":
      return {
        policyDecision,
        response: {
          kind: "error",
          code: policyDeclineErrorCode,
          message: "private auth token refresh is outside MVP boundary",
          data: { policyDecision },
        },
      };
    case "attestation/generate":
    case "item/tool/call":
      return {
        policyDecision,
        response: {
          kind: "error",
          code: unsupportedServerRequestErrorCode,
          message: `${request.method} is unsupported by MVP policy gate`,
          data: { policyDecision },
        },
      };
    default:
      return {
        policyDecision,
        response: {
          kind: "error",
          code: unsupportedServerRequestErrorCode,
          message: `unknown server request method: ${request.method}`,
          data: { policyDecision },
        },
      };
  }
}

function safeSerialize(value: unknown): string {
  try {
    return JSON.stringify(value) ?? "";
  } catch {
    return "";
  }
}
