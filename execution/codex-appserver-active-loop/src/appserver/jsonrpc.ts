export type JsonRpcId = string | number;

export interface JsonRpcRequest<TParams = unknown> {
  readonly id: JsonRpcId;
  readonly method: string;
  readonly params?: TParams;
}

export interface JsonRpcNotification<TParams = unknown> {
  readonly method: string;
  readonly params?: TParams;
}

export interface JsonRpcSuccess<TResult = unknown> {
  readonly id: JsonRpcId;
  readonly result: TResult;
}

export interface JsonRpcFailure {
  readonly id: JsonRpcId | null;
  readonly error: {
    readonly code: number;
    readonly message: string;
    readonly data?: unknown;
  };
}

export type JsonRpcResponse<TResult = unknown> = JsonRpcSuccess<TResult> | JsonRpcFailure;
export type JsonRpcInbound = JsonRpcRequest | JsonRpcNotification | JsonRpcResponse;

export class JsonRpcProtocolError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "JsonRpcProtocolError";
  }
}

export class JsonRpcRemoteError extends Error {
  readonly code: number;
  readonly data?: unknown;

  constructor(error: JsonRpcFailure["error"]) {
    super(error.message);
    this.name = "JsonRpcRemoteError";
    this.code = error.code;
    this.data = error.data;
  }
}

export function createIdGenerator(prefix = "rpc") {
  let nextId = 0;
  return () => `${prefix}-${++nextId}`;
}

export function createRequest<TParams>(
  id: JsonRpcId,
  method: string,
  params?: TParams,
): JsonRpcRequest<TParams> {
  assertMethod(method);
  return params === undefined ? { id, method } : { id, method, params };
}

export function createNotification<TParams>(
  method: string,
  params?: TParams,
): JsonRpcNotification<TParams> {
  assertMethod(method);
  return params === undefined ? { method } : { method, params };
}

export function createSuccess<TResult>(id: JsonRpcId, result: TResult): JsonRpcSuccess<TResult> {
  return { id, result };
}

export function createFailure(
  id: JsonRpcId | null,
  code: number,
  message: string,
  data?: unknown,
): JsonRpcFailure {
  return data === undefined
    ? { id, error: { code, message } }
    : { id, error: { code, message, data } };
}

export function encodeJsonLine(message: JsonRpcInbound): string {
  return `${JSON.stringify(message)}\n`;
}

export function decodeJsonLine(line: string): JsonRpcInbound {
  const trimmed = line.trim();
  if (!trimmed) {
    throw new JsonRpcProtocolError("empty JSON-RPC line");
  }

  let value: unknown;
  try {
    value = JSON.parse(trimmed);
  } catch (error) {
    throw new JsonRpcProtocolError(
      `invalid JSON-RPC JSON: ${error instanceof Error ? error.message : "unknown parse error"}`,
    );
  }

  if (!isRecord(value)) {
    throw new JsonRpcProtocolError("JSON-RPC message must be an object");
  }

  const hasId = Object.hasOwn(value, "id");
  const method = typeof value.method === "string" ? value.method : undefined;
  const hasMethod = method !== undefined;
  const hasResult = Object.hasOwn(value, "result");
  const hasError = Object.hasOwn(value, "error");

  if (hasMethod && hasId && isJsonRpcId(value.id)) {
    return "params" in value
      ? createRequest(value.id, method, value.params)
      : createRequest(value.id, method);
  }

  if (hasMethod && !hasId) {
    return "params" in value ? createNotification(method, value.params) : createNotification(method);
  }

  if (hasId && hasResult && isJsonRpcId(value.id)) {
    return createSuccess(value.id, value.result);
  }

  if (hasError && (isJsonRpcId(value.id) || value.id === null) && isJsonRpcError(value.error)) {
    return createFailure(value.id, value.error.code, value.error.message, value.error.data);
  }

  throw new JsonRpcProtocolError("unrecognized JSON-RPC message shape");
}

export function isRequest(message: JsonRpcInbound): message is JsonRpcRequest {
  return "method" in message && "id" in message;
}

export function isNotification(message: JsonRpcInbound): message is JsonRpcNotification {
  return "method" in message && !("id" in message);
}

export function isResponse<TResult = unknown>(message: JsonRpcInbound): message is JsonRpcResponse<TResult> {
  return "id" in message && ("result" in message || "error" in message) && !("method" in message);
}

export function isFailure(message: JsonRpcResponse): message is JsonRpcFailure {
  return "error" in message;
}

function assertMethod(method: string): void {
  if (!method.trim()) {
    throw new JsonRpcProtocolError("JSON-RPC method must be non-empty");
  }
}

function isJsonRpcId(value: unknown): value is JsonRpcId {
  return typeof value === "string" || typeof value === "number";
}

function isJsonRpcError(value: unknown): value is JsonRpcFailure["error"] {
  return isRecord(value) && typeof value.code === "number" && typeof value.message === "string";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
