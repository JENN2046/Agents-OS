export type ReadinessStatus = "AVAILABLE" | "PARTIAL" | "MISSING";
export type Phase8DirectRepoStatus = "BLOCKED_BY_SCHEMA" | "REVIEW_REQUIRED";

export interface CommanderEvidenceItem {
  readonly taskId: string;
  readonly title: string;
  readonly result: string;
  readonly reportPath: string;
  readonly receiptPath: string;
  readonly receiptExists: boolean;
  readonly gateStatus?: string;
  readonly phase8Decision?: string;
  readonly readableRootSupported?: boolean;
}

export interface CommanderReadinessRow {
  readonly taskId: string;
  readonly title: string;
  readonly capability: string;
  readonly status: ReadinessStatus;
  readonly evidenceReports: readonly string[];
  readonly evidenceReceipts: readonly string[];
  readonly notes: readonly string[];
}

export interface CommanderReadinessMatrix {
  readonly matrixVersion: 1;
  readonly rows: readonly CommanderReadinessRow[];
  readonly summary: {
    readonly safeSnapshotReviewLane: "READY" | "PARTIAL";
    readonly commanderReviewPackage: "READY" | "PARTIAL";
    readonly phase8DirectRealRepo: Phase8DirectRepoStatus;
    readonly availableRows: number;
    readonly partialRows: number;
    readonly missingRows: number;
  };
  readonly phase8UnlockConditions: readonly string[];
  readonly blockingItems: readonly string[];
}

interface ExpectedReadinessRow {
  readonly taskId: string;
  readonly title: string;
  readonly capability: string;
  readonly requiredEvidenceTaskIds: readonly string[];
  readonly notes: readonly string[];
}

const expectedRows = [
  {
    taskId: "CEA-011",
    title: "Safe Repo Snapshot Pilot",
    capability: "Bridge-owned safe snapshot exporter with allowlist, exclusions, manifest, and exclusion report.",
    requiredEvidenceTaskIds: ["CEA-011"],
    notes: ["Real repository is read only by Bridge exporter; managed sessions use snapshots."],
  },
  {
    taskId: "CEA-012",
    title: "Codex Context Ledger Pilot",
    capability: "Metadata-only context ledger for task and evidence references.",
    requiredEvidenceTaskIds: ["CEA-012"],
    notes: ["No raw private state is required for ledger promotion."],
  },
  {
    taskId: "CEA-013",
    title: "Context Promotion Gate",
    capability: "Promotion gate blocks unapproved or unsafe context packets.",
    requiredEvidenceTaskIds: ["CEA-013"],
    notes: ["Promotion remains gated before prompt use."],
  },
  {
    taskId: "CEA-014",
    title: "Promotion Approval Receipt",
    capability: "Reviewer or Commander approval receipt bound to source packet hash.",
    requiredEvidenceTaskIds: ["CEA-014"],
    notes: ["Approval receipt is auditable and separate from packet generation."],
  },
  {
    taskId: "CEA-015",
    title: "Prompt Packet Compiler",
    capability: "Packet-only prompt annex compiler with approval verification.",
    requiredEvidenceTaskIds: ["CEA-015"],
    notes: ["Prompt annex excludes raw private state and disables auto-injection."],
  },
  {
    taskId: "CEA-016",
    title: "Snapshot-Bound Worker Prep and Live Run",
    capability: "Worker plan plus live managed Worker run constrained to snapshot cwd.",
    requiredEvidenceTaskIds: ["CEA-016", "CEA-016-LIVE"],
    notes: ["Worker cwd remains snapshot-only; direct real repository remains blocked."],
  },
  {
    taskId: "CEA-017",
    title: "Snapshot-Bound Reviewer Pilot",
    capability: "Reviewer consumes Worker DONE evidence from the same snapshot boundary.",
    requiredEvidenceTaskIds: ["CEA-017"],
    notes: ["Reviewer cwd remains snapshot-only."],
  },
  {
    taskId: "CEA-018",
    title: "End-to-End Safe Review Loop",
    capability: "Single command chains snapshot export through Worker, Reviewer, report, and receipt.",
    requiredEvidenceTaskIds: ["CEA-018"],
    notes: ["E2E live path is available for snapshot-bound review."],
  },
  {
    taskId: "CEA-019",
    title: "E2E Evidence Verification Gate",
    capability: "Offline gate verifies CEA-018 evidence without starting new managed sessions.",
    requiredEvidenceTaskIds: ["CEA-019"],
    notes: ["Evidence verification is repeatable and does not require live Worker/Reviewer."],
  },
  {
    taskId: "CEA-020",
    title: "Phase 8 Schema Gate",
    capability: "Offline watcher for readableRoots or equivalent restricted readable-root schema support.",
    requiredEvidenceTaskIds: ["CEA-020"],
    notes: ["Gate is available; current direct real repository Phase 8 remains blocked if readable roots are absent."],
  },
  {
    taskId: "CEA-021",
    title: "Snapshot Review Package Publisher",
    capability: "Compact Commander/external review package containing only manifest, report, and receipt evidence.",
    requiredEvidenceTaskIds: ["CEA-021"],
    notes: ["Review package excludes events, annexes, plans, ledgers, prompt packets, and snapshot source files."],
  },
] as const satisfies readonly ExpectedReadinessRow[];

