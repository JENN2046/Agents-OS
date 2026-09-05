import { chmodSync, copyFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const source = fileURLToPath(new URL('../target/release/resident-peer-credentials', import.meta.url));
const target = fileURLToPath(new URL('../resident-peer-credentials', import.meta.url));
copyFileSync(source, target);
chmodSync(target, 0o755);
