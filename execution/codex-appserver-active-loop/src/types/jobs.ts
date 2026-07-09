import type { ActiveLoopState } from "../bridge/state_machine.js";

export interface JobRecord {
  readonly jobId: string;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly state: ActiveLoopState;
  readonly syntheticWorkspaceRoot: string;
  readonly eventLogPath?: string;
  readonly receiptPath?: string;
  readonly reportPath?: string;
  readonly boundaryFlags?: Record<string, "USED" | "NOT_USED" | "BLOCKED" | "REDACTED">;
}
