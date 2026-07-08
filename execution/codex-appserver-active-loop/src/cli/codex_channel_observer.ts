import { mkdir, readFile, readdir, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  createConversationObserverModel,
  createObserverLiveSnapshot,
  renderObserverHtml,
  renderObserverTranscript,
  type ObserverFilters,
  type ObserverLiveInfo,
  type ObserverLogNavItem,
} from "../bridge/conversation_observer.js";
import { assertSafeJobId, safeJoin } from "../stores/safe_path.js";

interface CliArgs {
  readonly log?: string;
  readonly out?: string;
  readonly format: "html" | "text" | "both";
  readonly conversationId?: string;
  readonly role?: string;
  readonly state?: string;
  readonly watch: boolean;
  readonly once: boolean;
  readonly pollMs: number;
  readonly staleAfterMs: number;
  readonly hideRaw: boolean;
  readonly autoScroll: boolean;
}

interface RenderSummary {
  readonly result: "PASS";
  readonly task_id: "CEA-035" | "CEA-036";
  readonly observer_surface: "LOCAL_ONLY_COMMANDER_VIEW";
  readonly observer_mode: "STATIC_REPLAY" | "LOCAL_ONLY_READ_ONLY_LIVE_TAIL";
  readonly selected_job_id: string;
  readonly selected_log: string;
  readonly companion_report_found: boolean;
  readonly html_output: string | null;
  readonly live_snapshot_output: string | null;
  readonly format: CliArgs["format"];
  readonly cards: number;
  readonly all_cards: number;
  readonly filters: ObserverFilters;
  readonly watch: boolean;
  readonly live?: ObserverLiveInfo;
  readonly boundary: Record<string, string>;
}

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const messageLogRoot = path.join(projectRoot, "data", "message-logs");
  const observerRoot = path.join(projectRoot, "data", "observer");
  const reportRoot = path.join(projectRoot, "data", "reports");
  const args = parseArgs(process.argv.slice(2));

  if (args.watch) {
    await runWatch({ projectRoot, messageLogRoot, observerRoot, reportRoot, args });
    return;
  }

  const summary = await renderOnce({ projectRoot, messageLogRoot, observerRoot, reportRoot, args });
  console.log(JSON.stringify(summary, null, 2));
}

async function renderOnce(input: {
  readonly projectRoot: string;
  readonly messageLogRoot: string;
  readonly observerRoot: string;
  readonly reportRoot: string;
  readonly args: CliArgs;
  readonly previousSizeBytes?: number;
}): Promise<RenderSummary> {
  const logPath = input.args.log
    ? resolveLogPath(input.projectRoot, input.messageLogRoot, input.args.log)
    : await latestMessageLogPath(input.messageLogRoot);
  const source = await readSelectedSource(logPath);
  const selectedJobId = source.jobId;
  const companionReport = await findCompanionReport(input.reportRoot, selectedJobId);
  const logs = await discoverLogs(input.messageLogRoot, logPath);
  const filters: ObserverFilters = {
    conversationId: input.args.conversationId,
    role: input.args.role,
    state: input.args.state,
  };
  const htmlPath = input.args.out
    ? resolveObserverPath(input.observerRoot, input.args.out)
    : safeJoin(input.observerRoot, `${selectedJobId}${input.args.watch ? ".live" : ""}.html`);
  const snapshotPath = input.args.watch ? safeJoin(input.observerRoot, `${selectedJobId}.live.json`) : null;
  const now = new Date();
  const sourceReplaced =
    input.previousSizeBytes !== undefined &&
    source.sizeBytes !== undefined &&
    source.sizeBytes < input.previousSizeBytes;
  const live: ObserverLiveInfo | undefined = input.args.watch
    ? {
        status: source.exists
          ? sourceReplaced
            ? "STALE"
            : now.getTime() - source.mtimeMs > input.args.staleAfterMs
              ? "STALE"
              : "LIVE"
          : "ERROR",
        watchedPath: logPath,
        snapshotPath: snapshotPath ?? undefined,
        lastUpdatedAt: now.toISOString(),
        lastEventAt: findLatestTimestamp(source.selectedLog),
        pollMs: input.args.pollMs,
        staleAfterMs: input.args.staleAfterMs,
        sourceSizeBytes: source.sizeBytes,
        sourceMissing: !source.exists,
        sourceReplaced,
        note: source.parseErrorCount > 0 ? `${source.parseErrorCount} JSONL line(s) skipped while tailing` : undefined,
      }
    : undefined;
  const model = createConversationObserverModel({
    projectFolder: path.basename(input.projectRoot),
    selectedLogPath: logPath,
    logs,
    selectedLog: source.selectedLog,
    companionReport,
    filters,
    live,
    rawContentVisible: !input.args.hideRaw,
    autoScroll: input.args.autoScroll,
  });

  if (input.args.format === "html" || input.args.format === "both") {
    await mkdir(path.dirname(htmlPath), { recursive: true });
    await writeFile(htmlPath, renderObserverHtml(model), "utf8");
  }
  if (snapshotPath) {
    await mkdir(path.dirname(snapshotPath), { recursive: true });
    await writeFile(snapshotPath, `${JSON.stringify(createObserverLiveSnapshot(model), null, 2)}\n`, "utf8");
  }
  if (input.args.format === "text" || input.args.format === "both") {
    console.log(renderObserverTranscript(model));
  }
  return {
    result: "PASS",
    task_id: input.args.watch ? "CEA-036" : "CEA-035",
    observer_surface: "LOCAL_ONLY_COMMANDER_VIEW",
    observer_mode: input.args.watch ? "LOCAL_ONLY_READ_ONLY_LIVE_TAIL" : "STATIC_REPLAY",
    selected_job_id: selectedJobId,
    selected_log: logPath,
    companion_report_found: companionReport !== undefined,
    html_output: input.args.format === "html" || input.args.format === "both" ? htmlPath : null,
    live_snapshot_output: snapshotPath,
    format: input.args.format,
    cards: model.cards.length,
    all_cards: model.allCardsCount,
    filters,
    watch: input.args.watch,
    live,
    boundary: model.boundary,
  };
}

