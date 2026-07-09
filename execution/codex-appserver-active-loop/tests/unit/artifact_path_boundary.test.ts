import { mkdir, rm, symlink, writeFile } from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { assertProjectArtifactPathBoundary } from "../../src/bridge/artifact_path_boundary.js";

const tmpRoot = path.join(process.cwd(), "data", "tmp", "artifact-path-boundary");

describe("artifact path boundary", () => {
  it("accepts real files under the allowed artifact root", async () => {
    const projectRoot = path.join(tmpRoot, `project-${Date.now()}`);
    const reportPath = path.join(projectRoot, "data", "reports", "report.json");
    await rm(projectRoot, { force: true, recursive: true });
    await mkdir(path.dirname(reportPath), { recursive: true });
    await writeFile(reportPath, "{}\n", "utf8");

    expect(assertProjectArtifactPathBoundary(projectRoot, reportPath, "data/reports", "report")).toBe(reportPath);
  });

  it("rejects artifact paths outside the allowed root or with denied terms", async () => {
    const projectRoot = path.join(tmpRoot, `denied-${Date.now()}`);
    const reportPath = path.join(projectRoot, "data", "reports", "report.json");
    const privatePath = path.join(projectRoot, "state-private", "report.json");
    await rm(projectRoot, { force: true, recursive: true });
    await mkdir(path.dirname(reportPath), { recursive: true });
    await mkdir(path.dirname(privatePath), { recursive: true });
    await writeFile(reportPath, "{}\n", "utf8");
    await writeFile(privatePath, "{}\n", "utf8");

    expect(() => assertProjectArtifactPathBoundary(projectRoot, reportPath, "data/receipts", "report")).toThrow("data/receipts");
    expect(() => assertProjectArtifactPathBoundary(projectRoot, privatePath, "state-private", "report")).toThrow("denied path term");
  });

  it("rejects symlinked artifact files", async () => {
    const projectRoot = path.join(tmpRoot, `symlink-${Date.now()}`);
    const reportRoot = path.join(projectRoot, "data", "reports");
    const outsideRoot = path.join(tmpRoot, `outside-${Date.now()}`);
    const outsidePath = path.join(outsideRoot, "report.json");
    const linkedPath = path.join(reportRoot, "linked.json");
    await rm(projectRoot, { force: true, recursive: true });
    await rm(outsideRoot, { force: true, recursive: true });
    await mkdir(reportRoot, { recursive: true });
    await mkdir(outsideRoot, { recursive: true });
    await writeFile(outsidePath, "{}\n", "utf8");
    await symlink(outsidePath, linkedPath);

    expect(() => assertProjectArtifactPathBoundary(projectRoot, linkedPath, "data/reports", "report")).toThrow("symlinks");
  });
});
