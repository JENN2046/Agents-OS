import { EventEmitter } from "node:events";
import { describe, expect, it, vi } from "vitest";
import { createAppServerClient, forbiddenClientMethods } from "../../src/appserver/client.js";
import {
  createFailure,
  createNotification,
  createRequest,
  createSuccess,
  type JsonRpcInbound,
} from "../../src/appserver/jsonrpc.js";
import type { StdioTransport, StdioTransportEventMap, StdioTransportOptions } from "../../src/appserver/transport_stdio.js";

class FakeTransport implements StdioTransport {
  readonly options: Required<StdioTransportOptions> = {
    command: "fake",
    args: [],
    cwd: process.cwd(),
    timeoutMs: 25,
  };

  readonly sent: JsonRpcInbound[] = [];
  readonly events = new EventEmitter();
  started = false;

  async start(): Promise<void> {
    this.started = true;
  }

  send(message: JsonRpcInbound): void {
    this.sent.push(message);
  }

  async stop(): Promise<void> {
    this.started = false;
  }

  on<K extends keyof StdioTransportEventMap>(event: K, listener: StdioTransportEventMap[K]): () => void {
    this.events.on(event, listener);
    return () => this.events.off(event, listener);
  }

  emitMessage(message: JsonRpcInbound): void {
    this.events.emit("message", message);
  }
}

describe("AppServerClient", () => {
  it("correlates request responses by id", async () => {
    const transport = new FakeTransport();
    const client = createAppServerClient(transport, { requestTimeoutMs: 50 });
    await client.start();

    const pending = client.initialize();
    expect(transport.sent[0]).toMatchObject({ method: "initialize" });
    transport.emitMessage(createSuccess("appserver-1", { userAgent: "ua", codexHome: "redacted", platformFamily: "windows", platformOs: "windows" }));

    await expect(pending).resolves.toMatchObject({ userAgent: "ua" });
  });

  it("sends initialized as a notification", async () => {
    const transport = new FakeTransport();
    const client = createAppServerClient(transport, { requestTimeoutMs: 50 });
    await client.start();

    client.sendInitialized();

    expect(transport.sent).toEqual([createNotification("initialized")]);
  });

  it("dispatches server notifications and server requests", async () => {
    const transport = new FakeTransport();
    const client = createAppServerClient(transport, { requestTimeoutMs: 50 });
    const onNotification = vi.fn();
    const onServerRequest = vi.fn();
    client.onNotification(onNotification);
    client.onServerRequest(onServerRequest);
    await client.start();

    transport.emitMessage(createNotification("thread/started", { thread: { id: "t1" } }));
    transport.emitMessage(createRequest("server-1", "item/fileChange/requestApproval", { changes: [] }));

    expect(onNotification).toHaveBeenCalledWith({ method: "thread/started", params: { thread: { id: "t1" } } });
    expect(onServerRequest).toHaveBeenCalledWith({
      id: "server-1",
      method: "item/fileChange/requestApproval",
      params: { changes: [] },
    });
  });

  it("sends JSON-RPC responses to server-initiated requests", async () => {
    const transport = new FakeTransport();
    const client = createAppServerClient(transport, { requestTimeoutMs: 50 });
    await client.start();

    client.respondToServerRequest("server-1", { decision: "decline" });
    client.respondToServerRequestError("server-2", -32040, "declined by policy", { method: "x" });

    expect(transport.sent).toEqual([
      createSuccess("server-1", { decision: "decline" }),
      createFailure("server-2", -32040, "declined by policy", { method: "x" }),
    ]);
  });

  it("rejects timed out requests and cleans pending state", async () => {
    const transport = new FakeTransport();
    const client = createAppServerClient(transport, { requestTimeoutMs: 5 });
    await client.start();

    await expect(client.initialize()).rejects.toThrow("timed out");
  });

  it("requires a known active turn id before turn/steer", async () => {
    const transport = new FakeTransport();
    const client = createAppServerClient(transport, { requestTimeoutMs: 50 });
    await client.start();

    await expect(client.turnSteer({ threadId: "t1", expectedTurnId: "turn-1", input: [] })).rejects.toThrow(
      "known active turn id",
    );

    const turnStart = client.turnStart({ threadId: "t1", input: [] });
    transport.emitMessage(
      createSuccess("appserver-1", {
        turn: {
          id: "turn-1",
          items: [],
          itemsView: { type: "all" },
          status: "running",
          error: null,
          startedAt: null,
          completedAt: null,
          durationMs: null,
        },
      }),
    );
    await turnStart;

    const steer = client.turnSteer({ threadId: "t1", expectedTurnId: "turn-1", input: [] });
    expect(transport.sent.at(-1)).toMatchObject({ method: "turn/steer" });
    transport.emitMessage(createSuccess("appserver-2", { turnId: "turn-1" }));
    await expect(steer).resolves.toEqual({ turnId: "turn-1" });
  });

  it("does not expose forbidden App Server methods on the client surface", () => {
    const transport = new FakeTransport();
    const client = createAppServerClient(transport, { requestTimeoutMs: 50 });
    const keys = new Set(Object.keys(client));

    for (const forbidden of forbiddenClientMethods) {
      expect([...keys].some((key) => key.toLowerCase().includes(forbidden.replace(/[^a-z]/gi, "").toLowerCase()))).toBe(
        false,
      );
    }
  });
});
