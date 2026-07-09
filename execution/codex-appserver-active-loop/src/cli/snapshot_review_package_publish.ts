import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { mkdir, readdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";
import {
  createSnapshotReviewPackagePlan,
  isAllowedSnapshotReviewPackageEntry,
  type SnapshotReviewPackageArtifact,
} from "../bridge/snapshot_review_package.js";
import { assertAllowedArtifactFilename, assertProjectArtifactPathBoundary } from "../bridge/artifact_path_boundary.js";
import { safeJoin } from "../stores/safe_path.js";

const execFileAsync = promisify(execFile);

type ZipCreationTool = "ZIP_CLI" | "PYTHON_ZIPFILE" | "POWERSHELL_COMPRESS_ARCHIVE";

interface CopiedPackageArtifact extends SnapshotReviewPackageArtifact {
  readonly bytes: number;
  readonly sha256: string;
}

async function main(): Promise<void> {
  const projectRoot = process.cwd();
  const completedAt = new Date().toISOString();
  const timestamp = completedAt.replace(/[-:.TZ]/g, "").slice(0, 14);
  const packageId = `snapshot-review-closure-${timestamp}`;
  const packageDir = path.join(projectRoot, "data", "review-packages", packageId);
  const contentDir = path.join(packageDir, "content");
  const zipPath = path.join(packageDir, `codex-appserver-active-loop-${packageId}.zip`);
  const reportPath = path.join(projectRoot, "data", "reports", "cea-021_snapshot_review_package_publisher.json");
  const receiptPath = path.join(projectRoot, "data", "receipts", `${formatDateForReceipt(new Date(completedAt))}-cea-021-snapshot-review-package-publisher.receipt.md`);

  const cea018Report = await readJson(path.join(projectRoot, "data", "reports", "cea-018_e2e_safe_review_loop.json"));
  const cea019Report = await readJson(path.join(projectRoot, "data", "reports", "cea-019_e2e_evidence_verification_gate.json"));
  const cea020Report = await readJson(path.join(projectRoot, "data", "reports", "cea-020_phase8_schema_gate.json"));
  const plan = createSnapshotReviewPackagePlan({ cea018Report, cea019Report, cea020Report });
  await mkdir(contentDir, { recursive: true });

  const copied: CopiedPackageArtifact[] = [];
  for (const item of plan.artifacts) {
    const sourcePath = resolvePackageSourceArtifact(projectRoot, item);
    const content = await readFile(sourcePath);
    const target = safeJoin(contentDir, item.entryPath);
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, content);
    copied.push({
      ...item,
      sourcePath,
      bytes: content.length,
      sha256: sha256(content),
    });
  }

  const packageManifest = {
    manifestVersion: 1,
    task_id: "CEA-021",
    package_id: packageId,
    created_at: completedAt,
    source_project_root: projectRoot,
    source_tasks: plan.sourceTasks,
    content_policy: plan.contentPolicy,
    included_files: copied.map((item) => ({
      task_id: item.taskId,
      kind: item.kind,
      label: item.label,
      entry_path: item.entryPath,
      source_path: item.sourcePath,
      bytes: item.bytes,
      sha256: item.sha256,
    })),
    excluded_referenced_artifacts: plan.excludedReferencedArtifactLabels,
    boundary: {
      only_manifest_report_receipt: true,
      events_copied: false,
      prompt_packets_copied: false,
      prompt_annexes_copied: false,
      worker_plans_copied: false,
      snapshot_source_files_copied: false,
      phase8_direct_real_repo: "BLOCKED",
    },
  };
  await writeJson(path.join(contentDir, "MANIFEST.json"), packageManifest);

  const zipCreationTool = await createZipFromContent(contentDir, zipPath);
  const zipEntries = await listZipEntries(zipPath);
  const forbiddenZipEntries = zipEntries.filter((entry) => !isAllowedSnapshotReviewPackageEntry(entry));
  const zipBytes = (await stat(zipPath)).size;
  const zipHash = sha256(await readFile(zipPath));

  const report = {
    task_id: "CEA-021",
    title: "Snapshot Review Package Publisher",
    result: forbiddenZipEntries.length === 0 ? "PASS" : "FAIL",
    completed_at: completedAt,
    package_id: packageId,
    package_dir: packageDir,
    content_dir: contentDir,
    zip: zipPath,
    zip_sha256: zipHash,
    zip_size_bytes: zipBytes,
    source_reports: {
      cea018: path.join(projectRoot, "data", "reports", "cea-018_e2e_safe_review_loop.json"),
      cea019: path.join(projectRoot, "data", "reports", "cea-019_e2e_evidence_verification_gate.json"),
      cea020: path.join(projectRoot, "data", "reports", "cea-020_phase8_schema_gate.json"),
    },
    included_files: copied.map((item) => ({
      task_id: item.taskId,
      kind: item.kind,
      label: item.label,
      entry_path: item.entryPath,
      source_path: item.sourcePath,
      bytes: item.bytes,
      sha256: item.sha256,
    })),
    excluded_referenced_artifacts: plan.excludedReferencedArtifactLabels,
    validation: {
      source_files_exist: "PASS",
      copied_hashes_recorded: "PASS",
      zip_created: "PASS",
      zip_entry_count: zipEntries.length,
      zip_entry_allowlist_scan: forbiddenZipEntries.length === 0 ? "PASS" : "FAIL",
      forbidden_zip_entries: forbiddenZipEntries,
      package_contains_only_manifest_report_receipt: forbiddenZipEntries.length === 0,
    },
    boundary_flags: {
      app_server_started: "NOT_STARTED",
      managed_worker_started: "NOT_STARTED",
      managed_reviewer_started: "NOT_STARTED",
      phase8_direct_real_repo: "BLOCKED",
      events_copied: "NO",
      ledger_packet_approval_annex_plan_copied: "NO",
      snapshot_source_files_copied: "NO",
      secrets_read: "NOT_USED",
      command_exec_api: "NOT_USED",
      local_zip_tool: zipCreationTool,
      commit_push_deploy_release_tag: "NOT_USED",
    },
    artifacts: {
      package_manifest: path.join(contentDir, "MANIFEST.json"),
      zip: zipPath,
      report: reportPath,
      receipt: receiptPath,
    },
  };
  await writeJson(reportPath, report);
  await writeReceipt(receiptPath, report);
  console.log(JSON.stringify(report, null, 2));
  if (report.result !== "PASS") {
    process.exitCode = 1;
  }
}

