import { lstatSync, realpathSync } from "node:fs";
import path from "node:path";
import { assertWorkerCwdIsSnapshot, type SnapshotManifest } from "./repo_snapshot.js";
import { assertPromptAnnex, type PromptAnnex } from "./prompt_annex.js";

export interface SnapshotBoundWorkerPlan {
  readonly planVersion: 1;
  readonly planId: string;
  readonly createdAt: string;
  readonly mode: "PREP_ONLY";
  readonly snapshotId: string;
  readonly snapshotRoot: string;
  readonly manifestPath: string;
  readonly workerCwd: string;
  readonly annexId: string;
  readonly annexRef: string;
  readonly sandboxPolicy: {
    readonly type: "readOnly";
    readonly networkAccess: false;
  };
  readonly turnPreview: {
    readonly cwd: string;
    readonly usesAnnex: true;
    readonly outputSchema: "WORKER_DONE_OR_NEED_REVIEWER";
    readonly artifactRefs: readonly string[];
    readonly snapshotIds: readonly string[];
  };
  readonly validation: {
    readonly snapshotManifestBoundary: "PASS";
    readonly annexApprovalVerified: "PASS";
    readonly annexSnapshotMatchesManifest: "PASS";
    readonly workerCwdIsSnapshotRoot: "PASS";
  };
  readonly boundary: {
    readonly managedWorkerStarted: false;
    readonly managedReviewerStarted: false;
    readonly directRealRepo: "BLOCKED";
    readonly workerCwdPolicy: "SNAPSHOT_ONLY";
    readonly autoInjection: "DISABLED";
    readonly rawContentIncluded: false;
  };
}

export interface CreateSnapshotBoundWorkerPlanInput {
  readonly planId: string;
  readonly manifest: SnapshotManifest;
  readonly manifestPath: string;
  readonly annex: PromptAnnex;
  readonly annexRef: string;
  readonly createdAt?: string;
}

const allowedPlanKeys = [
  "planVersion",
  "planId",
  "createdAt",
  "mode",
  "snapshotId",
  "snapshotRoot",
  "manifestPath",
  "workerCwd",
  "annexId",
  "annexRef",
  "sandboxPolicy",
  "turnPreview",
  "validation",
  "boundary",
] as const;

const rawContentFieldNames = new Set(["content", "raw", "rawContent", "message", "messages", "prompt", "response", "text"]);

export function createSnapshotBoundWorkerPlan(input: CreateSnapshotBoundWorkerPlanInput): SnapshotBoundWorkerPlan {
  assertSafePlanId(input.planId, "planId");
  assertPromptAnnex(input.annex);
  assertSnapshotManifest(input.manifest);
  assertWorkerCwdIsSnapshot(input.manifest.workerCwd, input.manifest.snapshotRoot);

  const snapshotId = path.basename(input.manifest.snapshotRoot);
  if (!input.annex.snapshotIds.includes(snapshotId)) {
    throw new Error("Worker plan annex snapshot id must match the snapshot manifest root");
  }
  if (input.annex.boundary.managedSessionStarted !== false || input.annex.boundary.directRealRepo !== "BLOCKED") {
    throw new Error("Worker plan requires dry-run annex with direct real repo blocked");
  }

  const plan: SnapshotBoundWorkerPlan = {
    planVersion: 1,
    planId: input.planId,
    createdAt: input.createdAt ?? new Date().toISOString(),
    mode: "PREP_ONLY",
    snapshotId,
    snapshotRoot: input.manifest.snapshotRoot,
    manifestPath: input.manifestPath,
    workerCwd: input.manifest.snapshotRoot,
    annexId: input.annex.annexId,
    annexRef: input.annexRef,
    sandboxPolicy: { type: "readOnly", networkAccess: false },
    turnPreview: {
      cwd: input.manifest.snapshotRoot,
      usesAnnex: true,
      outputSchema: "WORKER_DONE_OR_NEED_REVIEWER",
      artifactRefs: [...input.annex.artifactRefs],
      snapshotIds: [...input.annex.snapshotIds],
    },
    validation: {
      snapshotManifestBoundary: "PASS",
      annexApprovalVerified: "PASS",
      annexSnapshotMatchesManifest: "PASS",
      workerCwdIsSnapshotRoot: "PASS",
    },
    boundary: {
      managedWorkerStarted: false,
      managedReviewerStarted: false,
      directRealRepo: "BLOCKED",
      workerCwdPolicy: "SNAPSHOT_ONLY",
      autoInjection: "DISABLED",
      rawContentIncluded: false,
    },
  };
  assertSnapshotBoundWorkerPlan(plan);
  return plan;
}

