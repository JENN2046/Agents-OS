import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { safeJoin } from "../stores/safe_path.js";

export async function writeJsonArtifact(filePath: string, value: unknown): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

export async function writeReceiptArtifact(filePath: string, title: string, lines: readonly string[]): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  const target = safeJoin(path.dirname(filePath), path.basename(filePath));
  await writeFile(target, [`# ${title}`, "", ...lines, ""].join("\n"), "utf8");
}
