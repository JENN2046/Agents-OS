export type SnapshotReviewPackageKind = "manifest" | "report" | "receipt";

export interface SnapshotReviewPackageArtifact {
  readonly taskId: "CEA-018" | "CEA-019" | "CEA-020";
  readonly kind: SnapshotReviewPackageKind;
  readonly label: string;
  readonly sourcePath: string;
  readonly entryPath: string;
}

export interface SnapshotReviewPackagePlan {
  readonly packageVersion: 1;
  readonly sourceTasks: readonly ["CEA-018", "CEA-019", "CEA-020"];
  readonly contentPolicy: {
    readonly allowedKinds: readonly SnapshotReviewPackageKind[];
    readonly excludesRawEvents: true;
    readonly excludesPromptPackets: true;
    readonly excludesPromptAnnexes: true;
    readonly excludesWorkerPlans: true;
    readonly excludesSnapshotSourceFiles: true;
  };
  readonly artifacts: readonly SnapshotReviewPackageArtifact[];
  readonly excludedReferencedArtifactLabels: readonly string[];
}

const allowedPackageKinds = ["manifest", "report", "receipt"] as const satisfies readonly SnapshotReviewPackageKind[];
const forbiddenEntryTerms = [
  ".git",
  ".env",
  "config.env",
  "node_modules",
  "dist",
  "state-private",
  "secret",
  "secrets",
  "token",
  "tokens",
  "cookie",
  "cookies",
  "events",
  "context-ledger",
  "context-packets",
  "context-approvals",
  "prompt-annexes",
  "worker-pilots",
  "snapshots/",
] as const;

export function createSnapshotReviewPackagePlan(input: {
  readonly cea018Report: unknown;
  readonly cea019Report: unknown;
  readonly cea020Report: unknown;
}): SnapshotReviewPackagePlan {
  const cea018 = assertReport(input.cea018Report, "CEA-018");
  const cea019 = assertReport(input.cea019Report, "CEA-019");
  const cea020 = assertReport(input.cea020Report, "CEA-020");
  const cea018Artifacts = artifactsOf(cea018);
  const cea019Artifacts = artifactsOf(cea019);
  const cea020Artifacts = artifactsOf(cea020);

  const artifacts: SnapshotReviewPackageArtifact[] = [
    artifact("CEA-018", "manifest", "snapshot_manifest", requiredString(cea018Artifacts.snapshot_manifest, "CEA-018 snapshot manifest"), "cea-018/manifest/snapshot-manifest.json"),
    artifact("CEA-018", "report", "snapshot_exclusions", requiredString(cea018Artifacts.snapshot_exclusions, "CEA-018 snapshot exclusions"), "cea-018/report/snapshot-exclusions.json"),
    artifact("CEA-018", "report", "cea018_report", requiredString(cea018Artifacts.report, "CEA-018 report"), "cea-018/report/cea-018_e2e_safe_review_loop.json"),
    artifact("CEA-018", "receipt", "cea018_receipt", requiredString(cea018Artifacts.receipt, "CEA-018 receipt"), "cea-018/receipt/2026-07-07-cea-018-e2e-safe-review-loop.receipt.md"),
    artifact("CEA-019", "report", "cea019_report", requiredString(cea019Artifacts.report, "CEA-019 report"), "cea-019/report/cea-019_e2e_evidence_verification_gate.json"),
    artifact("CEA-019", "receipt", "cea019_receipt", requiredString(cea019Artifacts.receipt, "CEA-019 receipt"), "cea-019/receipt/2026-07-07-cea-019-e2e-evidence-verification-gate.receipt.md"),
    artifact("CEA-020", "report", "cea020_report", requiredString(cea020Artifacts.report, "CEA-020 report"), "cea-020/report/cea-020_phase8_schema_gate.json"),
    artifact("CEA-020", "receipt", "cea020_receipt", requiredString(cea020Artifacts.receipt, "CEA-020 receipt"), "cea-020/receipt/2026-07-07-cea-020-phase8-schema-gate.receipt.md"),
  ];
  validateSnapshotReviewPackageArtifacts(artifacts);

  return {
    packageVersion: 1,
    sourceTasks: ["CEA-018", "CEA-019", "CEA-020"],
    contentPolicy: {
      allowedKinds: allowedPackageKinds,
      excludesRawEvents: true,
      excludesPromptPackets: true,
      excludesPromptAnnexes: true,
      excludesWorkerPlans: true,
      excludesSnapshotSourceFiles: true,
    },
    artifacts,
    excludedReferencedArtifactLabels: [
      "cea018.events",
      "cea018.ledger",
      "cea018.packet",
      "cea018.approval",
      "cea018.annex",
      "cea018.plan",
      "cea018.snapshot_source_files",
      "cea019.cea018_events",
      "cea020.schema_source_contents",
    ],
  };
}

export function validateSnapshotReviewPackageArtifacts(artifacts: readonly SnapshotReviewPackageArtifact[]): void {
  const seen = new Set<string>();
  for (const item of artifacts) {
    if (!allowedPackageKinds.includes(item.kind)) {
      throw new Error(`review package artifact kind is not allowed: ${item.kind}`);
    }
    if (item.entryPath.includes("\\") || item.entryPath.startsWith("/") || item.entryPath.startsWith("../") || item.entryPath.includes("/../")) {
      throw new Error(`review package entry path is unsafe: ${item.entryPath}`);
    }
    if (!entryPathMatchesKind(item.entryPath, item.kind)) {
      throw new Error(`review package entry kind mismatch: ${item.entryPath}`);
    }
    const lower = item.entryPath.toLowerCase();
    const forbidden = forbiddenEntryTerms.find((term) => lower.includes(term));
    if (forbidden) {
      throw new Error(`review package entry contains forbidden term ${forbidden}: ${item.entryPath}`);
    }
    if (seen.has(item.entryPath)) {
      throw new Error(`duplicate review package entry: ${item.entryPath}`);
    }
    seen.add(item.entryPath);
  }
}

export function isAllowedSnapshotReviewPackageEntry(entryPath: string): boolean {
  if (entryPath === "MANIFEST.json") return true;
  const lower = entryPath.toLowerCase().replaceAll("\\", "/");
  if (forbiddenEntryTerms.some((term) => lower.includes(term))) return false;
  return lower.includes("/manifest/") || lower.includes("/report/") || lower.includes("/receipt/");
}

function artifact(
  taskId: SnapshotReviewPackageArtifact["taskId"],
  kind: SnapshotReviewPackageKind,
  label: string,
  sourcePath: string,
  entryPath: string,
): SnapshotReviewPackageArtifact {
  return { taskId, kind, label, sourcePath, entryPath };
}

function assertReport(value: unknown, taskId: SnapshotReviewPackageArtifact["taskId"]): Record<string, unknown> {
  if (!isRecord(value) || value.task_id !== taskId) {
    throw new Error(`expected ${taskId} report`);
  }
  return value;
}

function artifactsOf(report: Record<string, unknown>): Record<string, unknown> {
  if (!isRecord(report.artifacts)) {
    throw new Error(`${String(report.task_id)} report is missing artifacts`);
  }
  return report.artifacts;
}

function requiredString(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0 || value.includes("\0")) {
    throw new Error(`${label} path is missing or invalid`);
  }
  return value;
}

function entryPathMatchesKind(entryPath: string, kind: SnapshotReviewPackageKind): boolean {
  return entryPath.includes(`/${kind}/`);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
