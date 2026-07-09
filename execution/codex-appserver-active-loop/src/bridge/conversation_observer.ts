export type ObserverState =
  | "CAPTURED"
  | "ROUTED"
  | "REPLIED"
  | "OBSERVED"
  | "REJECTED"
  | "EXPIRED"
  | "FAILED"
  | "BLOCKED"
  | "DONE"
  | "UNKNOWN";

export interface ObserverFilters {
  readonly conversationId?: string;
  readonly role?: string;
  readonly state?: string;
}

export type ObserverLiveStatus = "LIVE" | "PAUSED" | "STALE" | "ERROR";

export interface ObserverLiveInfo {
  readonly status: ObserverLiveStatus;
  readonly watchedPath: string;
  readonly snapshotPath?: string;
  readonly lastUpdatedAt: string;
  readonly lastEventAt?: string;
  readonly pollMs: number;
  readonly staleAfterMs: number;
  readonly sourceSizeBytes?: number;
  readonly sourceMissing?: boolean;
  readonly sourceReplaced?: boolean;
  readonly note?: string;
}

export interface ObserverLogNavItem {
  readonly jobId: string;
  readonly label: string;
  readonly filePath: string;
  readonly selected: boolean;
}

export interface ObserverSource {
  readonly projectFolder: string;
  readonly selectedLogPath: string;
  readonly logs: readonly ObserverLogNavItem[];
  readonly selectedLog: unknown;
  readonly companionReport?: unknown;
  readonly filters?: ObserverFilters;
  readonly live?: ObserverLiveInfo;
  readonly rawContentVisible?: boolean;
  readonly autoScroll?: boolean;
}

export interface ObserverTimelineCard {
  readonly id: string;
  readonly category: "message" | "reply" | "event" | "done";
  readonly state: ObserverState;
  readonly title: string;
  readonly excerpt: string;
  readonly timestamp?: string;
  readonly roleIcon: string;
  readonly from?: string;
  readonly to?: string;
  readonly conversation_id?: string;
  readonly correlation_id?: string;
  readonly message_id?: string;
  readonly reply_to?: string;
  readonly fromThreadId?: string;
  readonly toThreadId?: string;
  readonly round?: number;
  readonly payloadLines: readonly PayloadLine[];
  readonly metadata: Readonly<Record<string, string>>;
}

export interface PayloadLine {
  readonly label: string;
  readonly value: string;
}

export interface ConversationObserverModel {
  readonly projectFolder: string;
  readonly selectedLogPath: string;
  readonly selectedJobId: string;
  readonly filters: ObserverFilters;
  readonly live?: ObserverLiveInfo;
  readonly rawContentVisible: boolean;
  readonly autoScroll: boolean;
  readonly logs: readonly ObserverLogNavItem[];
  readonly cards: readonly ObserverTimelineCard[];
  readonly allCardsCount: number;
  readonly stateCounts: Readonly<Record<ObserverState, number>>;
  readonly boundary: {
    readonly observer_surface: "LOCAL_ONLY_COMMANDER_VIEW";
    readonly raw_dialogue_content: "DISPLAY_ALLOWED_IN_OBSERVER_ONLY";
    readonly external_review_package_raw_payload: "DEFAULT_DENY";
    readonly message_bus_mutation: "NOT_USED";
    readonly live_routing_or_resume: "NOT_USED";
    readonly governance: "OUT_OF_SCOPE";
    readonly agents_md_interpretation: "OUT_OF_SCOPE";
    readonly phase8_direct_real_repo: "BLOCKED";
  };
}

interface DialogueEnvelope {
  readonly type: "MESSAGE_TO_CODEX" | "CODEX_MESSAGE_REPLY" | "DONE";
  readonly message_id?: string;
  readonly reply_to?: string;
  readonly conversation_id?: string;
  readonly correlation_id?: string;
  readonly from?: string;
  readonly to?: string;
  readonly kind?: string;
  readonly payload?: unknown;
  readonly summary?: string;
  readonly evidence?: unknown;
}

