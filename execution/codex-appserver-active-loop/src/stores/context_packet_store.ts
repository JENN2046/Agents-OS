import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { assertContextPromotionPacket, type ContextPromotionPacket } from "../bridge/context_promotion.js";
import { assertSafeJobId, safeJoin } from "./safe_path.js";

export interface ContextPacketStore {
  write(packet: ContextPromotionPacket): Promise<string>;
  read(packetId: string): Promise<ContextPromotionPacket>;
  pathFor(packetId: string): string;
}

export function createFileContextPacketStore(rootDir: string): ContextPacketStore {
  return new FileContextPacketStore(rootDir);
}

class FileContextPacketStore implements ContextPacketStore {
  constructor(readonly rootDir: string) {}

  pathFor(packetId: string): string {
    assertSafeJobId(packetId);
    return safeJoin(this.rootDir, `${packetId}.context-packet.json`);
  }

  async write(packet: ContextPromotionPacket): Promise<string> {
    assertContextPromotionPacket(packet);
    await mkdir(this.rootDir, { recursive: true });
    const target = this.pathFor(packet.packetId);
    const temp = `${target}.${process.pid}.${Date.now()}.tmp`;
    await writeFile(temp, `${JSON.stringify(packet, null, 2)}\n`, "utf8");
    await rename(temp, target);
    return target;
  }

  async read(packetId: string): Promise<ContextPromotionPacket> {
    const parsed = JSON.parse(await readFile(this.pathFor(packetId), "utf8")) as unknown;
    assertContextPromotionPacket(parsed);
    return parsed;
  }
}
