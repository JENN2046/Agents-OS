import { lstatSync, realpathSync } from "node:fs";
import path from "node:path";

const deniedArtifactPathTerms = [
  ".git",
  ".env",
  "config.env",
  "node_modules",
  "dist",
  "state-private",
  "secret",
  "secrets",
  "credential",
  "credentials",
  "token",
  "tokens",
  "cookie",
  "cookies",
  ".ssh",
  "data/tmp",
  "data/review-packages",
  "id_rsa",
  "id_ed25519",
] as const;

export function assertProjectArtifactPathBoundary(
  projectRoot: string,
  artifactPath: string,
  allowedRelativeRoot: string,
  label: string,
): string {
  if (!artifactPath || artifactPath.includes("\0")) {
    throw new Error(`${label} path is missing or invalid`);
  }
  const resolvedProjectRoot = path.resolve(projectRoot);
  const allowedRoot = path.resolve(resolvedProjectRoot, allowedRelativeRoot);
  const resolvedArtifactPath = path.resolve(artifactPath);
  assertNoDeniedArtifactPathTerms(resolvedProjectRoot, resolvedArtifactPath, label);
  if (!isPathInsideRootOrEqual(allowedRoot, resolvedArtifactPath)) {
    throw new Error(`${label} must stay under ${allowedRelativeRoot}`);
  }
  assertNoSymlinkInExistingPath(allowedRoot);
  assertNoSymlinkInExistingPath(resolvedArtifactPath);
  const realAllowedRoot = realpathSync(allowedRoot);
  const realArtifactPath = realpathSync(resolvedArtifactPath);
  assertNoDeniedArtifactPathTerms(resolvedProjectRoot, realArtifactPath, label);
  if (!isPathInsideRootOrEqual(realAllowedRoot, realArtifactPath)) {
    throw new Error(`${label} must stay under ${allowedRelativeRoot}`);
  }
  return resolvedArtifactPath;
}

export function assertAllowedArtifactFilename(artifactPath: string, allowedFilenames: readonly string[], label: string): void {
  const filename = path.basename(artifactPath);
  if (!allowedFilenames.includes(filename)) {
    throw new Error(`${label} filename is not allowed: ${filename}`);
  }
}

function assertNoDeniedArtifactPathTerms(projectRoot: string, artifactPath: string, label: string): void {
  const relativePath = toPosixPath(path.relative(projectRoot, artifactPath));
  const lower = relativePath.toLowerCase();
  const denied = deniedArtifactPathTerms.find((term) => lower === term || lower.includes(term));
  if (denied) {
    throw new Error(`${label} contains denied path term: ${denied}`);
  }
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
      throw new Error("artifact paths must not contain symlinks");
    }
  }
}

function isPathInsideRootOrEqual(root: string, candidate: string): boolean {
  const relative = path.relative(path.resolve(root), path.resolve(candidate));
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function toPosixPath(input: string): string {
  return input.replaceAll("\\", "/");
}