interface EventRecord {
  readonly event: string;
  readonly timestamp?: string;
  readonly state?: string;
  readonly message_id?: string;
  readonly reply_to?: string;
  readonly conversation_id?: string;
  readonly correlation_id?: string;
  readonly from?: string;
  readonly to?: string;
  readonly fromThreadId?: string;
  readonly toThreadId?: string;
  readonly round?: number;
}

export function createConversationObserverModel(input: ObserverSource): ConversationObserverModel {
  const selectedJobId = getJobId(input.selectedLog, input.selectedLogPath);
  const sourceRoots = [input.selectedLog, input.companionReport].filter((value): value is unknown => value !== undefined);
  const envelopes = uniqueEnvelopes(sourceRoots.flatMap((source) => collectDialogueEnvelopes(source)));
  const events = uniqueEvents(sourceRoots.flatMap((source) => collectEventRecords(source)));
  const cards = [
    ...envelopes.map((envelope, index) => createEnvelopeCard(envelope, events, index)),
    ...createUnmatchedEventCards(events, envelopes),
  ].sort(compareCards);
  const filteredCards = cards.filter((card) => matchesFilters(card, input.filters ?? {}));
  return {
    projectFolder: input.projectFolder,
    selectedLogPath: input.selectedLogPath,
    selectedJobId,
    filters: input.filters ?? {},
    live: input.live,
    rawContentVisible: input.rawContentVisible ?? true,
    autoScroll: input.autoScroll ?? false,
    logs: input.logs,
    cards: filteredCards,
    allCardsCount: cards.length,
    stateCounts: countStates(filteredCards),
    boundary: {
      observer_surface: "LOCAL_ONLY_COMMANDER_VIEW",
      raw_dialogue_content: "DISPLAY_ALLOWED_IN_OBSERVER_ONLY",
      external_review_package_raw_payload: "DEFAULT_DENY",
      message_bus_mutation: "NOT_USED",
      live_routing_or_resume: "NOT_USED",
      governance: "OUT_OF_SCOPE",
      agents_md_interpretation: "OUT_OF_SCOPE",
      phase8_direct_real_repo: "BLOCKED",
    },
  };
}

export function renderObserverTranscript(model: ConversationObserverModel): string {
  const lines = [
    `Conversation Observer: ${model.selectedJobId}`,
    `Project: ${model.projectFolder}`,
    `Log: ${model.selectedLogPath}`,
    `Mode: ${model.live ? "live-tail" : "static"}`,
    ...(model.live ? [`Live status: ${model.live.status}`, `Watched: ${model.live.watchedPath}`] : []),
    `Cards: ${model.cards.length}/${model.allCardsCount}`,
    "",
  ];
  for (const card of model.cards) {
    lines.push(`[${card.timestamp ?? "no timestamp"}] ${card.from ?? "system"} -> ${card.to ?? "system"}`);
    lines.push(`state: ${card.state}`);
    if (card.conversation_id) lines.push(`conversation: ${card.conversation_id}`);
    if (card.message_id) lines.push(`message: ${card.message_id}`);
    if (card.reply_to) lines.push(`reply_to: ${card.reply_to}`);
    if (card.correlation_id) lines.push(`correlation: ${card.correlation_id}`);
    if (card.fromThreadId) lines.push(`fromThreadId: ${card.fromThreadId}`);
    if (card.toThreadId) lines.push(`toThreadId: ${card.toThreadId}`);
    if (card.round !== undefined) lines.push(`round: ${card.round}`);
    lines.push("");
    if (model.rawContentVisible) {
      for (const payload of card.payloadLines) {
        lines.push(`${payload.label}:`);
        lines.push(payload.value);
        lines.push("");
      }
    } else {
      lines.push("Payload:");
      lines.push("<HIDDEN_IN_OBSERVER_VIEW>");
      lines.push("");
    }
    lines.push("---");
  }
  return lines.join("\n");
}

