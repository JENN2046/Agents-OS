import type { InitializeResponse } from "../generated/appserver/InitializeResponse";
import type { ServerNotification } from "../generated/appserver/ServerNotification";
import type { ServerRequest } from "../generated/appserver/ServerRequest";
import type { ReviewStartParams } from "../generated/appserver/v2/ReviewStartParams";
import type { ReviewStartResponse } from "../generated/appserver/v2/ReviewStartResponse";
import type { ThreadStartParams } from "../generated/appserver/v2/ThreadStartParams";
import type { ThreadStartResponse } from "../generated/appserver/v2/ThreadStartResponse";
import type { TurnInterruptParams } from "../generated/appserver/v2/TurnInterruptParams";
import type { TurnInterruptResponse } from "../generated/appserver/v2/TurnInterruptResponse";
import type { TurnStartParams } from "../generated/appserver/v2/TurnStartParams";
import type { TurnStartResponse } from "../generated/appserver/v2/TurnStartResponse";
import type { TurnSteerParams } from "../generated/appserver/v2/TurnSteerParams";
import type { TurnSteerResponse } from "../generated/appserver/v2/TurnSteerResponse";
import {
  createIdGenerator,
  createFailure,
  createNotification,
  createRequest,
  createSuccess,
  isFailure,
  isNotification,
  isRequest,
  isResponse,
  JsonRpcRemoteError,
  type JsonRpcId,
  type JsonRpcInbound,
} from "./jsonrpc.js";
import type { StdioTransport } from "./transport_stdio.js";

export type ServerRequestHandler = (request: ServerRequest) => void | Promise<void>;
export type ServerNotificationHandler = (notification: ServerNotification) => void;

export interface AppServerClientOptions {
  readonly requestTimeoutMs: number;
  readonly clientInfo?: {
    readonly name: string;
    readonly title: string | null;
    readonly version: string;
  };
}

export interface AppServerClient {
  readonly forbiddenMethods: readonly string[];
  start(): Promise<void>;
  stop(): Promise<void>;
  initialize(): Promise<InitializeResponse>;
  sendInitialized(): void;
  threadStart(params: ThreadStartParams): Promise<ThreadStartResponse>;
  turnStart(params: TurnStartParams): Promise<TurnStartResponse>;
  turnSteer(params: TurnSteerParams): Promise<TurnSteerResponse>;
  turnInterrupt(params: TurnInterruptParams): Promise<TurnInterruptResponse>;
  reviewStart(params: ReviewStartParams): Promise<ReviewStartResponse>;
  respondToServerRequest(id: JsonRpcId, result: unknown): void;
  respondToServerRequestError(id: JsonRpcId, code: number, message: string, data?: unknown): void;
  onServerRequest(handler: ServerRequestHandler): () => void;
  onNotification(handler: ServerNotificationHandler): () => void;
}

type PendingRequest = {
  readonly resolve: (value: unknown) => void;
  readonly reject: (error: Error) => void;
  readonly timer: NodeJS.Timeout;
};

export const forbiddenClientMethods = [
  "thread/shellCommand",
  "command/exec",
  "command/exec/write",
  "process/*",
] as const;

export function createAppServerClient(
  transport: StdioTransport,
  options: AppServerClientOptions,
): AppServerClient {
  return new JsonRpcAppServerClient(transport, options);
}

class JsonRpcAppServerClient implements AppServerClient {
  readonly forbiddenMethods = forbiddenClientMethods;
  readonly #transport: StdioTransport;
  readonly #options: AppServerClientOptions;
  readonly #nextId = createIdGenerator("appserver");
  readonly #pending = new Map<JsonRpcId, PendingRequest>();
  readonly #requestHandlers = new Set<ServerRequestHandler>();
  readonly #notificationHandlers = new Set<ServerNotificationHandler>();
  readonly #activeTurnByThread = new Map<string, string>();
  readonly #completedTurnIds = new Set<string>();
  #unsubscribers: Array<() => void> = [];

  constructor(transport: StdioTransport, options: AppServerClientOptions) {
    this.#transport = transport;
    this.#options = options;
  }

