import { createHash } from 'node:crypto';
import {
  chmodSync,
  lstatSync,
  readFileSync,
  renameSync,
  writeFileSync
} from 'node:fs';
import { dirname, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const OUTPUT_PATH = resolve(PACKAGE_ROOT, 'companion-integrity.json');
const SCHEMA_VERSION = 'agents-os-resident.companion-integrity.v1';
const INVENTORY = Object.freeze([
  'activation.js',
  'agents-os-resident.linux-x64-gnu.node',
  'companion/adapter.js',
  'companion/client.js',
  'companion/constants.js',
  'companion/discovery.js',
  'companion/integrity.js',
  'companion/probe.js',
  'companion/protocol.js',
  'companion/resident-daemon.js',
  'companion/server.js',
  'index.js',
  'package-manifest.json',
  'package.json',
  'plugin-manifest.json.block',
  'systemd/agents-os-resident.service.template',
  'tools/build-companion-integrity.mjs',
  'tools/render-systemd-unit.mjs',
  'tools/validate-companion-projection.mjs',
  'tools/verify-host-presentation-binding.mjs'
]);

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function canonicalJson(value) {
  const canonicalize = (input) => {
    if (Array.isArray(input)) {
      return input.map(canonicalize);
    }
    if (input !== null && typeof input === 'object') {
      return Object.fromEntries(
        Object.keys(input).sort().map((key) => [key, canonicalize(input[key])])
      );
    }
    return input;
  };
  return Buffer.from(JSON.stringify(canonicalize(value)), 'utf8');
}

export function buildCompanionIntegrity() {
  const packageJson = JSON.parse(
    readFileSync(resolve(PACKAGE_ROOT, 'package.json'), 'utf8')
  );
  const files = INVENTORY.map((sourcePath) => {
    const absolute = resolve(PACKAGE_ROOT, sourcePath);
    const rel = relative(PACKAGE_ROOT, absolute).split(sep).join('/');
    const stat = lstatSync(absolute);
    if (rel !== sourcePath
      || rel.startsWith('../')
      || !stat.isFile()
      || stat.isSymbolicLink()
      || stat.nlink !== 1) {
      throw new Error('COMPANION_INTEGRITY_INPUT_INVALID');
    }
    const bytes = readFileSync(absolute);
    return Object.freeze({
      path: sourcePath,
      byteLength: bytes.length,
      sha256: sha256(bytes)
    });
  });
  const base = Object.freeze({
    schemaVersion: SCHEMA_VERSION,
    packageVersion: packageJson.version,
    files
  });
  return Object.freeze({
    ...base,
    buildId: `sha256:${sha256(canonicalJson(base))}`
  });
}

export function encodeCompanionIntegrity(manifest) {
  return Buffer.from(`${JSON.stringify({
    schemaVersion: manifest.schemaVersion,
    packageVersion: manifest.packageVersion,
    buildId: manifest.buildId,
    files: manifest.files
  }, null, 2)}\n`, 'utf8');
}

function main(argv) {
  const manifest = buildCompanionIntegrity();
  const bytes = encodeCompanionIntegrity(manifest);
  if (argv.length === 0 || (argv.length === 1 && argv[0] === '--stdout')) {
    process.stdout.write(bytes);
    return;
  }
  if (argv.length !== 2 || argv[0] !== '--output' || resolve(argv[1]) !== OUTPUT_PATH) {
    throw new Error('COMPANION_INTEGRITY_OUTPUT_INVALID');
  }
  const temporary = `${OUTPUT_PATH}.tmp-${process.pid}`;
  writeFileSync(temporary, bytes, { flag: 'wx', mode: 0o644 });
  chmodSync(temporary, 0o644);
  renameSync(temporary, OUTPUT_PATH);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch {
    process.stderr.write('COMPANION_INTEGRITY_BUILD_FAILED\n');
    process.exit(1);
  }
}