export function renderObserverHtml(model: ConversationObserverModel): string {
  const stateClass = (state: ObserverState): string => `state-${state.toLowerCase()}`;
  return [
    "<!doctype html>",
    '<html lang="en">',
    "<head>",
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    ...(model.live ? [`<meta http-equiv="refresh" content="${Math.max(1, Math.ceil(model.live.pollMs / 1000))}">`] : []),
    `<title>${escapeHtml(model.selectedJobId)} Observer</title>`,
    "<style>",
    css(),
    "</style>",
    "</head>",
    "<body>",
    '<div class="app-shell">',
    '<aside class="sidebar">',
    "<h1>Observer</h1>",
    `<details class="project-group" open><summary>${escapeHtml(model.projectFolder)}</summary>`,
    '<nav class="thread-queue">',
    ...model.logs.map((log) =>
      `<a class="${log.selected ? "selected" : ""}" href="#${escapeAttribute(log.jobId)}"><span>${escapeHtml(log.label)}</span><small>${escapeHtml(log.jobId)}</small></a>`,
    ),
    "</nav>",
    "</details>",
    "</aside>",
    '<main class="timeline-panel">',
    '<header class="toolbar">',
    "<div>",
    `<p class="eyebrow">${escapeHtml(model.projectFolder)}</p>`,
    `<h2>${escapeHtml(model.selectedJobId)}</h2>`,
    ...(model.live ? [renderLiveStatus(model.live)] : []),
    "</div>",
    '<div class="filters">',
    filterChip("conversation", model.filters.conversationId),
    filterChip("role", model.filters.role),
    filterChip("state", model.filters.state),
    `<span>raw: ${model.rawContentVisible ? "visible" : "hidden"}</span>`,
    `<span>${model.cards.length}/${model.allCardsCount} cards</span>`,
    '<button class="payload-toggle" type="button" onclick="document.body.classList.toggle(\'hide-payload\')">Toggle Raw</button>',
    "</div>",
    "</header>",
    '<section class="timeline">',
    ...model.cards.map((card, index) => renderCard(card, stateClass(card.state), model.rawContentVisible, index === model.cards.length - 1)),
    "</section>",
    "</main>",
    '<aside class="meta-panel">',
    "<h2>Boundary</h2>",
    ...Object.entries(model.boundary).map(([key, value]) => `<dl><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></dl>`),
    "<h2>States</h2>",
    ...Object.entries(model.stateCounts).map(([state, count]) => `<dl><dt>${escapeHtml(state)}</dt><dd>${count}</dd></dl>`),
    "</aside>",
    "</div>",
    "<script>",
    clientScript(model.autoScroll),
    "</script>",
    "</body>",
    "</html>",
  ].join("\n");
}

export function createObserverLiveSnapshot(model: ConversationObserverModel): Record<string, unknown> {
  return {
    selected_job_id: model.selectedJobId,
    selected_log_path: model.selectedLogPath,
    mode: model.live ? "live-tail" : "static",
    live: model.live,
    filters: model.filters,
    raw_content_visible: model.rawContentVisible,
    cards: model.cards,
    all_cards_count: model.allCardsCount,
    state_counts: model.stateCounts,
    boundary: model.boundary,
  };
}

function renderLiveStatus(live: ObserverLiveInfo): string {
  const classes = `live-status live-${live.status.toLowerCase()}`;
  const details = [
    `watched: ${live.watchedPath}`,
    live.snapshotPath ? `snapshot: ${live.snapshotPath}` : undefined,
    live.lastEventAt ? `last event: ${live.lastEventAt}` : undefined,
    live.note,
  ].filter(isString);
  return [
    `<div class="${classes}">`,
    `<strong>${escapeHtml(live.status)}</strong>`,
    `<span>updated ${escapeHtml(live.lastUpdatedAt)}</span>`,
    ...details.map((detail) => `<small>${escapeHtml(detail)}</small>`),
    "</div>",
  ].join("\n");
}