async function runWatch(input: {
  readonly projectRoot: string;
  readonly messageLogRoot: string;
  readonly observerRoot: string;
  readonly reportRoot: string;
  readonly args: CliArgs;
}): Promise<void> {
  let previousSizeBytes: number | undefined;
  let lastSummary: RenderSummary | undefined;
  let stopped = false;
  process.once("SIGINT", () => {
    stopped = true;
  });
  while (!stopped) {
    lastSummary = await renderOnce({
      ...input,
      previousSizeBytes,
    });
    previousSizeBytes = lastSummary.live?.sourceSizeBytes;
    if (input.args.once) break;
    await delay(input.args.pollMs);
  }
  if (!lastSummary) return;
  const summary: RenderSummary = stopped
    ? {
        ...lastSummary,
        live: lastSummary.live
          ? {
              ...lastSummary.live,
              status: "PAUSED",
              note: "watch stopped by SIGINT",
            }
          : undefined,
      }
    : lastSummary;
  console.log(JSON.stringify(summary, null, 2));
}

function parseArgs(argv: readonly string[]): CliArgs {
  const args: Record<string, string | boolean> = {};
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (!item.startsWith("--")) {
      throw new Error(`unexpected argument: ${item}`);
    }
    const key = item.slice(2);
    const next = argv[index + 1];
    if (next && !next.startsWith("--")) {
      args[key] = next;
      index += 1;
    } else {
      args[key] = true;
    }
  }
  const format = typeof args.format === "string" ? args.format : "html";
  if (format !== "html" && format !== "text" && format !== "both") {
    throw new Error("--format must be html, text, or both");
  }
  return {
    log: stringArg(args.log),
    out: stringArg(args.out),
    format,
    conversationId: stringArg(args.conversation) ?? stringArg(args.conversation_id),
    role: stringArg(args.role),
    state: stringArg(args.state),
    watch: args.watch === true,
    once: args.once === true,
    pollMs: positiveIntegerArg(args.poll_ms ?? args.pollMs, 1500, "--poll-ms"),
    staleAfterMs: positiveIntegerArg(args.stale_ms ?? args.staleMs, 15_000, "--stale-ms"),
    hideRaw: args.hide_raw === true || args.hideRaw === true,
    autoScroll: args.auto_scroll === true || args.autoScroll === true,
  };
}

function positiveIntegerArg(value: string | boolean | undefined, fallback: number, name: string): number {
  if (value === undefined || value === false) return fallback;
  if (value === true) throw new Error(`${name} requires a positive integer`);
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) throw new Error(`${name} requires a positive integer`);
  return parsed;
}

function stringArg(value: string | boolean | undefined): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

async function latestMessageLogPath(messageLogRoot: string): Promise<string> {
  const entries = await readdir(messageLogRoot);
  const candidates = await Promise.all(
    entries
      .filter(isObserverLogFilename)
      .map(async (entry) => {
        const filePath = safeJoin(messageLogRoot, entry);
        const fileStat = await stat(filePath);
        return { filePath, mtimeMs: fileStat.mtimeMs };
      }),
  );
  const latest = candidates.sort((left, right) => right.mtimeMs - left.mtimeMs)[0];
  if (!latest) throw new Error(`no message log JSON or JSONL files found under ${messageLogRoot}`);
  return latest.filePath;
}

async function discoverLogs(messageLogRoot: string, selectedLogPath: string): Promise<readonly ObserverLogNavItem[]> {
  const entries = await readdir(messageLogRoot);
  const candidates = await Promise.all(
    entries
      .filter(isObserverLogFilename)
      .map(async (entry) => {
        const filePath = safeJoin(messageLogRoot, entry);
        const fileStat = await stat(filePath);
        const jobId = jobIdFromFilename(entry);
        return {
          jobId,
          label: jobId.replace(/^cea-\d+-/, ""),
          filePath,
          selected: path.resolve(filePath) === path.resolve(selectedLogPath),
          mtimeMs: fileStat.mtimeMs,
        };
      }),
  );
  return candidates.sort((left, right) => right.mtimeMs - left.mtimeMs).map(({ mtimeMs: _mtimeMs, ...item }) => item);
}

