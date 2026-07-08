import { createHash } from "node:crypto";
import { copyFile, mkdir, readdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";

export const defaultSnapshotAllowlist = [
  "src",
  "tests",
  "docs",
  "schemas",
  "data/synthetic-workspace",
  "data/reports",
  "data/receipts",
  "README.md",
  "package.json",
  "package-lock.json",
  "tsconfig.json",
  "vitest.config.ts",
] as const;

export const snapshotDeniedPathTerms = [
  ".git",
  ".env",
  "config.env",
  "secrets",
  "secret",
  "credentials",
  "credential",
  "tokens",
  "token",
  "cookies",
  "cookie",
  ".ssh",
  "state-private",
  "id_rsa",
  "id_ed25519",
] as const;

export const snapshotDeniedDirectoryNames = [
  ".git",
  "node_modules",
  "dist",
  "state-private",
  ".ssh",
  "secrets",
  "data/tmp",
  "data/review-packages",
  "data/snapshots",
] as const;

const deniedExtensions = [".pem", ".key", ".p12", ".pfx"] as const;

const sensitiveContentPatterns = [
  /\bBearer\s+[A-Za-z0-9._~+/=-]+/i,
  /\bsk-[A-Za-z0-9._-]+/,
  /\bOPENAI_API_KEY\s*=/i,
  /\bapi[_-]?key\s*=/i,
  /\bAuthorization\s*:/i,
  /\bpassword\s*=/i,
  /\bprivate[_-]?key\b/i,
] as const;

export interface SnapshotFileEntry {
  readonly relativePath: string;
  readonly bytes: number;
  readonly sha256: string;
}

export interface SnapshotExclusion {
  readonly relativePath: string;
  readonly reason: string;
  readonly matched: readonly string[];
}

export interface SnapshotManifest {
  readonly snapshotVersion: 1;
  readonly createdAt: string;
  readonly sourceRoot: string;
  readonly snapshotRoot: string;
  readonly workerCwd: string;
  readonly allowlist: readonly string[];
  readonly includedFiles: readonly SnapshotFileEntry[];
  readonly excludedFiles: readonly SnapshotExclusion[];
  readonly boundary: {
    readonly bridgeExporterReadSource: true;
    readonly managedSessionsReadSource: false;
    readonly workerCwdSnapshotOnly: true;
    readonly phase8DirectRealRepo: "BLOCKED";
  };
}

export interface SnapshotExportResult {
  readonly snapshotRoot: string;
  readonly manifestPath: string;
  readonly exclusionReportPath: string;
  readonly manifest: SnapshotManifest;
}

export interface SnapshotExportOptions {
  readonly sourceRoot: string;
  readonly snapshotRoot: string;
  readonly allowlist?: readonly string[];
  readonly now?: () => Date;
  readonly maxFileBytes?: number;
}

export async function exportSafeRepoSnapshot(options: SnapshotExportOptions): Promise<SnapshotExportResult> {
  const sourceRoot = path.resolve(options.sourceRoot);
  const snapshotRoot = path.resolve(options.snapshotRoot);
  assertSnapshotRootOutsideSourceTraversal(sourceRoot, snapshotRoot);

  const allowlist = options.allowlist ?? defaultSnapshotAllowlist;
  const now = options.now ?? (() => new Date());
  const maxFileBytes = options.maxFileBytes ?? 512 * 1024;
  const includedFiles: SnapshotFileEntry[] = [];
  const excludedFiles: SnapshotExclusion[] = [];

  await mkdir(snapshotRoot, { recursive: true });

  for (const entry of allowlist) {
    const relativeEntry = normalizeRelativePath(entry);
    const allowlistExclusion = classifyPath(relativeEntry);
    if (allowlistExclusion) {
      excludedFiles.push(allowlistExclusion);
      continue;
    }

    const sourcePath = resolveInsideRoot(sourceRoot, relativeEntry);
    let sourceStat;
    try {
      sourceStat = await stat(sourcePath);
    } catch {
      excludedFiles.push({ relativePath: relativeEntry, reason: "allowlist_entry_missing", matched: [] });
      continue;
    }

    if (sourceStat.isDirectory()) {
      await copyDirectory(sourceRoot, snapshotRoot, relativeEntry, includedFiles, excludedFiles, maxFileBytes);
    } else if (sourceStat.isFile()) {
      await copyAllowedFile(sourceRoot, snapshotRoot, relativeEntry, includedFiles, excludedFiles, maxFileBytes);
    } else {
      excludedFiles.push({ relativePath: relativeEntry, reason: "not_regular_file_or_directory", matched: [] });
    }
  }

  includedFiles.sort((a, b) => a.relativePath.localeCompare(b.relativePath));
  excludedFiles.sort((a, b) => a.relativePath.localeCompare(b.relativePath));

  const manifest: SnapshotManifest = {
    snapshotVersion: 1,
    createdAt: now().toISOString(),
    sourceRoot,
    snapshotRoot,
    workerCwd: snapshotRoot,
    allowlist: [...allowlist],
    includedFiles,
    excludedFiles,
    boundary: {
      bridgeExporterReadSource: true,
      managedSessionsReadSource: false,
      workerCwdSnapshotOnly: true,
      phase8DirectRealRepo: "BLOCKED",
    },
  };

  const metaDir = path.join(snapshotRoot, "_snapshot");
  await mkdir(metaDir, { recursive: true });
  const manifestPath = path.join(metaDir, "manifest.json");
  const exclusionReportPath = path.join(metaDir, "exclusions.json");
  await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  await writeFile(
    exclusionReportPath,
    `${JSON.stringify({ createdAt: manifest.createdAt, excludedFiles, redactionApplied: false }, null, 2)}\n`,
    "utf8",
  );

  return { snapshotRoot, manifestPath, exclusionReportPath, manifest };
}

export function assertWorkerCwdIsSnapshot(workerCwd: string, snapshotRoot: string): void {
  if (path.resolve(workerCwd) !== path.resolve(snapshotRoot)) {
    throw new Error("Worker cwd must be the generated snapshot path");
  }
}

async function copyDirectory(
  sourceRoot: string,
  snapshotRoot: string,
  relativeDir: string,
  includedFiles: SnapshotFileEntry[],
  excludedFiles: SnapshotExclusion[],
  maxFileBytes: number,
): Promise<void> {
  const dirExclusion = classifyPath(relativeDir);
  if (dirExclusion) {
    excludedFiles.push(dirExclusion);
    return;
  }

  const sourceDir = resolveInsideRoot(sourceRoot, relativeDir);
  const entries = await readdir(sourceDir, { withFileTypes: true });
  for (const entry of entries) {
    const relativePath = toPosixPath(path.join(relativeDir, entry.name));
    const exclusion = classifyPath(relativePath);
    if (exclusion) {
      excludedFiles.push(exclusion);
      continue;
    }
    if (entry.isDirectory()) {
      await copyDirectory(sourceRoot, snapshotRoot, relativePath, includedFiles, excludedFiles, maxFileBytes);
    } else if (entry.isFile()) {
      await copyAllowedFile(sourceRoot, snapshotRoot, relativePath, includedFiles, excludedFiles, maxFileBytes);
    } else {
      excludedFiles.push({ relativePath, reason: "not_regular_file_or_directory", matched: [] });
    }
  }
}

async function copyAllowedFile(
  sourceRoot: string,
  snapshotRoot: string,
  relativePath: string,
  includedFiles: SnapshotFileEntry[],
  excludedFiles: SnapshotExclusion[],
  maxFileBytes: number,
): Promise<void> {
  const exclusion = classifyPath(relativePath);
  if (exclusion) {
    excludedFiles.push(exclusion);
    return;
  }

  const sourcePath = resolveInsideRoot(sourceRoot, relativePath);
  const sourceStat = await stat(sourcePath);
  if (sourceStat.size > maxFileBytes) {
    excludedFiles.push({ relativePath, reason: "file_too_large", matched: [`>${maxFileBytes}`] });
    return;
  }

  const content = await readFile(sourcePath);
  const sensitiveMatches = findSensitiveContentMatches(content);
  if (sensitiveMatches.length > 0) {
    excludedFiles.push({ relativePath, reason: "sensitive_content_pattern", matched: sensitiveMatches });
    return;
  }

  const targetPath = resolveInsideRoot(snapshotRoot, relativePath);
  await mkdir(path.dirname(targetPath), { recursive: true });
  await copyFile(sourcePath, targetPath);
  includedFiles.push({
    relativePath,
    bytes: sourceStat.size,
    sha256: createHash("sha256").update(content).digest("hex").toUpperCase(),
  });
}

function classifyPath(relativePath: string): SnapshotExclusion | undefined {
  const normalized = normalizeRelativePath(relativePath);
  const lower = normalized.toLowerCase();
  const matched: string[] = [];

  for (const deniedDir of snapshotDeniedDirectoryNames) {
    const normalizedDenied = deniedDir.toLowerCase();
    if (lower === normalizedDenied || lower.startsWith(`${normalizedDenied}/`) || lower.includes(`/${normalizedDenied}/`)) {
      matched.push(deniedDir);
    }
  }

  for (const term of snapshotDeniedPathTerms) {
    if (lower.includes(term.toLowerCase())) {
      matched.push(term);
    }
  }

  for (const extension of deniedExtensions) {
    if (lower.endsWith(extension)) {
      matched.push(extension);
    }
  }

  return matched.length > 0
    ? { relativePath: normalized, reason: "denied_path_term", matched: [...new Set(matched)].sort() }
    : undefined;
}

function findSensitiveContentMatches(content: Buffer): readonly string[] {
  const text = content.toString("utf8");
  const matched = sensitiveContentPatterns
    .filter((pattern) => pattern.test(text))
    .map((pattern) => pattern.source);
  return [...new Set(matched)].sort();
}

function normalizeRelativePath(input: string): string {
  if (!input || input.includes("\0")) {
    throw new Error("snapshot path must be non-empty and must not contain null bytes");
  }
  const normalized = toPosixPath(path.normalize(input));
  if (normalized === "." || normalized.startsWith("../") || path.isAbsolute(normalized)) {
    throw new Error(`snapshot allowlist path escapes source root: ${input}`);
  }
  return normalized;
}

function resolveInsideRoot(root: string, relativePath: string): string {
  const resolvedRoot = path.resolve(root);
  const resolvedPath = path.resolve(resolvedRoot, relativePath);
  const relative = path.relative(resolvedRoot, resolvedPath);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`snapshot path escapes root: ${relativePath}`);
  }
  return resolvedPath;
}

function assertSnapshotRootOutsideSourceTraversal(sourceRoot: string, snapshotRoot: string): void {
  if (snapshotRoot === sourceRoot) {
    throw new Error("snapshot root must not be the source root");
  }
  const relative = path.relative(sourceRoot, snapshotRoot);
  if (relative === "" || relative.startsWith("..") || path.isAbsolute(relative)) {
    return;
  }
  if (!toPosixPath(relative).startsWith("data/snapshots/")) {
    throw new Error("snapshot root inside source root must be under data/snapshots");
  }
}

function toPosixPath(input: string): string {
  return input.replaceAll("\\", "/");
}
