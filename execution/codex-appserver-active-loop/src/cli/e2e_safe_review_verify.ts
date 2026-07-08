import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { assertAllowedArtifactFilename, assertProjectArtifactPathBoundary } from "../bridge/artifact_path_boundary.js";
import { verifyE2eSafeReviewEvidence } from "../bridge/e2e_safe_review_verify.js";
import { safeJoin } from "../stores/safe_path.js";

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const completedAt = new Date().toISOString();
  const timestamp = completedAt.replace(/[-:.TZ]/g, "").slice(0, 14);
  const jobId = `cea-019-e2e-evidence-verification-${timestamp}`;
  const cea018ReportPath = path.join(projectRoot, "data", "reports", "cea-018_e2e_safe_review_loop.json");
  const reportPath = path.join(projectRoot, "data", "reports", "cea-019_e2e_evidence_verification_gate.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", "2026-07-07-cea-019-e2e-evidence-verification-gate.receipt.md");

  const cea018Report = (await readJson(cea018ReportPath)) as Record<string, unknown>;
  const artifacts = isRecord(cea018Report.artifacts) ? cea018Report.artifacts : {};
  const verifiedArtifacts = Object.fromEntries(
    Object.entries(artifacts).map(([name, value]) => [name, resolveCea018ArtifactPath(projectRoot, name, value)]),
  );
  const artifactExists = Object.fromEntries(
    Object.entries(verifiedArtifacts).map(([name, value]) => [name, typeof value === "string" && existsSync(value)]),
  );

  const manifestPath = verifiedArtifacts.snapshot_manifest ?? "";
  const exclusionPath = verifiedArtifacts.snapshot_exclusions ?? "";
  const eventsPath = verifiedArtifacts.events ?? "";
  const manifest = manifestPath ? ((await readJson(manifestPath)) as Record<string, unknown>) : {};
  const exclusions = exclusionPath ? ((await readJson(exclusionPath)) as Record<string, unknown>) : {};
  const events = eventsPath ? await readJsonl(eventsPath) : [];

  const includedPaths = extractRelativePaths(manifest.includedFiles);
  const excludedPaths = extractRelativePaths(isRecord(exclusions) ? exclusions.excludedFiles : undefined);
  const eventMethodCounts = countBy(
    events
      .map((event) => (isRecord(event.payload) && typeof event.payload.method === "string" ? event.payload.method : ""))
      .filter((method) => method.length > 0),
  );
  const eventTypeCounts = countBy(events.map((event) => event.type).filter((type): type is string => typeof type === "string"));
  const stderrErrorCount = events.filter((event) => isRecord(event.payload) && event.payload.method === "stderr" && event.payload.hasError === true).length;

  const verification = verifyE2eSafeReviewEvidence({
    report: cea018Report,
    artifactExists,
    includedPaths,
    excludedPaths,
    eventMethodCounts,
    eventTypeCounts,
    stderrErrorCount,
  });

  const output = {
    task_id: "CEA-019",
    title: "E2E Evidence Verification Gate",
    result: verification.result,
    completed_at: completedAt,
    job_id: jobId,
    verifies_task_id: "CEA-018",
    verifies_job_id: typeof cea018Report.job_id === "string" ? cea018Report.job_id : null,
    cea018_report: cea018ReportPath,
    checks: verification.checks,
    failures: verification.failures,
    counts: verification.counts,
    artifacts: {
      cea018_report: cea018ReportPath,
      cea018_receipt: verifiedArtifacts.receipt ?? null,
      cea018_events: eventsPath || null,
      cea018_snapshot_manifest: manifestPath || null,
      cea018_snapshot_exclusions: exclusionPath || null,
      report: reportPath,
      receipt: receiptPath,
    },
    boundary: {
      phase8_direct_real_repo: "BLOCKED",
      live_sessions_started_by_this_gate: false,
      verifier_mode: "OFFLINE_EVIDENCE_ONLY",
    },
  };

  await writeJson(reportPath, output);
  await writeReceipt(receiptPath, output);
  console.log(JSON.stringify(output, null, 2));
  if (verification.result !== "PASS") {
    process.exitCode = 1;
  }
}

async function readJson(filePath: string): Promise<unknown> {
  return JSON.parse(await readFile(filePath, "utf8")) as unknown;
}