async function readJson(filePath: string): Promise<unknown> {
  return JSON.parse(await readFile(filePath, "utf8")) as unknown;
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
    readonly package_id: string;
    readonly zip: string;
    readonly zip_sha256: string;
    readonly zip_size_bytes: number;
    readonly validation: { readonly zip_entry_count: number; readonly zip_entry_allowlist_scan: string };
    readonly boundary_flags: {
      readonly phase8_direct_real_repo: string;
      readonly events_copied: string;
      readonly ledger_packet_approval_annex_plan_copied: string;
      readonly snapshot_source_files_copied: string;
    };
    readonly artifacts: { readonly report: string; readonly receipt: string; readonly package_manifest: string };
  },
): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const lines = [
    "# CEA-021 Snapshot Review Package Publisher Receipt",
    "",
    `result: ${report.result}`,
    `package_id: ${report.package_id}`,
    `zip: ${report.zip}`,
    `zip_sha256: ${report.zip_sha256}`,
    `zip_size_bytes: ${report.zip_size_bytes}`,
    "",
    "## Validation",
    `- zip_entry_count: ${report.validation.zip_entry_count}`,
    `- zip_entry_allowlist_scan: ${report.validation.zip_entry_allowlist_scan}`,
    "",
    "## Boundary",
    `- phase8_direct_real_repo: ${report.boundary_flags.phase8_direct_real_repo}`,
    `- events_copied: ${report.boundary_flags.events_copied}`,
    `- ledger_packet_approval_annex_plan_copied: ${report.boundary_flags.ledger_packet_approval_annex_plan_copied}`,
    `- snapshot_source_files_copied: ${report.boundary_flags.snapshot_source_files_copied}`,
    "",
    "## Artifacts",
    `- package_manifest: ${report.artifacts.package_manifest}`,
    `- report: ${report.artifacts.report}`,
    `- receipt: ${report.artifacts.receipt}`,
    "",
  ];
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, lines.join("\n"), "utf8");
}

function resolvePackageSourceArtifact(projectRoot: string, item: SnapshotReviewPackageArtifact): string {
  const allowedRoot = packageSourceRootForItem(item);
  const sourcePath = assertProjectArtifactPathBoundary(projectRoot, item.sourcePath, allowedRoot, `${item.taskId} ${item.label}`);
  assertAllowedArtifactFilename(sourcePath, [expectedSourceFilenameForItem(item)], `${item.taskId} ${item.label}`);
  return sourcePath;
}

function packageSourceRootForItem(item: SnapshotReviewPackageArtifact): string {
  if (item.taskId === "CEA-018" && (item.label === "snapshot_manifest" || item.label === "snapshot_exclusions")) {
    return "data/snapshots";
  }
  if (item.kind === "report") {
    return "data/reports";
  }
  if (item.kind === "receipt") {
    return "data/receipts";
  }
  throw new Error(`unsupported package source artifact kind: ${item.kind}`);
}

function expectedSourceFilenameForItem(item: SnapshotReviewPackageArtifact): string {
  if (item.label === "snapshot_manifest") return "manifest.json";
  if (item.label === "snapshot_exclusions") return "exclusions.json";
  return path.basename(item.entryPath);
}