export function validateSnapshotBoundWorkerPlan(value: unknown): value is SnapshotBoundWorkerPlan {
  if (!isRecord(value) || containsRawContentField(value) || !hasOnlyKeys(value, allowedPlanKeys)) {
    return false;
  }
  return (
    value.planVersion === 1 &&
    isSafePlanId(value.planId) &&
    isIsoTimestamp(value.createdAt) &&
    value.mode === "PREP_ONLY" &&
    isSafePlanId(value.snapshotId) &&
    isSafeString(value.snapshotRoot) &&
    isSafeString(value.manifestPath) &&
    value.workerCwd === value.snapshotRoot &&
    isSafePlanId(value.annexId) &&
    isSafeString(value.annexRef) &&
    isSandboxPolicy(value.sandboxPolicy) &&
    isTurnPreview(value.turnPreview) &&
    isValidation(value.validation) &&
    isBoundary(value.boundary)
  );
}

export function assertSnapshotBoundWorkerPlan(value: unknown): asserts value is SnapshotBoundWorkerPlan {
  if (!validateSnapshotBoundWorkerPlan(value)) {
    throw new Error("snapshot-bound Worker plan must be prep-only and snapshot-only");
  }
}

export function assertSnapshotBoundWorkerPlanPathBoundary(projectRoot: string, plan: SnapshotBoundWorkerPlan): void {
  assertSnapshotBoundWorkerPlan(plan);
  const snapshotsRoot = path.resolve(projectRoot, "data", "snapshots");
  const snapshotRoot = path.resolve(plan.snapshotRoot);
  const workerCwd = path.resolve(plan.workerCwd);
  const expectedManifestPath = path.join(snapshotRoot, "_snapshot", "manifest.json");
  if (!isPathInsideRoot(snapshotsRoot, snapshotRoot)) {
    throw new Error("live snapshot root must stay under project data/snapshots");
  }
  if (workerCwd !== snapshotRoot) {
    throw new Error("live Worker cwd must match the snapshot root");
  }
  if (path.resolve(plan.manifestPath) !== expectedManifestPath) {
    throw new Error("live Worker manifest path must match the snapshot root manifest");
  }
  if (plan.snapshotId !== path.basename(snapshotRoot)) {
    throw new Error("live Worker snapshot id must match the snapshot root");
  }

  assertNoSymlinkInExistingPath(snapshotsRoot);
  assertNoSymlinkInExistingPath(snapshotRoot);
  assertNoSymlinkInExistingPath(plan.manifestPath);
  const realSnapshotsRoot = realpathSync(snapshotsRoot);
  const realSnapshotRoot = realpathSync(snapshotRoot);
  const realWorkerCwd = realpathSync(workerCwd);
  const realManifestPath = realpathSync(plan.manifestPath);
  if (!isPathInsideRoot(realSnapshotsRoot, realSnapshotRoot)) {
    throw new Error("live snapshot root must stay under project data/snapshots");
  }
  if (realWorkerCwd !== realSnapshotRoot) {
    throw new Error("live Worker cwd must match the snapshot root");
  }
  if (realManifestPath !== path.join(realSnapshotRoot, "_snapshot", "manifest.json")) {
    throw new Error("live Worker manifest path must match the snapshot root manifest");
  }
}

export function assertSnapshotBoundWorkerPlanLiveBoundary(
  projectRoot: string,
  plan: SnapshotBoundWorkerPlan,
  manifest: SnapshotManifest,
): void {
  assertSnapshotBoundWorkerPlanPathBoundary(projectRoot, plan);
  assertSnapshotManifest(manifest);
  const snapshotRoot = path.resolve(plan.snapshotRoot);
  const realSnapshotRoot = realpathSync(snapshotRoot);
  const realManifestSnapshotRoot = realpathSync(manifest.snapshotRoot);
  const realManifestWorkerCwd = realpathSync(manifest.workerCwd);
  if (realManifestSnapshotRoot !== realSnapshotRoot || realManifestWorkerCwd !== realSnapshotRoot) {
    throw new Error("live Worker manifest must match the plan snapshot root");
  }
  if (path.basename(manifest.snapshotRoot) !== plan.snapshotId) {
    throw new Error("live Worker manifest snapshot id must match the plan");
  }
}

