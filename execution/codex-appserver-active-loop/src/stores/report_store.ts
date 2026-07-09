import { mkdir, rename, writeFile } from "node:fs/promises";
import { safeJoin } from "./safe_path.js";

export interface ReportStore {
  writeFinalReport(report: unknown): Promise<string>;
  pathForFinalReport(): string;
}

export function createFileReportStore(rootDir: string): ReportStore {
  return new FileReportStore(rootDir);
}

class FileReportStore implements ReportStore {
  constructor(readonly rootDir: string) {}

  pathForFinalReport(): string {
    return safeJoin(this.rootDir, "final_report.json");
  }

  async writeFinalReport(report: unknown): Promise<string> {
    await mkdir(this.rootDir, { recursive: true });
    const target = this.pathForFinalReport();
    const temp = `${target}.${process.pid}.${Date.now()}.tmp`;
    await writeFile(temp, `${JSON.stringify(report, null, 2)}\n`, "utf8");
    await rename(temp, target);
    return target;
  }
}
