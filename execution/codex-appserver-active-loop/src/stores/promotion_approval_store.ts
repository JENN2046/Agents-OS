import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { assertPromotionApprovalReceipt, type PromotionApprovalReceipt } from "../bridge/promotion_approval.js";
import { assertSafeJobId, safeJoin } from "./safe_path.js";

export interface PromotionApprovalStore {
  write(receipt: PromotionApprovalReceipt): Promise<string>;
  read(receiptId: string): Promise<PromotionApprovalReceipt>;
  pathFor(receiptId: string): string;
}

export function createFilePromotionApprovalStore(rootDir: string): PromotionApprovalStore {
  return new FilePromotionApprovalStore(rootDir);
}

class FilePromotionApprovalStore implements PromotionApprovalStore {
  constructor(readonly rootDir: string) {}

  pathFor(receiptId: string): string {
    assertSafeJobId(receiptId);
    return safeJoin(this.rootDir, `${receiptId}.approval.json`);
  }

  async write(receipt: PromotionApprovalReceipt): Promise<string> {
    assertPromotionApprovalReceipt(receipt);
    await mkdir(this.rootDir, { recursive: true });
    const target = this.pathFor(receipt.receiptId);
    const temp = `${target}.${process.pid}.${Date.now()}.tmp`;
    await writeFile(temp, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
    await rename(temp, target);
    return target;
  }

  async read(receiptId: string): Promise<PromotionApprovalReceipt> {
    const parsed = JSON.parse(await readFile(this.pathFor(receiptId), "utf8")) as unknown;
    assertPromotionApprovalReceipt(parsed);
    return parsed;
  }
}
