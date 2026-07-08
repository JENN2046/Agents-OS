export const activeLoopStates = [
  "CREATED",
  "APP_SERVER_STARTED",
  "INITIALIZED",
  "SCHEMA_GENERATED",
  "SYNTHETIC_WORKSPACE_READY",
  "WORKER_THREAD_STARTED",
  "WORKER_RUNNING",
  "NEED_REVIEWER",
  "REVIEWER_THREAD_STARTED",
  "REVIEWER_RUNNING",
  "REVIEW_RECEIVED",
  "CODEX_RESUMED",
  "DONE",
  "BLOCKED",
  "HUMAN_GATE_REQUIRED",
  "FAILED",
] as const;

export type ActiveLoopState = (typeof activeLoopStates)[number];

export interface StateTransition {
  readonly from: ActiveLoopState;
  readonly to: ActiveLoopState;
  readonly reason: string;
  readonly at: string;
}

export interface TransitionResult {
  readonly ok: boolean;
  readonly state: ActiveLoopState;
  readonly transition: StateTransition;
  readonly error?: string;
}

export const terminalStates: ReadonlySet<ActiveLoopState> = new Set([
  "DONE",
  "BLOCKED",
  "HUMAN_GATE_REQUIRED",
  "FAILED",
]);

const allowedTransitions: ReadonlyMap<ActiveLoopState, ReadonlySet<ActiveLoopState>> = new Map([
  ["CREATED", new Set(["APP_SERVER_STARTED", "BLOCKED", "FAILED"])],
  ["APP_SERVER_STARTED", new Set(["INITIALIZED", "BLOCKED", "FAILED"])],
  ["INITIALIZED", new Set(["SCHEMA_GENERATED", "BLOCKED", "FAILED"])],
  ["SCHEMA_GENERATED", new Set(["SYNTHETIC_WORKSPACE_READY", "BLOCKED", "FAILED"])],
  ["SYNTHETIC_WORKSPACE_READY", new Set(["WORKER_THREAD_STARTED", "BLOCKED", "FAILED"])],
  ["WORKER_THREAD_STARTED", new Set(["WORKER_RUNNING", "BLOCKED", "FAILED"])],
  ["WORKER_RUNNING", new Set(["NEED_REVIEWER", "HUMAN_GATE_REQUIRED", "BLOCKED", "FAILED"])],
  ["NEED_REVIEWER", new Set(["REVIEWER_THREAD_STARTED", "HUMAN_GATE_REQUIRED", "BLOCKED", "FAILED"])],
  ["REVIEWER_THREAD_STARTED", new Set(["REVIEWER_RUNNING", "BLOCKED", "FAILED"])],
  ["REVIEWER_RUNNING", new Set(["REVIEW_RECEIVED", "HUMAN_GATE_REQUIRED", "BLOCKED", "FAILED"])],
  ["REVIEW_RECEIVED", new Set(["CODEX_RESUMED", "HUMAN_GATE_REQUIRED", "BLOCKED", "FAILED"])],
  ["CODEX_RESUMED", new Set(["DONE", "HUMAN_GATE_REQUIRED", "BLOCKED", "FAILED"])],
  ["DONE", new Set()],
  ["BLOCKED", new Set()],
  ["HUMAN_GATE_REQUIRED", new Set()],
  ["FAILED", new Set()],
]);

export function isActiveLoopState(value: string): value is ActiveLoopState {
  return (activeLoopStates as readonly string[]).includes(value);
}

export function canTransition(from: ActiveLoopState, to: ActiveLoopState): boolean {
  return allowedTransitions.get(from)?.has(to) ?? false;
}

export function transitionState(
  from: ActiveLoopState,
  to: ActiveLoopState,
  reason: string,
  now = new Date(),
): TransitionResult {
  const at = now.toISOString();
  if (!canTransition(from, to)) {
    return {
      ok: false,
      state: "BLOCKED",
      transition: {
        from,
        to: "BLOCKED",
        reason: `invalid transition ${from} -> ${to}: ${reason}`,
        at,
      },
      error: `invalid transition ${from} -> ${to}`,
    };
  }

  return {
    ok: true,
    state: to,
    transition: { from, to, reason, at },
  };
}
