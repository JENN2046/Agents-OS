import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { assertPromptAnnex, type PromptAnnex } from "../bridge/prompt_annex.js";
import { assertSafeJobId, safeJoin } from "./safe_path.js";

export interface PromptAnnexStore {
  write(annex: PromptAnnex): Promise<string>;
  read(annexId: string): Promise<PromptAnnex>;
  pathFor(annexId: string): string;
}

export function createFilePromptAnnexStore(rootDir: string): PromptAnnexStore {
  return new FilePromptAnnexStore(rootDir);
}

class FilePromptAnnexStore implements PromptAnnexStore {
  constructor(readonly rootDir: string) {}

  pathFor(annexId: string): string {
    assertSafeJobId(annexId);
    return safeJoin(this.rootDir, `${annexId}.prompt-annex.json`);
  }

  async write(annex: PromptAnnex): Promise<string> {
    assertPromptAnnex(annex);
    await mkdir(this.rootDir, { recursive: true });
    const target = this.pathFor(annex.annexId);
    const temp = `${target}.${process.pid}.${Date.now()}.tmp`;
    await writeFile(temp, `${JSON.stringify(annex, null, 2)}\n`, "utf8");
    await rename(temp, target);
    return target;
  }

  async read(annexId: string): Promise<PromptAnnex> {
    const parsed = JSON.parse(await readFile(this.pathFor(annexId), "utf8")) as unknown;
    assertPromptAnnex(parsed);
    return parsed;
  }
}
