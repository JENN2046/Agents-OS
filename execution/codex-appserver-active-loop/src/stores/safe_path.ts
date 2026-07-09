import path from "node:path";

export function safeJoin(root: string, filename: string): string {
  if (!filename || filename.includes("\0")) {
    throw new Error("unsafe empty or null-containing filename");
  }

  const resolvedRoot = path.resolve(root);
  const resolvedPath = path.resolve(resolvedRoot, filename);
  const relative = path.relative(resolvedRoot, resolvedPath);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`path escapes store root: ${filename}`);
  }
  return resolvedPath;
}

export function assertSafeJobId(jobId: string): void {
  if (!/^[A-Za-z0-9._-]+$/.test(jobId)) {
    throw new Error(`unsafe job id: ${jobId}`);
  }
}
