import { describe, expect, it } from "vitest";
import type { Turn } from "../../src/generated/appserver/v2/Turn.js";
import { assertLiveTurnCompleted, rejectLiveTerminalNonCompletedTurn } from "../../src/bridge/live_turn_completion.js";

describe("live turn completion guard", () => {
  it("accepts completed turns", () => {
    const turn = makeTurn("completed");

    expect(assertLiveTurnCompleted(turn, "Worker live turn")).toBe(turn);
  });

  it("allows in-progress turns to keep waiting", () => {
    expect(() => rejectLiveTerminalNonCompletedTurn(makeTurn("inProgress"), "Worker live turn")).not.toThrow();
    expect(() => assertLiveTurnCompleted(makeTurn("inProgress"), "Worker live turn")).toThrow("status=inProgress");
  });

  it("rejects interrupted turns before output parsing", () => {
    expect(() => assertLiveTurnCompleted(makeTurn("interrupted"), "Worker live turn")).toThrow("status=interrupted");
    expect(() => rejectLiveTerminalNonCompletedTurn(makeTurn("interrupted"), "Reviewer live turn")).toThrow(
      "Reviewer live turn ended without completion",
    );
  });

  it("keeps failed turn errors explicit", () => {
    expect(() => assertLiveTurnCompleted(makeTurn("failed", "turn failed"), "Worker live turn")).toThrow("turn failed");
  });
});

function makeTurn(status: string, message: string | null = null): Turn {
  return {
    id: "turn-1",
    items: [],
    itemsView: { type: "all" },
    status,
    error: message ? { message, codexErrorInfo: null, additionalDetails: null } : null,
    startedAt: null,
    completedAt: null,
    durationMs: null,
  } as unknown as Turn;
}
