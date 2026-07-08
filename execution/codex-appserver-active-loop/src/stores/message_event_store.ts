import { appendFile, mkdir, readFile } from "node:fs/promises";
import { assertSafeJobId, safeJoin } from "./safe_path.js";
import type { MessageBusAuditEvent, MessageBusAuditEventName } from "../bridge/message_bus.js";

export interface MessageEventRecord extends MessageBusAuditEvent {
  readonly job_id: string;
  readonly event: MessageBusAuditEventName;
  readonly timestamp: string;
}

export interface MessageEventStore {
  append(jobId: string, event: MessageBusAuditEvent): Promise<void>;
  appendMany(jobId: string, events: readonly MessageBusAuditEvent[]): Promise<void>;
  read(jobId: string): Promise<readonly MessageEventRecord[]>;
  pathFor(jobId: string): string;
}

export function createFileMessageEventStore(rootDir: string): MessageEventStore {
  return new FileMessageEventStore(rootDir);
}

class FileMessageEventStore implements MessageEventStore {
  constructor(readonly rootDir: string) {}

  pathFor(jobId: string): string {
    assertSafeJobId(jobId);
    return safeJoin(this.rootDir, `${jobId}.messages.jsonl`);
  }

  async append(jobId: string, event: MessageBusAuditEvent): Promise<void> {
    assertSafeJobId(jobId);
    await mkdir(this.rootDir, { recursive: true });
    const target = this.pathFor(jobId);
    await appendFile(target, `${JSON.stringify(toRecord(jobId, event))}\n`, "utf8");
  }

  async appendMany(jobId: string, events: readonly MessageBusAuditEvent[]): Promise<void> {
    for (const event of events) {
      await this.append(jobId, event);
    }
  }

  async read(jobId: string): Promise<readonly MessageEventRecord[]> {
    const text = await readFile(this.pathFor(jobId), "utf8");
    return text
      .split(/\r?\n/)
      .filter((line) => line.trim().length > 0)
      .map((line) => JSON.parse(line) as MessageEventRecord);
  }
}

function toRecord(jobId: string, event: MessageBusAuditEvent): MessageEventRecord {
  return { job_id: jobId, ...event };
}
