import {
  chmodSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  realpathSync,
  renameSync,
  rmSync,
  writeFileSync
} from 'node:fs';
import { tmpdir } from 'node:os';
import {
  basename,
  dirname,
  isAbsolute,
  join,
  normalize,
  relative,
  resolve,
  sep
} from 'node:path';
import { fileURLToPath } from 'node:url';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const TEMPLATE_PATH = resolve(
  PACKAGE_ROOT,
  'systemd/agents-os-resident.service.template'
);
const INTEGRITY_PATH = resolve(PACKAGE_ROOT, 'companion-integrity.json');
const REQUIRED_PLACEHOLDERS = Object.freeze([
  '@@ACTIVATION_ROOT@@',
  '@@BUILD_ID@@',
  '@@MEMORY_BODY_ROOT@@',
  '@@NODE_BINARY@@',
  '@@PLUGIN_ROOT@@',
  '@@WITNESS_ROOT@@'
]);
const RENDER_KEYS = Object.freeze([
  'activationRoot',
  'buildId',
  'memoryBodyRoot',
  'nodeBinary',
  'pluginRoot',
  'witnessRoot'
]);

function isPlainObject(value) {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function hasExactKeys(value, expected) {
  if (!isPlainObject(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length
    && actual.every((key, index) => key === wanted[index]);
}

function safeAbsolute(value) {
  return typeof value === 'string'
    && value.length > 0
    && isAbsolute(value)
    && normalize(value) === value
    && !/[\0\r\n\t %$\\'"]/.test(value);
}

function protectedRoot(value) {
  if (!safeAbsolute(value)) {
    throw new Error('SYSTEMD_RENDER_PROTECTED_ROOT_INVALID');
  }
  try {
    const stat = lstatSync(value);
    const canonical = realpathSync.native(value);
    const uid = typeof process.getuid === 'function' ? process.getuid() : null;
    if (!stat.isDirectory()
      || stat.isSymbolicLink()
      || canonical !== value
      || uid === null
      || stat.uid !== uid
      || (stat.mode & 0o777) !== 0o700) {
      throw new Error('SYSTEMD_RENDER_PROTECTED_ROOT_INVALID');
    }
    return Object.freeze({
      device: stat.dev,
      inode: stat.ino,
      path: canonical
    });
  } catch (error) {
    if (error?.message === 'SYSTEMD_RENDER_PROTECTED_ROOT_INVALID') {
      throw error;
    }
    throw new Error('SYSTEMD_RENDER_PROTECTED_ROOT_INVALID');
  }
}

function pathContains(parent, child) {
  const result = relative(parent, child);
  return result === ''
    || (result !== '..'
      && !result.startsWith(`..${sep}`)
      && !isAbsolute(result));
}

function validateProtectedRoots(values) {
  const roots = values.map(protectedRoot);
  for (let left = 0; left < roots.length; left += 1) {
    for (let right = left + 1; right < roots.length; right += 1) {
      if ((roots[left].device === roots[right].device
          && roots[left].inode === roots[right].inode)
        || pathContains(roots[left].path, roots[right].path)
        || pathContains(roots[right].path, roots[left].path)) {
        throw new Error('SYSTEMD_RENDER_PROTECTED_ROOT_OVERLAP');
      }
    }
  }
}

function parseIntegrity() {
  const manifest = JSON.parse(readFileSync(INTEGRITY_PATH, 'utf8'));
  if (!/^sha256:[0-9a-f]{64}$/.test(manifest.buildId)) {
    throw new Error('SYSTEMD_RENDER_INTEGRITY_INVALID');
  }
  return manifest;
}

export function renderSystemdUnit(config) {
  if (!hasExactKeys(config, RENDER_KEYS)) {
    throw new Error('SYSTEMD_RENDER_INPUT_INVALID');
  }
  const {
    activationRoot,
    buildId,
    memoryBodyRoot,
    nodeBinary,
    pluginRoot,
    witnessRoot
  } = config;
  if (!safeAbsolute(nodeBinary)
    || !safeAbsolute(pluginRoot)
    || !safeAbsolute(activationRoot)
    || !safeAbsolute(memoryBodyRoot)
    || !safeAbsolute(witnessRoot)
    || !/^sha256:[0-9a-f]{64}$/.test(buildId)
    || !activationRoot.startsWith(`${pluginRoot}/state/`)
    || basename(activationRoot) !== 'agents-os-resident-local-owner-v1') {
    throw new Error('SYSTEMD_RENDER_INPUT_INVALID');
  }
  validateProtectedRoots([activationRoot, witnessRoot, memoryBodyRoot]);
  const templateStat = lstatSync(TEMPLATE_PATH);
  if (!templateStat.isFile() || templateStat.isSymbolicLink()) {
    throw new Error('SYSTEMD_TEMPLATE_INVALID');
  }
  let rendered = readFileSync(TEMPLATE_PATH, 'utf8');
  for (const placeholder of REQUIRED_PLACEHOLDERS) {
    if (!rendered.includes(placeholder)) {
      throw new Error('SYSTEMD_TEMPLATE_INVALID');
    }
  }
  rendered = rendered
    .replaceAll('@@NODE_BINARY@@', nodeBinary)
    .replaceAll('@@PLUGIN_ROOT@@', pluginRoot)
    .replaceAll('@@ACTIVATION_ROOT@@', activationRoot)
    .replaceAll('@@WITNESS_ROOT@@', witnessRoot)
    .replaceAll('@@MEMORY_BODY_ROOT@@', memoryBodyRoot)
    .replaceAll('@@BUILD_ID@@', buildId);
  const restrictSuidSgid = rendered
    .split('\n')
    .filter((line) => line.startsWith('RestrictSUIDSGID='));
  if (REQUIRED_PLACEHOLDERS.some((placeholder) => rendered.includes(placeholder))
    || restrictSuidSgid.length !== 1
    || restrictSuidSgid[0] !== 'RestrictSUIDSGID=no'
    || !rendered.includes('RestrictAddressFamilies=AF_UNIX')
    || !rendered.includes('IPAddressDeny=any')
    || !rendered.includes('StandardOutput=null')
    || !rendered.includes('StandardError=null')
    || rendered.includes('PartOf=')
    || rendered.includes('BindsTo=')
    || rendered.includes('MemoryDenyWriteExecute=')
    || rendered.includes('SystemCallFilter=')) {
    throw new Error('SYSTEMD_RENDER_OUTPUT_INVALID');
  }
  return `${rendered.trimEnd()}\n`;
}

function parseArgs(argv) {
  if (argv.length === 1 && argv[0] === '--check') {
    return Object.freeze({ check: true });
  }
  if (argv.length === 0 || argv.length % 2 !== 0) {
    throw new Error('SYSTEMD_RENDER_ARGUMENTS_INVALID');
  }
  const parsed = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (![
      '--activation-root',
      '--memory-body-root',
      '--node',
      '--output',
      '--plugin-root',
      '--witness-root'
    ].includes(key)
      || typeof value !== 'string'
      || value.length === 0
      || Object.hasOwn(parsed, key)) {
      throw new Error('SYSTEMD_RENDER_ARGUMENTS_INVALID');
    }
    parsed[key] = value;
  }
  if (!Object.hasOwn(parsed, '--activation-root')
    || !Object.hasOwn(parsed, '--memory-body-root')
    || !Object.hasOwn(parsed, '--node')
    || !Object.hasOwn(parsed, '--output')
    || !Object.hasOwn(parsed, '--plugin-root')
    || !Object.hasOwn(parsed, '--witness-root')) {
    throw new Error('SYSTEMD_RENDER_ARGUMENTS_INVALID');
  }
  return Object.freeze({
    activationRoot: parsed['--activation-root'],
    memoryBodyRoot: parsed['--memory-body-root'],
    nodeBinary: parsed['--node'],
    output: parsed['--output'],
    pluginRoot: parsed['--plugin-root'],
    witnessRoot: parsed['--witness-root']
  });
}

function main(argv) {
  const args = parseArgs(argv);
  const integrity = parseIntegrity();
  if (args.check) {
    const root = mkdtempSync(join(tmpdir(), 'agents-os-resident-systemd-check-'));
    try {
      chmodSync(root, 0o700);
      const pluginRoot = resolve(root, 'plugin');
      const stateRoot = resolve(pluginRoot, 'state');
      const activationRoot = resolve(
        stateRoot,
        'agents-os-resident-local-owner-v1'
      );
      const witnessRoot = resolve(stateRoot, 'protected-witness');
      const memoryBodyRoot = resolve(stateRoot, 'private-memory-bodies');
      for (const directory of [
        pluginRoot,
        stateRoot,
        activationRoot,
        witnessRoot,
        memoryBodyRoot
      ]) {
        mkdirSync(directory, { mode: 0o700 });
        chmodSync(directory, 0o700);
      }
      renderSystemdUnit({
        activationRoot,
        buildId: integrity.buildId,
        memoryBodyRoot,
        nodeBinary: process.execPath,
        pluginRoot,
        witnessRoot
      });
    } finally {
      rmSync(root, { force: true, recursive: true });
    }
    process.stdout.write('SYSTEMD_UNIT_TEMPLATE_VERIFIED\n');
    return;
  }
  if (!safeAbsolute(args.output)) {
    throw new Error('SYSTEMD_RENDER_OUTPUT_PATH_INVALID');
  }
  const rendered = renderSystemdUnit({
    activationRoot: args.activationRoot,
    buildId: integrity.buildId,
    memoryBodyRoot: args.memoryBodyRoot,
    nodeBinary: args.nodeBinary,
    pluginRoot: args.pluginRoot,
    witnessRoot: args.witnessRoot
  });
  const temporary = `${args.output}.tmp-${process.pid}`;
  writeFileSync(temporary, rendered, { flag: 'wx', mode: 0o644 });
  chmodSync(temporary, 0o644);
  renameSync(temporary, args.output);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch {
    process.stderr.write('SYSTEMD_UNIT_RENDER_FAILED\n');
    process.exit(1);
  }
}
