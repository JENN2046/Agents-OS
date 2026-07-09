import { appendFile, mkdir, readFile } from "node:fs/promises";
import type { LoopEvent } from "../types/events.js";
import { assertSafeJobId, safeJoin } from "./safe_path.js";

export interface EventStore {
  append(jobId: string, event: LoopEvent): Promise<void>;
  read(jobId: string): Promise<LoopEvent[]>;
  pathFor(jobId: string): string;
}

export function createFileEventStore(rootDir: string): EventStore {
  return new FileEventStore(rootDir);
}

class FileEventStore implements EventStore {
  constructor(readonly rootDir: string) {}

  pathFor(jobId: string): string {
    assertSafeJobId(jobId);
    return safeJoin(this.rootDir, `${jobId}.events.jsonl`);
  }

  async append(jobId: string, event: LoopEvent): Promise<void> {
    assertSafeJobId(jobId);
    if (event.jobId !== jobId) {
      throw new Error("event job id mismatch");
    }
    await mkdir(this.rootDir, { recursive: true });
    await appendFile(this.pathFor(jobId), `${JSON.stringify(event)}\n`, "utf8");
  }

  async read(jobId: string): Promise<LoopEvent[]> {
    try {
      const content = await readFile(this.pathFor(jobId), "utf8");
      return content
        .split(/\r?\n/)
        .filter((line) => line.trim().length > 0)
        .map((line) => JSON.parse(line) as LoopEvent);
    } catch (error) {
      if (typeof error === "object" && error !== null && "code" in error && error.code === "ENOENT") {
        return [];
      }
      throw error;
    }
  }
}