function renderCard(card: ObserverTimelineCard, stateClass: string, rawContentVisible: boolean, isLatest: boolean): string {
  return [
    `<article class="timeline-card ${stateClass}${isLatest ? " latest-card" : ""}" id="${escapeAttribute(card.id)}" data-card-id="${escapeAttribute(card.id)}">`,
    '<div class="marker">',
    `<span>${escapeHtml(card.roleIcon)}</span>`,
    "</div>",
    '<div class="card-body">',
    '<header class="card-head">',
    "<div>",
    `<p>${escapeHtml(card.timestamp ?? "no timestamp")}</p>`,
    `<h3>${escapeHtml(card.title)}</h3>`,
    "</div>",
    `<strong>${escapeHtml(card.state)}</strong>`,
    "</header>",
    `<p class="excerpt">${escapeHtml(card.excerpt)}</p>`,
    rawContentVisible
      ? ['<div class="payload">', ...card.payloadLines.map((line) => `<section><h4>${escapeHtml(line.label)}</h4><pre>${escapeHtml(line.value)}</pre></section>`), "</div>"].join("\n")
      : '<div class="payload payload-hidden"><section><h4>Payload</h4><pre>&lt;HIDDEN_IN_OBSERVER_VIEW&gt;</pre></section></div>',
    '<dl class="metadata">',
    ...Object.entries(card.metadata).map(([key, value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`),
    "</dl>",
    "</div>",
    "</article>",
  ].join("\n");
}

function filterChip(label: string, value: string | undefined): string {
  return `<span>${escapeHtml(label)}: ${escapeHtml(value ?? "all")}</span>`;
}

function createEnvelopeCard(
  envelope: DialogueEnvelope,
  events: readonly EventRecord[],
  index: number,
): ObserverTimelineCard {
  const event = bestMatchingEvent(envelope, events);
  const category = envelope.type === "DONE" ? "done" : envelope.type === "CODEX_MESSAGE_REPLY" ? "reply" : "message";
  const state = stateFromEnvelope(envelope, event);
  const payloadLines = payloadLinesForEnvelope(envelope);
  const from = envelope.from ?? event?.from;
  const to = envelope.to ?? event?.to;
  const title = titleForEnvelope(envelope);
  const excerpt = firstUsefulPayloadValue(payloadLines) ?? title;
  return {
    id: envelope.message_id ?? `${category}-${index}`,
    category,
    state,
    title,
    excerpt,
    timestamp: event?.timestamp,
    roleIcon: roleIcon(from, category),
    from,
    to,
    conversation_id: envelope.conversation_id ?? event?.conversation_id,
    correlation_id: envelope.correlation_id ?? event?.correlation_id,
    message_id: envelope.message_id ?? event?.message_id,
    reply_to: envelope.reply_to ?? event?.reply_to,
    fromThreadId: event?.fromThreadId,
    toThreadId: event?.toThreadId,
    round: event?.round,
    payloadLines,
    metadata: metadataFrom({
      conversation_id: envelope.conversation_id ?? event?.conversation_id,
      correlation_id: envelope.correlation_id ?? event?.correlation_id,
      message_id: envelope.message_id ?? event?.message_id,
      reply_to: envelope.reply_to ?? event?.reply_to,
      from,
      to,
      fromThreadId: event?.fromThreadId,
      toThreadId: event?.toThreadId,
      round: event?.round,
    }),
  };
}

function createUnmatchedEventCards(
  events: readonly EventRecord[],
  envelopes: readonly DialogueEnvelope[],
): readonly ObserverTimelineCard[] {
  const envelopeKeys = new Set(envelopes.flatMap((envelope) => [envelope.message_id, envelope.reply_to].filter(isString)));
  return events
    .filter((event) => shouldRenderEventCard(event, envelopeKeys))
    .map((event, index) => {
      const state = stateFromEvent(event);
      return {
        id: `${event.event}-${event.message_id ?? event.conversation_id ?? index}`,
        category: "event",
        state,
        title: titleForEvent(event),
        excerpt: event.event,
        timestamp: event.timestamp,
        roleIcon: roleIcon(event.from, "event"),
        from: event.from,
        to: event.to,
        conversation_id: event.conversation_id,
        correlation_id: event.correlation_id,
        message_id: event.message_id,
        reply_to: event.reply_to,
        fromThreadId: event.fromThreadId,
        toThreadId: event.toThreadId,
        round: event.round,
        payloadLines: [{ label: "Event", value: event.event }],
        metadata: metadataFrom(event),
      };
    });
}

function shouldRenderEventCard(event: EventRecord, envelopeKeys: ReadonlySet<string>): boolean {
  if (["MESSAGE_REJECTED", "MESSAGE_EXPIRED", "CONVERSATION_BLOCKED", "CHANNEL_DONE"].includes(event.event)) {
    return true;
  }
  if (event.message_id && envelopeKeys.has(event.message_id)) return false;
  if (event.reply_to && envelopeKeys.has(event.reply_to)) return false;
  return event.event.includes("OBSERVED") || event.event.includes("FAILED");
}

function bestMatchingEvent(envelope: DialogueEnvelope, events: readonly EventRecord[]): EventRecord | undefined {
  const candidates = events.filter((event) => {
    if (envelope.type === "DONE") return event.event === "CHANNEL_DONE";
    if (envelope.type === "CODEX_MESSAGE_REPLY") return event.message_id === envelope.message_id || event.reply_to === envelope.reply_to;
    return event.message_id === envelope.message_id;
  });
  return candidates.sort((left, right) => eventPriority(right) - eventPriority(left))[0];
}

function eventPriority(event: EventRecord): number {
  switch (event.event) {
    case "CHANNEL_DONE":
      return 90;
    case "CONVERSATION_BLOCKED":
      return 80;
    case "MESSAGE_REJECTED":
      return 70;
    case "MESSAGE_EXPIRED":
      return 60;
    case "REPLY_ROUTED":
    case "MESSAGE_ROUTED":
      return 50;
    case "REPLY_OBSERVED":
    case "MESSAGE_OBSERVED":
      return 45;
    case "REPLY_CAPTURED":
    case "MESSAGE_CAPTURED":
      return 30;
    default:
      return 10;
  }
}

function collectDialogueEnvelopes(value: unknown): readonly DialogueEnvelope[] {
  const found: DialogueEnvelope[] = [];
  walk(value, (candidate) => {
    if (isDialogueEnvelope(candidate)) {
      found.push(candidate as unknown as DialogueEnvelope);
    }
  });
  return found;
}

function collectEventRecords(value: unknown): readonly EventRecord[] {
  const found: EventRecord[] = [];
  walk(value, (candidate) => {
    if (isEventRecord(candidate)) {
      found.push(candidate as unknown as EventRecord);
    }
  });
  return found;
}

function walk(value: unknown, visit: (record: Record<string, unknown>) => void): void {
  if (Array.isArray(value)) {
    for (const child of value) walk(child, visit);
    return;
  }
  if (!isRecord(value)) return;
  visit(value);
  for (const child of Object.values(value)) walk(child, visit);
}

function isDialogueEnvelope(value: Record<string, unknown>): boolean {
  if (value.type === "MESSAGE_TO_CODEX") {
    return isString(value.message_id) && isString(value.conversation_id);
  }
  if (value.type === "CODEX_MESSAGE_REPLY") {
    return isString(value.message_id) && isString(value.reply_to);
  }
  if (value.type === "DONE") {
    return isString(value.summary);
  }
  return false;
}

function isEventRecord(value: Record<string, unknown>): boolean {
  return isString(value.event) && (isString(value.timestamp) || isString(value.message_id) || isString(value.conversation_id));
}

function uniqueEnvelopes(envelopes: readonly DialogueEnvelope[]): readonly DialogueEnvelope[] {
  const seen = new Set<string>();
  const unique: DialogueEnvelope[] = [];
  for (const envelope of envelopes) {
    const key = `${envelope.type}:${envelope.message_id ?? envelope.reply_to ?? envelope.summary ?? unique.length}`;
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(envelope);
  }
  return unique;
}

function uniqueEvents(events: readonly EventRecord[]): readonly EventRecord[] {
  const seen = new Set<string>();
  const unique: EventRecord[] = [];
  for (const event of events) {
    const key = [
      event.event,
      event.timestamp,
      event.message_id,
      event.reply_to,
      event.conversation_id,
      event.round,
    ].join(":");
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(event);
  }
  return unique;
}

function payloadLinesForEnvelope(envelope: DialogueEnvelope): readonly PayloadLine[] {
  if (envelope.type === "DONE") {
    return [
      { label: "Summary", value: formatDisplayValue(envelope.summary) },
      { label: "Evidence", value: formatDisplayValue(envelope.evidence) },
    ].filter((line) => line.value.length > 0);
  }
  if (!isRecord(envelope.payload)) {
    return [{ label: "Payload", value: formatDisplayValue(envelope.payload) }];
  }
  return Object.entries(envelope.payload).map(([key, value]) => ({
    label: titleCase(key),
    value: formatDisplayValue(value, key),
  }));
}

function formatDisplayValue(value: unknown, key?: string): string {
  if (key && isSecretLikeKey(key)) return "<REDACTED_SECRET_LIKE_FIELD>";
  if (value === undefined || value === null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    if (value.length === 0) return "[]";
    return value.map((item) => `- ${formatDisplayValue(item)}`).join("\n");
  }
  if (isRecord(value)) {
    return Object.entries(value)
      .map(([childKey, child]) => `${childKey}: ${formatDisplayValue(child, childKey)}`)
      .join("\n");
  }
  return String(value);
}

function isSecretLikeKey(key: string): boolean {
  return /secret|token|password|credential|cookie|api[_-]?key|private[_-]?key/i.test(key);
}

function titleForEnvelope(envelope: DialogueEnvelope): string {
  if (envelope.type === "MESSAGE_TO_CODEX") return `${envelope.from ?? "agent"} to ${envelope.to ?? "agent"} ${envelope.kind ?? "message"}`;
  if (envelope.type === "CODEX_MESSAGE_REPLY") return `${envelope.from ?? "agent"} reply to ${envelope.reply_to ?? "message"}`;
  return "Conversation done";
}

function titleForEvent(event: EventRecord): string {
  return event.event
    .toLowerCase()
    .split("_")
    .map(titleCase)
    .join(" ");
}

function titleCase(value: string): string {
  if (!value) return value;
  return `${value[0]?.toUpperCase() ?? ""}${value.slice(1).replace(/_/g, " ")}`;
}

function firstUsefulPayloadValue(lines: readonly PayloadLine[]): string | undefined {
  return lines.find((line) => line.value.length > 0)?.value.split(/\r?\n/)[0];
}

function stateFromEnvelope(envelope: DialogueEnvelope, event: EventRecord | undefined): ObserverState {
  if (event) return stateFromEvent(event);
  if (envelope.type === "DONE") return "DONE";
  if (envelope.type === "CODEX_MESSAGE_REPLY") return "REPLIED";
  return "CAPTURED";
}

function stateFromEvent(event: EventRecord): ObserverState {
  const direct = normalizeState(event.state);
  if (direct !== "UNKNOWN") return direct;
  switch (event.event) {
    case "MESSAGE_CAPTURED":
    case "REPLY_CAPTURED":
      return "CAPTURED";
    case "MESSAGE_ROUTED":
      return "ROUTED";
    case "REPLY_ROUTED":
    case "WORKER_RESUMED":
      return "REPLIED";
    case "MESSAGE_OBSERVED":
    case "REPLY_OBSERVED":
      return "OBSERVED";
    case "MESSAGE_REJECTED":
      return "REJECTED";
    case "MESSAGE_EXPIRED":
      return "EXPIRED";
    case "CONVERSATION_BLOCKED":
      return "BLOCKED";
    case "CHANNEL_DONE":
      return "DONE";
    default:
      return "UNKNOWN";
  }
}

function normalizeState(value: unknown): ObserverState {
  if (!isString(value)) return "UNKNOWN";
  const normalized = value.toUpperCase();
  if (
    normalized === "CAPTURED" ||
    normalized === "ROUTED" ||
    normalized === "REPLIED" ||
    normalized === "OBSERVED" ||
    normalized === "REJECTED" ||
    normalized === "EXPIRED" ||
    normalized === "FAILED" ||
    normalized === "BLOCKED" ||
    normalized === "DONE"
  ) {
    return normalized;
  }
  return "UNKNOWN";
}

function metadataFrom(value: {
  readonly conversation_id?: string;
  readonly correlation_id?: string;
  readonly message_id?: string;
  readonly reply_to?: string;
  readonly from?: string;
  readonly to?: string;
  readonly fromThreadId?: string;
  readonly toThreadId?: string;
  readonly round?: number;
}): Readonly<Record<string, string>> {
  const entries = Object.entries({
    conversation_id: value.conversation_id,
    correlation_id: value.correlation_id,
    message_id: value.message_id,
    reply_to: value.reply_to,
    from: value.from,
    to: value.to,
    fromThreadId: value.fromThreadId,
    toThreadId: value.toThreadId,
    round: value.round === undefined ? undefined : String(value.round),
  }).filter((entry): entry is [string, string] => typeof entry[1] === "string" && entry[1].length > 0);
  return Object.fromEntries(entries);
}

function roleIcon(role: string | undefined, category: ObserverTimelineCard["category"]): string {
  if (role) return role.slice(0, 1).toUpperCase();
  if (category === "done") return "D";
  return "E";
}

function matchesFilters(card: ObserverTimelineCard, filters: ObserverFilters): boolean {
  if (filters.conversationId && card.conversation_id !== filters.conversationId) return false;
  if (filters.role && card.from !== filters.role && card.to !== filters.role) return false;
  if (filters.state && card.state.toLowerCase() !== filters.state.toLowerCase()) return false;
  return true;
}

function compareCards(left: ObserverTimelineCard, right: ObserverTimelineCard): number {
  const leftTime = left.timestamp ? Date.parse(left.timestamp) : Number.POSITIVE_INFINITY;
  const rightTime = right.timestamp ? Date.parse(right.timestamp) : Number.POSITIVE_INFINITY;
  if (leftTime !== rightTime) return leftTime - rightTime;
  return left.id.localeCompare(right.id);
}

function countStates(cards: readonly ObserverTimelineCard[]): Readonly<Record<ObserverState, number>> {
  const states: ObserverState[] = ["CAPTURED", "ROUTED", "REPLIED", "OBSERVED", "REJECTED", "EXPIRED", "FAILED", "BLOCKED", "DONE", "UNKNOWN"];
  const counts = Object.fromEntries(states.map((state) => [state, 0])) as Record<ObserverState, number>;
  for (const card of cards) {
    counts[card.state] += 1;
  }
  return counts;
}

function getJobId(log: unknown, selectedLogPath: string): string {
  if (isRecord(log) && isString(log.job_id)) return log.job_id;
  const match = /([^\\/]+)\.json$/i.exec(selectedLogPath);
  return match?.[1] ?? "unknown-log";
}

function escapeHtml(value: unknown): string {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeAttribute(value: unknown): string {
  return escapeHtml(value).replace(/\s+/g, "-");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

function css(): string {
  return `
:root {
  color-scheme: dark;
  --bg: #04070d;
  --panel: #10151f;
  --panel-strong: #161d2b;
  --text: #e8edf7;
  --muted: #9aa7ba;
  --line: #2a3547;
  --routed: #36b37e;
  --observed: #7aa2ff;
  --rejected: #f79009;
  --blocked: #f97066;
  --done: #b8c3d8;
}
* { box-sizing: border-box; }
html {
  background: var(--bg);
}
body {
  margin: 0;
  background:
    radial-gradient(circle at 12% 18%, rgba(255, 255, 255, 0.9) 0 1px, transparent 1.4px),
    radial-gradient(circle at 75% 32%, rgba(122, 162, 255, 0.8) 0 1px, transparent 1.3px),
    radial-gradient(circle at 38% 72%, rgba(255, 255, 255, 0.55) 0 1px, transparent 1.2px),
    linear-gradient(180deg, #04070d 0%, #0a0f1a 46%, #04070d 100%);
  background-size: 220px 220px, 300px 300px, 260px 260px, auto;
  color: var(--text);
  font: 14px/1.45 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  animation: star-drift 42s linear infinite;
}
@keyframes star-drift {
  from { background-position: 0 0, 0 0, 0 0, 0 0; }
  to { background-position: 220px 140px, -300px 120px, 160px -260px, 0 0; }
}
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(0, 1fr) minmax(220px, 280px);
}
.sidebar, .meta-panel {
  background: rgba(10, 15, 26, 0.92);
  border-right: 1px solid var(--line);
  padding: 18px;
  overflow: auto;
  backdrop-filter: blur(10px);
}
.meta-panel {
  border-right: 0;
  border-left: 1px solid var(--line);
}
h1, h2, h3, h4, p { margin: 0; }
h1 { font-size: 18px; margin-bottom: 18px; }
h2 { font-size: 18px; }
.project-group summary {
  cursor: pointer;
  font-weight: 700;
  margin-bottom: 10px;
}
.thread-queue {
  display: grid;
  gap: 6px;
}
.thread-queue a {
  display: grid;
  gap: 2px;
  color: inherit;
  text-decoration: none;
  padding: 8px;
  border: 1px solid transparent;
  border-radius: 6px;
}
.thread-queue a.selected {
  background: var(--panel-strong);
  border-color: var(--line);
}
.thread-queue small, .eyebrow, .card-head p, .metadata dt, .filters span, .meta-panel dt {
  color: var(--muted);
  font-size: 12px;
}
.timeline-panel {
  min-width: 0;
  padding: 20px 24px;
  overflow: auto;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 22px;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}
.filters span {
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(16, 21, 31, 0.94);
  padding: 4px 8px;
}
.payload-toggle {
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(22, 29, 43, 0.94);
  color: var(--text);
  padding: 4px 10px;
  cursor: pointer;
}
.hide-payload .payload {
  display: none;
}
.live-status {
  margin-top: 8px;
  display: grid;
  gap: 2px;
}
.live-status strong {
  width: fit-content;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 12px;
}
.live-status span, .live-status small {
  color: var(--muted);
  overflow-wrap: anywhere;
}
.live-live strong { color: #9ff0c8; border-color: rgba(54, 179, 126, 0.6); }
.live-paused strong { color: #d0d5dd; }
.live-stale strong { color: #ffd18a; border-color: rgba(247, 144, 9, 0.7); }
.live-error strong { color: #ffb4ad; border-color: rgba(249, 112, 102, 0.7); }
.timeline {
  position: relative;
  display: grid;
  gap: 14px;
}
.timeline::before {
  content: "";
  position: absolute;
  left: 18px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--line);
}
.timeline-card {
  position: relative;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 12px;
}
.marker {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
}
.marker span {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--done);
  color: white;
  font-weight: 700;
}
.card-body {
  background: rgba(16, 21, 31, 0.94);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
}
.latest-card .card-body {
  border-color: rgba(122, 162, 255, 0.9);
}
.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.card-head strong {
  font-size: 12px;
  letter-spacing: 0;
}
.excerpt {
  margin-bottom: 10px;
}
.payload {
  display: grid;
  gap: 8px;
}
.payload section {
  border-top: 1px solid var(--line);
  padding-top: 8px;
}
.payload h4 {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 3px;
}
pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  margin: 0;
  font: 13px/1.4 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
}
.payload-hidden pre {
  color: var(--muted);
}
.metadata {
  margin: 10px 0 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 6px 10px;
}
.metadata div, .meta-panel dl {
  margin: 0;
}
.metadata dd, .meta-panel dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.state-routed .marker span { background: var(--routed); }
.state-observed .marker span { background: var(--observed); }
.state-rejected .marker span, .state-expired .marker span { background: var(--rejected); }
.state-blocked .marker span, .state-failed .marker span { background: var(--blocked); }
.state-done .marker span, .state-replied .marker span { background: var(--done); }
.meta-panel h2 {
  margin: 0 0 10px;
}
.meta-panel h2 + dl, .meta-panel dl + dl {
  margin-top: 8px;
}
@media (max-width: 960px) {
  .app-shell {
    grid-template-columns: 1fr;
  }
  .sidebar, .meta-panel {
    border: 0;
    border-bottom: 1px solid var(--line);
  }
  .toolbar {
    display: grid;
  }
  .filters {
    justify-content: flex-start;
  }
}`;
}

function clientScript(autoScroll: boolean): string {
  return `
(function () {
  var key = "codex-observer-scroll:" + location.pathname;
  if (${autoScroll ? "true" : "false"}) {
    requestAnimationFrame(function () { window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }); });
    return;
  }
  window.addEventListener("beforeunload", function () {
    sessionStorage.setItem(key, String(window.scrollY));
  });
  var saved = sessionStorage.getItem(key);
  if (saved !== null) {
    requestAnimationFrame(function () { window.scrollTo(0, Number(saved)); });
  }
})();`;
}
