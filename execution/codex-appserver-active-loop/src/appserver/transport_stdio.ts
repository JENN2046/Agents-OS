import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { EventEmitter } from "node:events";
import { decodeJsonLine, encodeJsonLine, type JsonRpcInbound } from "./jsonrpc.js";

export interface StdioTransportOptions {
  readonly command?: string;
  readonly args?: readonly string[];
  readonly cwd: string;
  readonly timeoutMs: number;
}

export type StdioTransportEventMap = {
  message: (message: JsonRpcInbound) => void;
  stderr: (chunk: string) => void;
  protocolError: (error: Error) => void;
  exit: (code: number | null, signal: NodeJS.Signals | null) => void;
};

export interface StdioTransport {
  readonly options: Required<StdioTransportOptions>;
  readonly started: boolean;
  start(): Promise<void>;
  send(message: JsonRpcInbound): void;
  stop(): Promise<void>;
  on<K extends keyof StdioTransportEventMap>(event: K, listener: StdioTransportEventMap[K]): () => void;
}

type Listener = (...args: unknown[]) => void;

export function createStdioTransport(options: StdioTransportOptions): StdioTransport {
  const defaults = defaultAppServerCommand();
  return new NodeStdioTransport({
    command: options.command ?? defaults.command,
    args: options.args ?? defaults.args,
    cwd: options.cwd,
    timeoutMs: options.timeoutMs,
  });
}

export function defaultAppServerCommand(platform: NodeJS.Platform = process.platform): Pick<Required<StdioTransportOptions>, "command" | "args"> {
  if (platform === "win32") {
    return { command: "cmd.exe", args: ["/d", "/s", "/c", "codex app-server --stdio"] };
  }
  return { command: "codex", args: ["app-server", "--stdio"] };
}

class NodeStdioTransport implements StdioTransport {
  readonly options: Required<StdioTransportOptions>;
  #child: ChildProcessWithoutNullStreams | undefined;
  #events = new EventEmitter();
  #stdoutBuffer = "";
  #started = false;

  constructor(options: Required<StdioTransportOptions>) {
    this.options = options;
  }

  get started(): boolean {
    return this.#started;
  }

  start(): Promise<void> {
    if (this.#started) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      const child = spawn(this.options.command, [...this.options.args], {
        cwd: this.options.cwd,
        stdio: ["pipe", "pipe", "pipe"],
        windowsHide: true,
      });

      const timer = setTimeout(() => {
        cleanup();
        child.kill();
        reject(new Error("stdio transport start timed out"));
      }, this.options.timeoutMs);

      const cleanup = () => {
        clearTimeout(timer);
        child.off("error", onError);
        child.off("spawn", onSpawn);
      };
      const onError = (error: Error) => {
        cleanup();
        reject(error);
      };
      const onSpawn = () => {
        cleanup();
        this.#child = child;
        this.#started = true;
        resolve();
      };

      child.stdout.setEncoding("utf8");
      child.stderr.setEncoding("utf8");
      child.stdout.on("data", (chunk: string) => this.#handleStdout(chunk));
      child.stderr.on("data", (chunk: string) => this.#events.emit("stderr", sanitizeStderr(chunk)));
      child.stdin.on("error", (error) => this.#events.emit("protocolError", error));
      child.on("exit", (code, signal) => {
        this.#started = false;
        this.#child = undefined;
        this.#events.emit("exit", code, signal);
      });
      child.on("error", onError);
      child.on("spawn", onSpawn);
    });
  }

  send(message: JsonRpcInbound): void {
    if (!this.#child || !this.#started || this.#child.stdin.destroyed || this.#child.stdin.writableEnded) {
      throw new Error("stdio transport is not running");
    }
    this.#child.stdin.write(encodeJsonLine(message));
  }

  async stop(): Promise<void> {
    const child = this.#child;
    if (!child) {
      this.#started = false;
      return;
    }

    await new Promise<void>((resolve) => {
      const timer = setTimeout(() => {
        child.kill();
        resolve();
      }, this.options.timeoutMs);
      child.once("exit", () => {
        clearTimeout(timer);
        resolve();
      });
      try {
        child.stdin.end();
      } catch {
        child.kill();
      }
    });
    this.#started = false;
    this.#child = undefined;
  }

  on<K extends keyof StdioTransportEventMap>(event: K, listener: StdioTransportEventMap[K]): () => void {
    this.#events.on(event, listener as Listener);
    return () => this.#events.off(event, listener as Listener);
  }

  #handleStdout(chunk: string): void {
    this.#stdoutBuffer += chunk;
    const lines = this.#stdoutBuffer.split(/\r?\n/);
    this.#stdoutBuffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.trim()) {
        continue;
      }
      try {
        this.#events.emit("message", decodeJsonLine(line));
      } catch (error) {
        this.#events.emit("protocolError", error instanceof Error ? error : new Error("unknown protocol error"));
      }
    }
  }
}

export function sanitizeStderr(text: string): string {
  return text
    .replace(/[A-Za-z]:\\Users\\[^\\\r\n]+\\\.codex/g, "<REDACTED_CODEX_HOME>")
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer <REDACTED>")
    .replace(/sk-[A-Za-z0-9._-]+/g, "sk-<REDACTED>");
}
