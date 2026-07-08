import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import type { JobRecord } from "../types/jobs.js";
import { assertSafeJobId, safeJoin } from "./safe_path.js";

export interface JobStore {
  put(job: JobRecord): Promise<void>;
  get(jobId: string): Promise<JobRecord | undefined>;
  pathFor(jobId: string): string;
}

export function createFileJobStore(rootDir: string): JobStore {
  return new FileJobStore(rootDir);
}

class FileJobStore implements JobStore {
  constructor(readonly rootDir: string) {}

  pathFor(jobId: string): string {
    assertSafeJobId(jobId);
    return safeJoin(this.rootDir, `${jobId}.json`);
  }

  async put(job: JobRecord): Promise<void> {
    assertSafeJobId(job.jobId);
    await mkdir(this.rootDir, { recursive: true });
    const target = this.pathFor(job.jobId);
    const temp = `${target}.${process.pid}.${Date.now()}.tmp`;
    await writeFile(temp, `${JSON.stringify(job, null, 2)}\n`, "utf8");
    await rename(temp, target);
  }

  async get(jobId: string): Promise<JobRecord | undefined> {
    try {
      return JSON.parse(await readFile(this.pathFor(jobId), "utf8")) as JobRecord;
    } catch (error) {
      if (isNotFound(error)) {
        return undefined;
      }
      throw error;
    }
  }
}

function isNotFound(error: unknown): boolean {
  return typeof error === "object" && error !== null && "code" in error && error.code === "ENOENT";
}
