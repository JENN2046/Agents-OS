import { describe, expect, it } from "vitest";
import {
  createFailure,
  createIdGenerator,
  createNotification,
  createRequest,
  createSuccess,
  decodeJsonLine,
  encodeJsonLine,
  isFailure,
  isNotification,
  isRequest,
  isResponse,
} from "../../src/appserver/jsonrpc.js";

describe("jsonrpc", () => {
  it("builds request and notification messages", () => {
    expect(createRequest(1, "initialize")).toEqual({ id: 1, method: "initialize" });
    expect(createNotification("initialized")).toEqual({ method: "initialized" });
  });

  it("generates stable request ids", () => {
    const nextId = createIdGenerator("test");
    expect(nextId()).toBe("test-1");
    expect(nextId()).toBe("test-2");
  });

  it("encodes and decodes JSONL message shapes", () => {
    expect(decodeJsonLine(encodeJsonLine(createRequest(1, "initialize")))).toEqual({
      id: 1,
      method: "initialize",
    });
    expect(decodeJsonLine(encodeJsonLine(createNotification("initialized")))).toEqual({
      method: "initialized",
    });
    expect(decodeJsonLine(encodeJsonLine(createSuccess(1, { ok: true })))).toEqual({
      id: 1,
      result: { ok: true },
    });
    expect(decodeJsonLine(encodeJsonLine(createFailure(1, -32000, "nope")))).toEqual({
      id: 1,
      error: { code: -32000, message: "nope" },
    });
  });

  it("classifies inbound message kinds", () => {
    expect(isRequest(createRequest(1, "initialize"))).toBe(true);
    expect(isNotification(createNotification("initialized"))).toBe(true);
    const response = createFailure(1, -1, "bad");
    expect(isResponse(response)).toBe(true);
    expect(isFailure(response)).toBe(true);
  });
});
