import { describe, expect, it } from "vitest";
import {
  activeLoopStates,
  canTransition,
  transitionState,
  terminalStates,
} from "../../src/bridge/state_machine.js";

describe("state machine", () => {
  it("declares terminal and boundary states", () => {
    expect(activeLoopStates).toContain("DONE");
    expect(terminalStates.has("BLOCKED")).toBe(true);
    expect(terminalStates.has("HUMAN_GATE_REQUIRED")).toBe(true);
  });

  it("allows the happy path in order", () => {
    expect(canTransition("CREATED", "APP_SERVER_STARTED")).toBe(true);
    expect(canTransition("WORKER_RUNNING", "NEED_REVIEWER")).toBe(true);
    expect(canTransition("CODEX_RESUMED", "DONE")).toBe(true);
  });

  it("fails closed to BLOCKED for invalid transitions", () => {
    const result = transitionState("CREATED", "DONE", "cannot skip setup", new Date("2026-07-07T00:00:00.000Z"));

    expect(result.ok).toBe(false);
    expect(result.state).toBe("BLOCKED");
    expect(result.transition).toMatchObject({
      from: "CREATED",
      to: "BLOCKED",
      reason: "invalid transition CREATED -> DONE: cannot skip setup",
    });
  });

  it("does not allow transitions out of terminal states", () => {
    expect(canTransition("DONE", "CREATED")).toBe(false);
    expect(canTransition("BLOCKED", "FAILED")).toBe(false);
  });
});