async function readJsonl(filePath: string): Promise<readonly Record<string, unknown>[]> {
  const text = await readFile(filePath, "utf8");
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
}

function extractRelativePaths(value: unknown): readonly string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((entry) => (isRecord(entry) && typeof entry.relativePath === "string" ? entry.relativePath : ""))
    .filter((relativePath) => relativePath.length > 0);
}

function countBy(values: readonly string[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const value of values) {
    counts[value] = (counts[value] ?? 0) + 1;
  }
  return counts;
}

function resolveCea018ArtifactPath(projectRoot: string, name: string, value: unknown): string | null {
  if (typeof value !== "string") return null;
  try {
    const allowedRoot = cea018ArtifactRoot(name);
    if (!allowedRoot) return null;
    const artifactPath = assertProjectArtifactPathBoundary(projectRoot, value, allowedRoot, `CEA-018 ${name}`);
    assertCea018ArtifactFilename(name, artifactPath);
    return artifactPath;
  } catch {
    return null;
  }
}

function cea018ArtifactRoot(name: string): string | null {
  switch (name) {
    case "snapshot_manifest":
    case "snapshot_exclusions":
      return "data/snapshots";
    case "events":
      return "data/events";
    case "ledger":
      return "data/context-ledger";
    case "packet":
      return "data/context-packets";
    case "approval":
      return "data/context-approvals";
    case "annex":
      return "data/prompt-annexes";
    case "plan":
      return "data/worker-pilots";
    case "report":
      return "data/reports";
    case "receipt":
      return "data/receipts";
    default:
      return null;
  }
}

function assertCea018ArtifactFilename(name: string, artifactPath: string): void {
  if (name === "snapshot_manifest") {
    assertAllowedArtifactFilename(artifactPath, ["manifest.json"], "CEA-018 snapshot_manifest");
    return;
  }
  if (name === "snapshot_exclusions") {
    assertAllowedArtifactFilename(artifactPath, ["exclusions.json"], "CEA-018 snapshot_exclusions");
    return;
  }
  if (name === "report") {
    assertAllowedArtifactFilename(artifactPath, ["cea-018_e2e_safe_review_loop.json"], "CEA-018 report");
    return;
  }
  if (name === "receipt") {
    assertAllowedArtifactFilename(artifactPath, ["2026-07-07-cea-018-e2e-safe-review-loop.receipt.md"], "CEA-018 receipt");
    return;
  }
  const basename = path.basename(artifactPath);
  const expectedSuffixByName: Record<string, string> = {
    events: ".events.jsonl",
    ledger: ".context.jsonl",
    packet: ".context-packet.json",
    approval: ".approval.json",
    annex: ".prompt-annex.json",
    plan: ".worker-plan.json",
  };
  const expectedSuffix = expectedSuffixByName[name];
  if (!expectedSuffix || !basename.endsWith(expectedSuffix)) {
    throw new Error(`CEA-018 ${name} filename is not allowed: ${basename}`);
  }
}

async function writeJson(filePath: string, value: unknown): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function writeReceipt(
  filePath: string,
  report: {
    readonly result: string;
    readonly job_id: string;
    readonly verifies_job_id: string | null;
    readonly failures: readonly string[];
    readonly artifacts: { readonly report: string; readonly receipt: string; readonly cea018_report: string };
    readonly boundary: { readonly phase8_direct_real_repo: string; readonly verifier_mode: string };
  },
): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const lines = [
    "# CEA-019 E2E Evidence Verification Gate Receipt",
    "",
    `result: ${report.result}`,
    `job_id: ${report.job_id}`,
    `verifies_job_id: ${report.verifies_job_id ?? "UNKNOWN"}`,
    "",
    "## Boundary",
    `- verifier_mode: ${report.boundary.verifier_mode}`,
    `- phase8_direct_real_repo: ${report.boundary.phase8_direct_real_repo}`,
    `- live_sessions_started_by_this_gate: false`,
    "",
    "## Failures",
    ...(report.failures.length === 0 ? ["- NONE"] : report.failures.map((failure) => `- ${failure}`)),
    "",
    "## Artifacts",
    `- cea018_report: ${report.artifacts.cea018_report}`,
    `- report: ${report.artifacts.report}`,
    `- receipt: ${report.artifacts.receipt}`,
    "",
  ];
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, lines.join("\n"), "utf8");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

void main();