function assertSnapshotManifest(value: SnapshotManifest): void {
  if (
    value.snapshotVersion !== 1 ||
    value.boundary.bridgeExporterReadSource !== true ||
    value.boundary.managedSessionsReadSource !== false ||
    value.boundary.workerCwdSnapshotOnly !== true ||
    value.boundary.phase8DirectRealRepo !== "BLOCKED" ||
    value.workerCwd !== value.snapshotRoot
  ) {
    throw new Error("snapshot manifest boundary is not valid for Worker pilot prep");
  }
}

function isPathInsideRoot(root: string, candidate: string): boolean {
  const relative = path.relative(path.resolve(root), path.resolve(candidate));
  return relative !== "" && !relative.startsWith("..") && !path.isAbsolute(relative);
}

function assertNoSymlinkInExistingPath(targetPath: string): void {
  const resolvedTarget = path.resolve(targetPath);
  const parsed = path.parse(resolvedTarget);
  const segments = path.relative(parsed.root, resolvedTarget).split(path.sep).filter(Boolean);
  let currentPath = parsed.root;
  for (const segment of segments) {
    currentPath = path.join(currentPath, segment);
    const stat = lstatSync(currentPath);
    if (stat.isSymbolicLink()) {
      throw new Error("live snapshot paths must not contain symlinks");
    }
  }
}

function isSandboxPolicy(value: unknown): value is SnapshotBoundWorkerPlan["sandboxPolicy"] {
  return isRecord(value) && hasOnlyKeys(value, ["type", "networkAccess"]) && value.type === "readOnly" && value.networkAccess === false;
}

function isTurnPreview(value: unknown): value is SnapshotBoundWorkerPlan["turnPreview"] {
  return (
    isRecord(value) &&
    hasOnlyKeys(value, ["cwd", "usesAnnex", "outputSchema", "artifactRefs", "snapshotIds"]) &&
    isSafeString(value.cwd) &&
    value.usesAnnex === true &&
    value.outputSchema === "WORKER_DONE_OR_NEED_REVIEWER" &&
    isSafeStringArray(value.artifactRefs) &&
    isSafeStringArray(value.snapshotIds)
  );
}

function isValidation(value: unknown): value is SnapshotBoundWorkerPlan["validation"] {
  return (
    isRecord(value) &&
    hasOnlyKeys(value, ["snapshotManifestBoundary", "annexApprovalVerified", "annexSnapshotMatchesManifest", "workerCwdIsSnapshotRoot"]) &&
    value.snapshotManifestBoundary === "PASS" &&
    value.annexApprovalVerified === "PASS" &&
    value.annexSnapshotMatchesManifest === "PASS" &&
    value.workerCwdIsSnapshotRoot === "PASS"
  );
}

function isBoundary(value: unknown): value is SnapshotBoundWorkerPlan["boundary"] {
  return (
    isRecord(value) &&
    hasOnlyKeys(value, ["managedWorkerStarted", "managedReviewerStarted", "directRealRepo", "workerCwdPolicy", "autoInjection", "rawContentIncluded"]) &&
    value.managedWorkerStarted === false &&
    value.managedReviewerStarted === false &&
    value.directRealRepo === "BLOCKED" &&
    value.workerCwdPolicy === "SNAPSHOT_ONLY" &&
    value.autoInjection === "DISABLED" &&
    value.rawContentIncluded === false
  );
}

function containsRawContentField(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.some((item) => containsRawContentField(item));
  }
  if (!isRecord(value)) {
    return false;
  }
  return Object.entries(value).some(([key, nested]) => rawContentFieldNames.has(key) || containsRawContentField(nested));
}

function assertSafePlanId(value: string, fieldName: string): void {
  if (!isSafePlanId(value)) {
    throw new Error(`unsafe snapshot Worker plan ${fieldName}`);
  }
}

function isSafePlanId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9._:-]{1,240}$/.test(value);
}

function isSafeString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0 && value.length <= 2000 && !value.includes("\0");
}

function isSafeStringArray(value: unknown): value is readonly string[] {
  return Array.isArray(value) && value.every(isSafeString);
}

function isIsoTimestamp(value: unknown): value is string {
  return typeof value === "string" && !Number.isNaN(Date.parse(value));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(value: Record<string, unknown>, allowed: readonly string[]): boolean {
  const allowedSet = new Set(allowed);
  return Object.keys(value).every((key) => allowedSet.has(key));
}
