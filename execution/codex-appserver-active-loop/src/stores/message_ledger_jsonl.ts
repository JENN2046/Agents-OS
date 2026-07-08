import { appendFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import type { MessageLedgerEntry, MessageLedgerSnapshot, MessageLedgerStore } from "./message_ledger.js";
import { createDeliveryFingerprint, createMessageLedgerSnapshot } from "./message_ledger.js";
import { assertSafeJobId, safeJoin } from "./safe_path.js";

export interface JsonlMessageLedgerStore extends MessageLedgerStore {
  pathFor(): string;
  readPersistedSnapshot(): MessageLedgerSnapshot;
}

export function createJsonlMessageLedgerStore(rootDir: string, ledgerId: string): JsonlMessageLedgerStore {
  return new FileJsonlMessageLedgerStore(rootDir, ledgerId);
}

class FileJsonlMessageLedgerStore implements JsonlMessageLedgerStore {
  readonly #entries: MessageLedgerEntry[];

  constructor(
    readonly rootDir: string,
    readonly ledgerId: string,
  ) {
    assertSafeJobId(ledgerId);
    this.#entries = readEntriesIfPresent(this.pathFor());
  }

  pathFor(): string {
    assertSafeJobId(this.ledgerId);
    return safeJoin(this.rootDir, `${this.ledgerId}.ledger.jsonl`);
  }

  record(entry: Omit<MessageLedgerEntry, "entry_id"> & { readonly entry_id?: string }): MessageLedgerEntry {
    const recorded = sanitizeLedgerEntry({
      ...entry,
      entry_id: entry.entry_id ?? createDeliveryFingerprint(["jsonl-ledger-entry", this.#entries.length + 1, entry]),
    });
    try {
      mkdirSync(this.rootDir, { recursive: true });
      appendFileSync(this.pathFor(), `${JSON.stringify(recorded)}\n`, "utf8");
    } catch (error) {
      throw new Error(`failed to append message ledger entry: ${error instanceof Error ? error.message : String(error)}`);
    }
    this.#entries.push(recorded);
    return recorded;
  }

  snapshot(): MessageLedgerSnapshot {
    return createMessageLedgerSnapshot(this.#entries);
  }

  readPersistedSnapshot(): MessageLedgerSnapshot {
    return createMessageLedgerSnapshot(readEntriesIfPresent(this.pathFor()));
  }
}

function readEntriesIfPresent(filePath: string): MessageLedgerEntry[] {
  if (!existsSync(filePath)) return [];
  const text = readFileSync(filePath, "utf8");
  return text
    .split(/\r?\n/)
    .filter((line) => line.trim().length > 0)
    .map((line) => sanitizeLedgerEntry(JSON.parse(line) as MessageLedgerEntry));
}

function sanitizeLedgerEntry(entry: MessageLedgerEntry): MessageLedgerEntry {
  return {
    entry_id: entry.entry_id,
    kind: entry.kind,
    at: entry.at,
    message_id: entry.message_id,
    reply_to: entry.reply_to,
    conversation_id: entry.conversation_id,
    correlation_id: entry.correlation_id,
    from: entry.from,
    to: entry.to,
    fromThreadId: entry.fromThreadId,
    toThreadId: entry.toThreadId,
    message_kind: entry.message_kind,
    state: entry.state,
    round: entry.round,
    round_count: entry.round_count,
    max_rounds: entry.max_rounds,
    payload_hash: entry.payload_hash,
    delivery_fingerprint: entry.delivery_fingerprint,
    message_ids: entry.message_ids,
    reply_ids: entry.reply_ids,
    failure_reason: entry.failure_reason,
  };
}
