import type { Turn } from "../generated/appserver/v2/Turn";

export function assertLiveTurnCompleted(turn: Turn, label = "live turn"): Turn {
  if (turn.status === "completed") {
    return turn;
  }
  if (turn.status === "failed") {
    throw new Error(formatTurnFailure(turn, label));
  }
  throw new Error(`${label} ended without completion: ${turn.id}: status=${turn.status}`);
}

export function rejectLiveTerminalNonCompletedTurn(turn: Turn, label = "live turn"): void {
  if (turn.status !== "inProgress") {
    assertLiveTurnCompleted(turn, label);
  }
}

function formatTurnFailure(turn: Turn, label: string): string {
  const message = turn.error?.message ?? "unknown turn failure";
  return `${label} failed: ${turn.id}: ${message}`;
}
