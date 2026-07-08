import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { assertWorkerCwdIsSnapshot, exportSafeRepoSnapshot } from "../../src/bridge/repo_snapshot.js";

const tmpRoot = path.join(process.cwd(), "data", "tmp", "repo-snapshot");

describe("safe repo snapshot exporter", () => {
  it("copies only allowlisted safe files and writes manifest plus exclusion report", async () => {
    const sourceRoot = path.join(tmpRoot, `source-${Date.now()}`);
    const snapshotRoot = path.join(tmpRoot, `snapshot-${Date.now()}`);
    await rm(sourceRoot, { force: true, recursive: true });
    await rm(snapshotRoot, { force: true, recursive: true });
    await mkdir(path.join(sourceRoot, "src"), { recursive: true });
    await mkdir(path.join(sourceRoot, "docs"), { recursive: true });
    await mkdir(path.join(sourceRoot, ".git"), { recursive: true });
    await mkdir(path.join(sourceRoot, "node_modules/pkg"), { recursive: true });
    await mkdir(path.join(sourceRoot, "state-private"), { recursive: true });

    await writeFile(path.join(sourceRoot, "src/index.ts"), "export const ok = true;\n", "utf8");
    await writeFile(path.join(sourceRoot, "docs/README.md"), "safe docs\n", "utf8");
    await writeFile(path.join(sourceRoot, "docs/.gitkeep"), "\n", "utf8");
    await writeFile(path.join(sourceRoot, ".env"), "OPENAI_API_KEY=secret\n", "utf8");
    await writeFile(path.join(sourceRoot, ".gitignore"), "node_modules\n", "utf8");
    await writeFile(path.join(sourceRoot, "src/token-example.ts"), "export const name = 'nope';\n", "utf8");
    await writeFile(path.join(sourceRoot, "src/leaky.ts"), "const value = 'sk-test';\n", "utf8");
    await writeFile(path.join(sourceRoot, ".git/config"), "repo metadata\n", "utf8");
    await writeFile(path.join(sourceRoot, "node_modules/pkg/index.js"), "pkg\n", "utf8");
    await writeFile(path.join(sourceRoot, "state-private/memory.md"), "private\n", "utf8");

    const result = await exportSafeRepoSnapshot({
      sourceRoot,
      snapshotRoot,
      allowlist: ["src", "docs", ".env", ".git", ".gitignore", "node_modules", "state-private"],
      now: () => new Date("2026-07-07T00:00:00.000Z"),
    });

    const included = result.manifest.includedFiles.map((file) => file.relativePath).sort();
    expect(included).toEqual(["docs/README.md", "src/index.ts"]);
    expect(result.manifest.excludedFiles.map((file) => file.relativePath)).toEqual(
      expect.arrayContaining([
        ".env",
        ".git",
        ".gitignore",
        "docs/.gitkeep",
        "node_modules",
        "src/leaky.ts",
        "src/token-example.ts",
        "state-private",
      ]),
    );
    expect(result.manifest.workerCwd).toBe(snapshotRoot);
    expect(result.manifest.boundary).toMatchObject({
      bridgeExporterReadSource: true,
      managedSessionsReadSource: false,
      workerCwdSnapshotOnly: true,
      phase8DirectRealRepo: "BLOCKED",
    });

    await expect(readFile(path.join(snapshotRoot, "src/index.ts"), "utf8")).resolves.toContain("ok");
    await expect(readFile(result.manifestPath, "utf8")).resolves.toContain("workerCwdSnapshotOnly");
    await expect(readFile(result.exclusionReportPath, "utf8")).resolves.toContain("denied_path_term");
  });

  it("requires managed Worker cwd to be the snapshot root", () => {
    assertWorkerCwdIsSnapshot("A:/snapshot", "A:/snapshot");
    expect(() => assertWorkerCwdIsSnapshot("A:/repo", "A:/snapshot")).toThrow("snapshot path");
  });

  it("rejects allowlist path escapes", async () => {
    const sourceRoot = path.join(tmpRoot, `escape-source-${Date.now()}`);
    await mkdir(sourceRoot, { recursive: true });
    await expect(
      exportSafeRepoSnapshot({
        sourceRoot,
        snapshotRoot: path.join(tmpRoot, `escape-snapshot-${Date.now()}`),
        allowlist: ["../outside"],
      }),
    ).rejects.toThrow("escapes source root");
  });
});
