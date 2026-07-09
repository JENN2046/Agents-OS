import { mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import type { AppServerClient } from "../../src/appserver/client.js";
import {
  createActiveLoopOrchestrator,
  parseStructuredTurnOutput,
} from "../../src/bridge/orchestrator.js";
import { createFileEventStore } from "../../src/stores/event_store.js";
import { createFileJobStore } from "../../src/stores/job_store.js";
import { createFileReceiptStore } from "../../src/stores/receipt_store.js";
import type { Turn } from "../../src/generated/appserver/v2/Turn.js";
import type { ThreadStartParams } from "../../src/generated/appserver/v2/ThreadStartParams.js";
import type { TurnStartParams } from "../../src/generated/appserver/v2/TurnStartParams.js";
import type { ServerNotification } from "../../src/generated/appserver/ServerNotification.js";

const syntheticWorkspaceRoot = path.join(process.cwd(), "data", "synthetic-workspace");

class FakeLoopClient implements Pick<AppServerClient, "threadStart" | "turnStart" | "turnSteer"> {
  threadStarts: ThreadStartParams[] = [];
  turnStarts: TurnStartParams[] = [];
  startedTurns: Turn[] = [];
  notificationHandlers = new Set<(notification: ServerNotification) => void>();
  nextThread = 0;
  completeTurnsInStart = true;
  notifyCompletedTurns = false;
  initialTurnStatus = "inProgress";
  outputs: unknown[] = [
    {
      type: "NEED_REVIEWER",
      problem_type: "architecture",
      question: "Should the bridge continue?",
      evidence: ["sample.txt"],
      proposed_options: ["continue"],
      recommended_next_action: "ask reviewer",
    },
    {
      type: "REVIEWER_DECISION",
      decision: "continue",
      reason: "Synthetic workspace is safe",
      next_instruction: "finish",
      constraints: ["read-only"],
      evidence_used: ["sample.txt"],
    },
    {
      type: "DONE",
      summary: "Loop completed",
      evidence: ["receipt"],
    },
  ];

  async threadStart(params: ThreadStartParams) {
    this.threadStarts.push(params);
    const id = `thread-${++this.nextThread}`;
    return { thread: { id } } as Awaited<ReturnType<AppServerClient["threadStart"]>>;
  }

  async turnStart(params: TurnStartParams) {
    this.turnStarts.push(params);
    const output = this.outputs.shift();
    const turn = this.completeTurnsInStart ? makeTurn(JSON.stringify(output)) : makeTurn("", { status: this.initialTurnStatus });
    this.startedTurns.push(turn);
    if (!this.completeTurnsInStart && this.notifyCompletedTurns) {
      const completed = makeTurn(JSON.stringify(output), { id: turn.id });
      queueMicrotask(() => {
        this.emitNotification({ method: "turn/completed", params: { threadId: params.threadId, turn: completed } } as ServerNotification);
      });
    }
    return { turn };
  }

  async turnSteer() {
    return { turnId: "unused" };
  }

  onNotification(handler: (notification: ServerNotification) => void): () => void {
    this.notificationHandlers.add(handler);
    return () => this.notificationHandlers.delete(handler);
  }

  emitNotification(notification: ServerNotification): void {
    for (const handler of this.notificationHandlers) {
      handler(notification);
    }
  }
}

describe("ActiveLoopOrchestrator", () => {
  it("runs Worker -> Reviewer -> Worker DONE under synthetic read-only params", async () => {
    const root = path.join(process.cwd(), "data", "tmp", `orchestrator-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });

    const client = new FakeLoopClient();
    const stores = {
      jobs: createFileJobStore(path.join(root, "jobs")),
      events: createFileEventStore(path.join(root, "events")),
      receipts: createFileReceiptStore(path.join(root, "receipts")),
    };
    const orchestrator = createActiveLoopOrchestrator({
      client,
      stores,
      plan: { jobId: "job-cea-006", syntheticWorkspaceRoot },
      now: () => new Date("2026-07-07T00:00:00.000Z"),
    });

    const result = await orchestrator.runWorkerReviewerLoop();

    expect(result.finalState).toBe("DONE");
    expect(result.workerNeedReviewer.type).toBe("NEED_REVIEWER");
    expect(result.reviewerDecision.type).toBe("REVIEWER_DECISION");
    expect(result.workerDone.type).toBe("DONE");
    expect(client.threadStarts).toHaveLength(2);
    expect(client.turnStarts).toHaveLength(3);
    expect(client.turnStarts.every((params) => params.cwd === syntheticWorkspaceRoot)).toBe(true);
    expect(client.turnStarts.every((params) => params.sandboxPolicy?.type === "readOnly")).toBe(true);

    const events = await stores.events.read("job-cea-006");
    expect(events.some((event) => event.state === "DONE")).toBe(true);
    await expect(stores.jobs.get("job-cea-006")).resolves.toMatchObject({ state: "DONE" });
  });

  it("rejects malformed structured output", () => {
    expect(() => parseStructuredTurnOutput(makeTurn("{ nope"), "NEED_REVIEWER")).toThrow("malformed structured output");
    expect(() => parseStructuredTurnOutput(makeTurn(JSON.stringify({ type: "DONE", summary: "early", evidence: [] })), "NEED_REVIEWER")).toThrow("invalid structured output");
  });

  it("waits for turn completion before parsing structured output", async () => {
    const root = path.join(process.cwd(), "data", "tmp", `orchestrator-wait-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });

    const client = new FakeLoopClient();
    client.completeTurnsInStart = false;
    const completedOutputs = [...client.outputs];
    const waitedTurnIds: string[] = [];
    const stores = {
      jobs: createFileJobStore(path.join(root, "jobs")),
      events: createFileEventStore(path.join(root, "events")),
      receipts: createFileReceiptStore(path.join(root, "receipts")),
    };
    const orchestrator = createActiveLoopOrchestrator({
      client,
      stores,
      plan: { jobId: "job-cea-006-wait", syntheticWorkspaceRoot },
      now: () => new Date("2026-07-07T00:00:00.000Z"),
      waitForTurnCompletion: async (turn) => {
        waitedTurnIds.push(turn.id);
        return makeTurn(JSON.stringify(completedOutputs.shift()), { id: turn.id });
      },
    });

    const result = await orchestrator.runWorkerReviewerLoop();

    expect(result.finalState).toBe("DONE");
    expect(waitedTurnIds).toEqual(client.startedTurns.map((turn) => turn.id));
    expect(waitedTurnIds).toHaveLength(3);
  });

  it("uses App Server turn/completed notifications when no explicit waiter is supplied", async () => {
    const root = path.join(process.cwd(), "data", "tmp", `orchestrator-notify-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });

    const client = new FakeLoopClient();
    client.completeTurnsInStart = false;
    client.notifyCompletedTurns = true;
    const stores = {
      jobs: createFileJobStore(path.join(root, "jobs")),
      events: createFileEventStore(path.join(root, "events")),
      receipts: createFileReceiptStore(path.join(root, "receipts")),
    };
    const orchestrator = createActiveLoopOrchestrator({
      client,
      stores,
      plan: { jobId: "job-cea-006-notify", syntheticWorkspaceRoot },
      now: () => new Date("2026-07-07T00:00:00.000Z"),
      turnCompletionTimeoutMs: 1_000,
    });

    const result = await orchestrator.runWorkerReviewerLoop();

    expect(result.finalState).toBe("DONE");
    expect(client.notificationHandlers.size).toBe(1);
    expect(client.startedTurns).toHaveLength(3);
  });

  it("rejects interrupted initial turns without waiting for completion timeout", async () => {
    const root = path.join(process.cwd(), "data", "tmp", `orchestrator-interrupted-${Date.now()}`);
    await rm(root, { force: true, recursive: true });
    await mkdir(root, { recursive: true });

    const client = new FakeLoopClient();
    client.completeTurnsInStart = false;
    client.initialTurnStatus = "interrupted";
    const stores = {
      jobs: createFileJobStore(path.join(root, "jobs")),
      events: createFileEventStore(path.join(root, "events")),
      receipts: createFileReceiptStore(path.join(root, "receipts")),
    };
    const orchestrator = createActiveLoopOrchestrator({
      client,
      stores,
      plan: { jobId: "job-cea-006-interrupted", syntheticWorkspaceRoot },
      now: () => new Date("2026-07-07T00:00:00.000Z"),
      turnCompletionTimeoutMs: 60_000,
    });

    await expect(orchestrator.runWorkerReviewerLoop()).rejects.toThrow("status=interrupted");
    expect(client.startedTurns).toHaveLength(1);
  });
});

function makeTurn(text: string, options: { readonly id?: string; readonly status?: string } = {}): Turn {
  return {
    id: options.id ?? `turn-${Math.random().toString(16).slice(2)}`,
    items: text.length > 0 ? [{ type: "agentMessage", id: "item-1", text, phase: null, memoryCitation: null }] : [],
    itemsView: { type: "all" },
    status: options.status ?? "completed",
    error: null,
    startedAt: null,
    completedAt: null,
    durationMs: null,
  } as unknown as Turn;
}
