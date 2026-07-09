import type { ActiveLoopState, StateTransition } from "../bridge/state_machine.js";

export type LoopEventType =
  | "STATE_TRANSITION"
  | "POLICY_DECISION"
  | "APP_SERVER_MESSAGE"
  | "RECEIPT_WRITTEN"
  | "REPORT_WRITTEN";

export interface LoopEvent {
  readonly jobId: string;
  readonly type: LoopEventType;
  readonly at: string;
  readonly state?: ActiveLoopState;
  readonly payload?: unknown;
}

export function createStateTransitionEvent(jobId: string, transition: StateTransition): LoopEvent {
  return {
    jobId,
    type: "STATE_TRANSITION",
    at: transition.at,
    state: transition.to,
    payload: transition,
  };
}
