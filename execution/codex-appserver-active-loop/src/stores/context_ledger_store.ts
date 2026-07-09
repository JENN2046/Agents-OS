import { appendFile, mkdir, readFile } from "node:fs/promises";
import { assertRecordOnlyContextLedgerEntry, type ContextLedgerEntry } from "../bridge/context_ledger.js";
import { assertSafeJobId, safeJoin } from "./safe_path.js";

export interface ContextLedgerStore {
  append(taskId: string, entry: ContextLedgerEntry): Promise<void>;
  read(taskId: string): Promise<ContextLedgerEntry[]>;
  pathFor(taskId: string): string;
}

export function createFileContextLedgerStore(rootDir: string): ContextLedgerStore {
  return new FileContextLedgerStore(rootDir);
}

class FileContextLedgerStore implements ContextLedgerStore {
  constructor(readonly rootDir: string) {}

  pathFor(taskId: string): string {
    assertSafeJobId(taskId);
    return safeJoin(this.rootDir, `${taskId}.context.jsonl`);
  }

  async append(taskId: string, entry: ContextLedgerEntry): Promise<void> {
    assertSafeJobId(taskId);
    assertRecordOnlyContextLedgerEntry(entry);
    if (entry.taskId !== taskId) {
      throw new Error("context ledger task id mismatch");
    }
    await mkdir(this.rootDir, { recursive: true });
    await appendFile(this.pathFor(taskId), `${JSON.stringify(entry)}\n`, "utf8");
  }

  async read(taskId: string): Promise<ContextLedgerEntry[]> {
    try {
      const content = await readFile(this.pathFor(taskId), "utf8");
      return content
        .split(/\r?\n/)
        .filter((line) => line.trim().length > 0)
        .map((line) => {
          const parsed = JSON.parse(line) as unknown;
          assertRecordOnlyContextLedgerEntry(parsed);
          return parsed;
        });
    } catch (error) {
      if (typeof error === "object" && error !== null && "code" in error && error.code === "ENOENT") {
        return [];
      }
      throw error;
    }
  }
}
