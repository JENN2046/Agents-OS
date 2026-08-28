import { createHash } from 'node:crypto';
import {
  existsSync,
  lstatSync,
  readFileSync
} from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const SCHEMA_VERSION =
  'agents-os-resident.host-presentation-source-binding.v1';
const CANONICALIZATION = 'ORDERED_PATH_BYTE_LENGTH_SHA256_JSON_V1';
const SOURCE_PATHS = Object.freeze([
  'runtime/VCPToolBox/Plugin.js',
  'runtime/VCPToolBox/modules/chatCompletionHandler.js',
  'runtime/VCPToolBox/modules/handlers/nonStreamHandler.js',
  'runtime/VCPToolBox/modules/handlers/streamHandler.js',
  'runtime/VCPToolBox/modules/vcpLoop/toolExecutor.js',
  'runtime/VCPToolBox/modules/vcpLoop/residentPresentation.js',
  'runtime/VCPChat/modules/messageRenderer.js',
  'runtime/VCPChat/modules/renderer/streamManager.js',
  'runtime/VCPChat/modules/renderer/residentEphemeralPresentation.mjs',
  'runtime/VCPChat/modules/ipc/chatHandlers.js',
  'runtime/VCPChat/modules/vcpClient.js',
  'runtime/VCPChat/renderer.js',
  'runtime/VCPChat/styles/messageRenderer.css'
]);
const HEX_64 = /^[0-9a-f]{64}$/u;

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function hasExactKeys(value, expectedKeys) {
  return value !== null
    && typeof value === 'object'
    && !Array.isArray(value)
    && Object.keys(value).length === expectedKeys.length
    && expectedKeys.every((key) => Object.hasOwn(value, key));
}

function resolveWorkspaceRoot() {
  const candidates = [
    process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT,
    resolve(PACKAGE_ROOT, '../..'),
    resolve(PACKAGE_ROOT, '../../../..')
  ].filter((candidate) => typeof candidate === 'string');
  for (const candidate of candidates) {
    if (SOURCE_PATHS.every((sourcePath) => (
      existsSync(resolve(candidate, sourcePath))
    ))) {
      return candidate;
    }
  }
  throw new Error('HOST_PRESENTATION_WORKSPACE_NOT_FOUND');
}

function readSourceRows(workspaceRoot) {
  return SOURCE_PATHS.map((sourcePath) => {
    const absolute = resolve(workspaceRoot, sourcePath);
    const stat = lstatSync(absolute);
    if (!stat.isFile() || stat.isSymbolicLink()) {
      throw new Error('HOST_PRESENTATION_SOURCE_INVALID');
    }
    const bytes = readFileSync(absolute);
    return Object.freeze({
      path: sourcePath,
      byteLength: bytes.length,
      sha256: sha256(bytes)
    });
  });
}

export function verifyHostPresentationBinding() {
  const metadata = JSON.parse(
    readFileSync(resolve(PACKAGE_ROOT, 'package-manifest.json'), 'utf8')
  );
  const binding = metadata.host_presentation_source_binding;
  if (!hasExactKeys(binding, [
    'schemaVersion',
    'bundleId',
    'canonicalization',
    'files'
  ])
    || binding.schemaVersion !== SCHEMA_VERSION
    || binding.canonicalization !== CANONICALIZATION
    || typeof binding.bundleId !== 'string'
    || !binding.bundleId.startsWith('sha256:')
    || !HEX_64.test(binding.bundleId.slice('sha256:'.length))
    || !Array.isArray(binding.files)
    || binding.files.length !== SOURCE_PATHS.length) {
    throw new Error('HOST_PRESENTATION_BINDING_INVALID');
  }

  const rows = readSourceRows(resolveWorkspaceRoot());
  if (JSON.stringify(binding.files) !== JSON.stringify(rows)) {
    throw new Error('HOST_PRESENTATION_SOURCE_MISMATCH');
  }
  const bundleId = `sha256:${sha256(Buffer.from(JSON.stringify(rows), 'utf8'))}`;
  if (binding.bundleId !== bundleId) {
    throw new Error('HOST_PRESENTATION_BUNDLE_ID_MISMATCH');
  }

  return Object.freeze({
    result: 'HOST_PRESENTATION_SOURCE_BINDING_VERIFIED',
    bundleId,
    fileCount: rows.length
  });
}

function main(argv) {
  if (argv.length !== 1 || argv[0] !== '--check') {
    throw new Error('HOST_PRESENTATION_BINDING_ARGUMENTS_INVALID');
  }
  process.stdout.write(`${JSON.stringify(verifyHostPresentationBinding())}\n`);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch {
    process.stderr.write('HOST_PRESENTATION_SOURCE_BINDING_FAILED\n');
    process.exit(1);
  }
}