async function createZipFromContent(contentDir: string, zipPath: string): Promise<ZipCreationTool> {
  await mkdir(path.dirname(zipPath), { recursive: true });
  await rm(zipPath, { force: true });
  const relativeFiles = await collectRelativeFiles(contentDir);
  if (relativeFiles.length === 0) {
    throw new Error("snapshot review package content directory contains no files");
  }
  if (await commandAvailable("zip")) {
    await execFileAsync("zip", ["-q", zipPath, ...relativeFiles], {
      cwd: contentDir,
      windowsHide: true,
      maxBuffer: 10 * 1024 * 1024,
    });
    return "ZIP_CLI";
  }
  if (await commandAvailable("python3")) {
    await createZipWithPython(contentDir, zipPath, relativeFiles);
    return "PYTHON_ZIPFILE";
  }

  const command =
    "& { param([string]$ContentDir, [string]$ZipPath); $ErrorActionPreference='Stop'; Compress-Archive -Path (Join-Path $ContentDir '*') -DestinationPath $ZipPath -Force }";
  await execPowerShell(command, [await toPowerShellPath(contentDir), await toPowerShellPath(zipPath)]);
  return "POWERSHELL_COMPRESS_ARCHIVE";
}

async function listZipEntries(zipPath: string): Promise<readonly string[]> {
  if (await commandAvailable("unzip")) {
    const { stdout } = await execFileAsync("unzip", ["-Z1", zipPath], {
      windowsHide: true,
      maxBuffer: 10 * 1024 * 1024,
    });
    return parseLineSeparatedZipEntries(stdout);
  }
  if (await commandAvailable("python3")) {
    const script = [
      "import json, sys, zipfile",
      "with zipfile.ZipFile(sys.argv[1], 'r') as archive:",
      "    print(json.dumps(archive.namelist(), separators=(',', ':')))",
    ].join("\n");
    const { stdout } = await execFileAsync("python3", ["-c", script, zipPath], {
      windowsHide: true,
      maxBuffer: 10 * 1024 * 1024,
    });
    return parseJsonZipEntries(stdout);
  }
  const command =
    "& { param([string]$ZipPath); $ErrorActionPreference='Stop'; Add-Type -AssemblyName System.IO.Compression.FileSystem; $zip=[System.IO.Compression.ZipFile]::OpenRead($ZipPath); try { $zip.Entries | ForEach-Object { $_.FullName } | ConvertTo-Json -Compress } finally { $zip.Dispose() } }";
  const { stdout } = await execPowerShell(command, [await toPowerShellPath(zipPath)]);
  return parseJsonZipEntries(stdout);
}

async function collectRelativeFiles(root: string, current = root): Promise<string[]> {
  const entries = await readdir(current, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    const entryPath = path.join(current, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectRelativeFiles(root, entryPath)));
      continue;
    }
    if (entry.isFile()) {
      files.push(toZipEntry(path.relative(root, entryPath)));
    }
  }
  return files.sort((left, right) => left.localeCompare(right));
}

async function createZipWithPython(contentDir: string, zipPath: string, relativeFiles: readonly string[]): Promise<void> {
  const script = [
    "import sys, zipfile",
    "root = sys.argv[1]",
    "out = sys.argv[2]",
    "files = sys.argv[3:]",
    "with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as archive:",
    "    for name in files:",
    "        archive.write(__import__('os').path.join(root, *name.split('/')), name)",
  ].join("\n");
  await execFileAsync("python3", ["-c", script, contentDir, zipPath, ...relativeFiles], {
    windowsHide: true,
    maxBuffer: 10 * 1024 * 1024,
  });
}

function parseLineSeparatedZipEntries(stdout: string): readonly string[] {
  return stdout
    .split(/\r?\n/)
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
}

function parseJsonZipEntries(stdout: string): readonly string[] {
  const trimmed = stdout.trim();
  if (!trimmed) return [];
  const parsed = JSON.parse(trimmed) as unknown;
  return Array.isArray(parsed) ? parsed.filter((entry): entry is string => typeof entry === "string") : typeof parsed === "string" ? [parsed] : [];
}

async function commandAvailable(command: string): Promise<boolean> {
  const locator = process.platform === "win32" ? "where.exe" : "which";
  try {
    await execFileAsync(locator, [command], {
      windowsHide: true,
      maxBuffer: 1024 * 1024,
    });
    return true;
  } catch {
    return false;
  }
}

async function execPowerShell(command: string, args: readonly string[]): Promise<{ stdout: string; stderr: string }> {
  return execFileAsync("powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command, ...args], {
    windowsHide: true,
    maxBuffer: 10 * 1024 * 1024,
  });
}

async function toPowerShellPath(filePath: string): Promise<string> {
  if (process.platform !== "linux") return filePath;
  try {
    const { stdout } = await execFileAsync("wslpath", ["-w", filePath], {
      windowsHide: true,
      maxBuffer: 1024 * 1024,
    });
    const converted = stdout.trim();
    return converted.length > 0 ? converted : filePath;
  } catch {
    return filePath;
  }
}

function sha256(content: Buffer | string): string {
  return createHash("sha256").update(content).digest("hex").toUpperCase();
}

function toZipEntry(filePath: string): string {
  return filePath.split(path.sep).join("/");
}

function formatDateForReceipt(date: Date): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const year = parts.find((part) => part.type === "year")?.value ?? "0000";
  const month = parts.find((part) => part.type === "month")?.value ?? "00";
  const day = parts.find((part) => part.type === "day")?.value ?? "00";
  return `${year}-${month}-${day}`;
}

void main();