export function createCommanderReadinessMatrix(evidence: readonly CommanderEvidenceItem[]): CommanderReadinessMatrix {
  const byTask = new Map(evidence.map((item) => [item.taskId, item]));
  const rows = expectedRows.map((row) => buildRow(row, byTask));
  const availableRows = rows.filter((row) => row.status === "AVAILABLE").length;
  const partialRows = rows.filter((row) => row.status === "PARTIAL").length;
  const missingRows = rows.filter((row) => row.status === "MISSING").length;
  const safeTaskIds = new Set(["CEA-011", "CEA-012", "CEA-013", "CEA-014", "CEA-015", "CEA-016", "CEA-017", "CEA-018", "CEA-019"]);
  const safeSnapshotReviewLane = rows.filter((row) => safeTaskIds.has(row.taskId)).every((row) => row.status === "AVAILABLE")
    ? "READY"
    : "PARTIAL";
  const commanderReviewPackage = rows.find((row) => row.taskId === "CEA-021")?.status === "AVAILABLE" ? "READY" : "PARTIAL";
  const schemaGate = byTask.get("CEA-020");
  const phase8DirectRealRepo: Phase8DirectRepoStatus = schemaGate?.readableRootSupported === true ? "REVIEW_REQUIRED" : "BLOCKED_BY_SCHEMA";

  return {
    matrixVersion: 1,
    rows,
    summary: {
      safeSnapshotReviewLane,
      commanderReviewPackage,
      phase8DirectRealRepo,
      availableRows,
      partialRows,
      missingRows,
    },
    phase8UnlockConditions: [
      "App Server generated schema exposes readableRoots or an equivalent restricted readable-root field for managed session reads.",
      "CEA-020 returns UNLOCK_CANDIDATE / REVIEW_REQUIRED instead of BLOCK.",
      "Human semantic review confirms the field constrains readable roots and is not merely cwd, readOnly, sandboxPolicy, writableRoots, or a write-only boundary.",
      "A new explicit Phase 8 authorization package names the target root, readable roots, denylist, evidence location, and stop conditions.",
      "A dry-run/preflight confirms no secrets, state-private, .git, node_modules, dist, or denied paths are readable by managed sessions.",
    ],
    blockingItems:
      phase8DirectRealRepo === "BLOCKED_BY_SCHEMA"
        ? ["Phase 8 direct real repository managed-session pilot remains blocked because restricted readable roots are absent."]
        : ["Phase 8 is not automatically unlocked; human review and fresh authorization are still required."],
  };
}

function buildRow(row: ExpectedReadinessRow, byTask: ReadonlyMap<string, CommanderEvidenceItem>): CommanderReadinessRow {
  const items = row.requiredEvidenceTaskIds.map((taskId) => byTask.get(taskId));
  const presentItems = items.filter((item): item is CommanderEvidenceItem => Boolean(item));
  const evidenceReports = presentItems.map((item) => item.reportPath);
  const evidenceReceipts = presentItems.map((item) => item.receiptPath);
  const allPresent = presentItems.length === row.requiredEvidenceTaskIds.length;
  const allPass = presentItems.every((item) => isPassLike(item.result));
  const allReceipts = presentItems.every((item) => item.receiptExists);
  const status: ReadinessStatus = !allPresent ? "MISSING" : allPass && allReceipts ? "AVAILABLE" : "PARTIAL";
  const notes = [...row.notes];
  if (!allPresent) {
    notes.push(`Missing evidence for: ${row.requiredEvidenceTaskIds.filter((taskId) => !byTask.has(taskId)).join(", ")}`);
  }
  if (presentItems.some((item) => !item.receiptExists)) {
    notes.push("One or more receipts are missing.");
  }
  if (row.taskId === "CEA-020") {
    const gate = byTask.get("CEA-020");
    notes.push(`Phase 8 gate status: ${gate?.gateStatus ?? "UNKNOWN"}; decision: ${gate?.phase8Decision ?? "UNKNOWN"}.`);
  }
  return {
    taskId: row.taskId,
    title: row.title,
    capability: row.capability,
    status,
    evidenceReports,
    evidenceReceipts,
    notes,
  };
}

function isPassLike(result: string): boolean {
  return result === "PASS" || result.startsWith("PASS_");
}