  async start(): Promise<void> {
    this.#unsubscribers.push(
      this.#transport.on("message", (message) => this.#handleMessage(message)),
      this.#transport.on("exit", () => this.#rejectAllPending(new Error("app-server transport exited"))),
      this.#transport.on("protocolError", (error) => this.#rejectAllPending(error)),
    );
    await this.#transport.start();
  }

  async stop(): Promise<void> {
    this.#rejectAllPending(new Error("app-server client stopped"));
    for (const unsubscribe of this.#unsubscribers.splice(0)) {
      unsubscribe();
    }
    await this.#transport.stop();
  }

  initialize(): Promise<InitializeResponse> {
    return this.#request("initialize", {
      clientInfo: this.#options.clientInfo ?? {
        name: "codex-appserver-active-loop",
        title: "Codex App Server Active Loop",
        version: "0.0.0",
      },
      capabilities: {
        experimentalApi: false,
        requestAttestation: false,
        optOutNotificationMethods: [],
      },
    });
  }

  sendInitialized(): void {
    this.#transport.send(createNotification("initialized"));
  }

  threadStart(params: ThreadStartParams): Promise<ThreadStartResponse> {
    return this.#request("thread/start", params);
  }

  async turnStart(params: TurnStartParams): Promise<TurnStartResponse> {
    const response = await this.#request<TurnStartResponse>("turn/start", params);
    if (response.turn.status === "inProgress" && !this.#completedTurnIds.has(response.turn.id)) {
      this.#activeTurnByThread.set(params.threadId, response.turn.id);
    } else {
      this.#activeTurnByThread.delete(params.threadId);
    }
    return response;
  }

  turnSteer(params: TurnSteerParams): Promise<TurnSteerResponse> {
    const activeTurnId = this.#activeTurnByThread.get(params.threadId);
    if (!activeTurnId || activeTurnId !== params.expectedTurnId) {
      return Promise.reject(new Error("turn/steer requires a known active turn id match"));
    }
    return this.#request("turn/steer", params);
  }

  async turnInterrupt(params: TurnInterruptParams): Promise<TurnInterruptResponse> {
    const response = await this.#request<TurnInterruptResponse>("turn/interrupt", params);
    this.#activeTurnByThread.delete(params.threadId);
    return response;
  }

  reviewStart(params: ReviewStartParams): Promise<ReviewStartResponse> {
    return this.#request("review/start", params);
  }

  respondToServerRequest(id: JsonRpcId, result: unknown): void {
    this.#transport.send(createSuccess(id, result));
  }

  respondToServerRequestError(id: JsonRpcId, code: number, message: string, data?: unknown): void {
    this.#transport.send(createFailure(id, code, message, data));
  }

  onServerRequest(handler: ServerRequestHandler): () => void {
    this.#requestHandlers.add(handler);
    return () => this.#requestHandlers.delete(handler);
  }

  onNotification(handler: ServerNotificationHandler): () => void {
    this.#notificationHandlers.add(handler);
    return () => this.#notificationHandlers.delete(handler);
  }

  #request<TResult>(method: string, params: unknown): Promise<TResult> {
    if (this.#isForbidden(method)) {
      return Promise.reject(new Error(`forbidden App Server method is not exposed: ${method}`));
    }

    const id = this.#nextId();
    const request = createRequest(id, method, params);
    const promise = new Promise<TResult>((resolve, reject) => {
      const timer = setTimeout(() => {
        this.#pending.delete(id);
        reject(new Error(`App Server request timed out: ${method}`));
      }, this.#options.requestTimeoutMs);
      this.#pending.set(id, { resolve: resolve as (value: unknown) => void, reject, timer });
    });
    this.#transport.send(request);
    return promise;
  }

  #handleMessage(message: JsonRpcInbound): void {
    if (isResponse(message)) {
      if (message.id === null) {
        return;
      }
      const pending = this.#pending.get(message.id);
      if (!pending) {
        return;
      }
      clearTimeout(pending.timer);
      this.#pending.delete(message.id);
      if (isFailure(message)) {
        pending.reject(new JsonRpcRemoteError(message.error));
        return;
      }
      pending.resolve(message.result);
      return;
    }

    if (isRequest(message)) {
      for (const handler of this.#requestHandlers) {
        void handler(message as ServerRequest);
      }
      return;
    }

    if (isNotification(message)) {
      this.#trackNotification(message as ServerNotification);
      for (const handler of this.#notificationHandlers) {
        handler(message as ServerNotification);
      }
    }
  }

  #trackNotification(notification: ServerNotification): void {
    if (notification.method !== "turn/completed") {
      return;
    }
    this.#completedTurnIds.add(notification.params.turn.id);
    const activeTurnId = this.#activeTurnByThread.get(notification.params.threadId);
    if (activeTurnId === notification.params.turn.id) {
      this.#activeTurnByThread.delete(notification.params.threadId);
    }
  }

  #rejectAllPending(error: Error): void {
    for (const [id, pending] of this.#pending) {
      clearTimeout(pending.timer);
      pending.reject(error);
      this.#pending.delete(id);
    }
  }

  #isForbidden(method: string): boolean {
    return this.forbiddenMethods.some((forbidden) =>
      forbidden.endsWith("/*") ? method.startsWith(forbidden.slice(0, -1)) : method === forbidden,
    );
  }
}