async function findCompanionReport(reportRoot: string, jobId: string): Promise<unknown | undefined> {
  const entries = await readdir(reportRoot);
  for (const entry of entries.filter((candidate) => candidate.endsWith(".json"))) {
    const filePath = safeJoin(reportRoot, entry);
    try {
      const report = await readJson(filePath);
      if (isRecord(report) && report.job_id === jobId) return report;
    } catch {
      continue;
    }
  }
  return undefined;
}

async function readSelectedSource(filePath: string): Promise<{
  readonly exists: boolean;
  readonly selectedLog: unknown;
  readonly jobId: string;
  readonly sizeBytes?: number;
  readonly mtimeMs: number;
  readonly parseErrorCount: number;
}> {
  const jobId = jobIdFromFilename(path.basename(filePath));
  try {
    const fileStat = await stat(filePath);
    if (filePath.endsWith(".jsonl")) {
      const parsed = await readJsonlAsLog(filePath, jobId);
      return {
        exists: true,
        selectedLog: parsed.log,
        jobId,
        sizeBytes: fileStat.size,
        mtimeMs: fileStat.mtimeMs,
        parseErrorCount: parsed.parseErrorCount,
      };
    }
    return {
      exists: true,
      selectedLog: await readJson(filePath),
      jobId,
      sizeBytes: fileStat.size,
      mtimeMs: fileStat.mtimeMs,
      parseErrorCount: 0,
    };
  } catch (error) {
    if (isMissingFileError(error)) {
      return {
        exists: false,
        selectedLog: { job_id: jobId, message_events: [] },
        jobId,
        mtimeMs: 0,
        parseErrorCount: 0,
      };
    }
    throw error;
  }
}

async function readJsonlAsLog(filePath: string, jobId: string): Promise<{ readonly log: unknown; readonly parseErrorCount: number }> {
  const text = await readFile(filePath, "utf8");
  const messageEvents: unknown[] = [];
  let parseErrorCount = 0;
  for (const line of text.split(/\r?\n/)) {
    if (line.trim().length === 0) continue;
    try {
      messageEvents.push(JSON.parse(line) as unknown);
    } catch {
      parseErrorCount += 1;
    }
  }
  return { log: { job_id: jobId, message_events: messageEvents }, parseErrorCount };
}

async function readJson(filePath: string): Promise<unknown> {
  return JSON.parse(await readFile(filePath, "utf8")) as unknown;
}

function resolveLogPath(projectRoot: string, messageLogRoot: string, input: string): string {
  const candidates = [
    path.isAbsolute(input) ? path.resolve(input) : path.resolve(projectRoot, input),
    path.isAbsolute(input) ? path.resolve(input) : path.resolve(messageLogRoot, input),
  ];
  const resolvedRoot = path.resolve(messageLogRoot);
  for (const candidate of candidates) {
    const relative = path.relative(resolvedRoot, candidate);
    if (!relative.startsWith("..") && !path.isAbsolute(relative)) {
      return candidate;
    }
  }
  throw new Error(`path escapes message log root: ${input}`);
}

function resolveObserverPath(root: string, input: string): string {
  const candidate = path.isAbsolute(input) ? path.resolve(input) : path.resolve(root, input);
  const resolvedRoot = path.resolve(root);
  const relative = path.relative(resolvedRoot, candidate);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`path escapes observer root: ${input}`);
  }
  return candidate;
}

function isObserverLogFilename(entry: string): boolean {
  return entry.endsWith(".json") || entry.endsWith(".messages.jsonl");
}

function jobIdFromFilename(filename: string): string {
  const jobId = filename.replace(/\.messages\.jsonl$/i, "").replace(/\.jsonl$/i, "").replace(/\.json$/i, "");
  assertSafeJobId(jobId);
  return jobId;
}

function findLatestTimestamp(value: unknown): string | undefined {
  const timestamps: string[] = [];
  collectTimestamps(value, timestamps);
  return timestamps.sort((left, right) => Date.parse(right) - Date.parse(left))[0];
}

function collectTimestamps(value: unknown, timestamps: string[]): void {
  if (Array.isArray(value)) {
    for (const child of value) collectTimestamps(child, timestamps);
    return;
  }
  if (!isRecord(value)) return;
  if (typeof value.timestamp === "string") timestamps.push(value.timestamp);
  for (const child of Object.values(value)) collectTimestamps(child, timestamps);
}

function isMissingFileError(error: unknown): boolean {
  return typeof error === "object" && error !== null && "code" in error && (error as { readonly code?: unknown }).code === "ENOENT";
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

void main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
