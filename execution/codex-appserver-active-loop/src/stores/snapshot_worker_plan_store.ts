import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { assertSnapshotBoundWorkerPlan, type SnapshotBoundWorkerPlan } from "../bridge/snapshot_worker_pilot.js";
import { assertSafeJobId, safeJoin } from "./safe_path.js";

export interface SnapshotWorkerPlanStore {
  write(plan: SnapshotBoundWorkerPlan): Promise<string>;
  read(planId: string): Promise<SnapshotBoundWorkerPlan>;
  pathFor(planId: string): string;
}

export function createFileSnapshotWorkerPlanStore(rootDir: string): SnapshotWorkerPlanStore {
  return new FileSnapshotWorkerPlanStore(rootDir);
}

class FileSnapshotWorkerPlanStore implements SnapshotWorkerPlanStore {
  constructor(readonly rootDir: string) {}

  pathFor(planId: string): string {
    assertSafeJobId(planId);
    return safeJoin(this.rootDir, `${planId}.worker-plan.json`);
  }

  async write(plan: SnapshotBoundWorkerPlan): Promise<string> {
    assertSnapshotBoundWorkerPlan(plan);
    await mkdir(this.rootDir, { recursive: true });
    const target = this.pathFor(plan.planId);
    const temp = `${target}.${process.pid}.${Date.now()}.tmp`;
    await writeFile(temp, `${JSON.stringify(plan, null, 2)}\n`, "utf8");
    await rename(temp, target);
    return target;
  }

  async read(planId: string): Promise<SnapshotBoundWorkerPlan> {
    const parsed = JSON.parse(await readFile(this.pathFor(planId), "utf8")) as unknown;
    assertSnapshotBoundWorkerPlan(parsed);
    return parsed;
  }
}
