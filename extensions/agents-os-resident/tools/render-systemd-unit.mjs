import {
  chmodSync,
  chownSync,
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
  '@@DAEMON_UID@@',
  '@@MEMORY_BODY_ROOT@@',
  '@@NODE_BINARY@@',
  '@@PLUGIN_ROOT@@',
  '@@SOCKET_GID@@',
  '@@WITNESS_ROOT@@'
]);
const RENDER_KEYS = Object.freeze([
  'activationRoot',
  'buildId',
  'clientUid',
  'daemonUid',
  'memoryBodyRoot',
  'nodeBinary',
  'pluginRoot',
  'socketGid',
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

function validateOutputTargets(outputs) {
  const identities = outputs.map((output) => {
    if (!safeAbsolute(output) || output === '/') {
      throw new Error('SYSTEMD_RENDER_OUTPUT_PATH_INVALID');
    }
    try {
      const parent = dirname(output);
      const metadata = lstatSync(parent, { bigint: true });
      if (!metadata.isDirectory() || metadata.isSymbolicLink()
        || realpathSync.native(parent) !== parent) {
        throw new Error('SYSTEMD_RENDER_OUTPUT_PATH_INVALID');
      }
      // Device/inode also detects two distinct bind-mount paths to one parent.
      return `${metadata.dev}:${metadata.ino}:${basename(output)}`;
    } catch {
      throw new Error('SYSTEMD_RENDER_OUTPUT_PATH_INVALID');
    }
  });
  if (new Set(identities).size !== identities.length) {
    throw new Error('SYSTEMD_RENDER_OUTPUT_PATH_INVALID');
  }
}

function protectedRoot(value, daemonUid) {
  if (!safeAbsolute(value)) {
    throw new Error('SYSTEMD_RENDER_PROTECTED_ROOT_INVALID');
  }
  try {
    const stat = lstatSync(value);
    const canonical = realpathSync.native(value);
    if (!stat.isDirectory()
      || stat.isSymbolicLink()
      || canonical !== value
      || stat.uid !== daemonUid
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

function validateProtectedRoots(values, daemonUid) {
  const roots = values.map((value) => protectedRoot(value, daemonUid));
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

function validIdentityId(value) {
  return Number.isSafeInteger(value) && value > 0 && value <= 0xfffffffe;
}

function validateConfig(config) {
  if (!hasExactKeys(config, RENDER_KEYS)) {
    throw new Error('SYSTEMD_RENDER_INPUT_INVALID');
  }
  const {
    activationRoot,
    buildId,
    clientUid,
    daemonUid,
    memoryBodyRoot,
    nodeBinary,
    pluginRoot,
    socketGid,
    witnessRoot
  } = config;
  if (!safeAbsolute(nodeBinary)
    || !safeAbsolute(pluginRoot)
    || !safeAbsolute(activationRoot)
    || !safeAbsolute(memoryBodyRoot)
    || !safeAbsolute(witnessRoot)
    || !/^sha256:[0-9a-f]{64}$/.test(buildId)
    || !validIdentityId(daemonUid)
    || !validIdentityId(clientUid)
    || !validIdentityId(socketGid)
    || daemonUid === clientUid
    || basename(activationRoot) !== 'agents-os-resident-local-owner-v1') {
    throw new Error('SYSTEMD_RENDER_INPUT_INVALID');
  }
  validateProtectedRoots([activationRoot, witnessRoot, memoryBodyRoot], daemonUid);
}

export function renderDaemonIdentityPolicy(config) {
  validateConfig(config);
  // A generated policy is non-secret input for an administrator to install at
  // /etc/agents-os-resident/daemon-identity.json. Rendering does not qualify the
  // ownership or ancestry of an installed package or policy.
  return Object.freeze({
    schema: 'agents-os-resident.daemon-identity.v1',
    daemonUid: config.daemonUid,
    clientUid: config.clientUid,
    socketGid: config.socketGid,
    packageRoot: config.pluginRoot,
    nodeBinary: config.nodeBinary,
    buildId: config.buildId
  });
}

export function renderSystemdUnit(config) {
  validateConfig(config);
  const {
    activationRoot, buildId, daemonUid, memoryBodyRoot, nodeBinary,
    pluginRoot, socketGid, witnessRoot
  } = config;
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
    .replaceAll('@@DAEMON_UID@@', String(daemonUid))
    .replaceAll('@@SOCKET_GID@@', String(socketGid))
    .replaceAll('@@BUILD_ID@@', buildId);
  const restrictSuidSgid = rendered
    .split('\n')
    .filter((line) => line.startsWith('RestrictSUIDSGID='));
  if (REQUIRED_PLACEHOLDERS.some((placeholder) => rendered.includes(placeholder))
    || restrictSuidSgid.length !== 1
    || restrictSuidSgid[0] !== 'RestrictSUIDSGID=no'
    || !rendered.includes(`\nUser=${daemonUid}\n`)
    || !rendered.includes(`\nGroup=${socketGid}\n`)
    || !rendered.includes('--socket /run/agents-os-resident/control.sock ')
    || !rendered.includes('\nRuntimeDirectoryMode=0750\n')
    || !rendered.includes('\nWantedBy=multi-user.target\n')
    || !rendered.includes(`\nReadOnlyPaths=${pluginRoot} ${witnessRoot}\n`)
    || !rendered.includes(`\nReadWritePaths=${activationRoot} ${memoryBodyRoot}\n`)
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
      '--client-uid',
      '--daemon-uid',
      '--identity-output',
      '--memory-body-root',
      '--node',
      '--output',
      '--plugin-root',
      '--socket-gid',
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
    || !Object.hasOwn(parsed, '--client-uid')
    || !Object.hasOwn(parsed, '--daemon-uid')
    || !Object.hasOwn(parsed, '--identity-output')
    || !Object.hasOwn(parsed, '--memory-body-root')
    || !Object.hasOwn(parsed, '--node')
    || !Object.hasOwn(parsed, '--output')
    || !Object.hasOwn(parsed, '--plugin-root')
    || !Object.hasOwn(parsed, '--socket-gid')
    || !Object.hasOwn(parsed, '--witness-root')) {
    throw new Error('SYSTEMD_RENDER_ARGUMENTS_INVALID');
  }
  for (const key of ['--client-uid', '--daemon-uid', '--socket-gid']) {
    if (!/^[1-9][0-9]*$/.test(parsed[key])
      || !validIdentityId(Number(parsed[key]))) {
      throw new Error('SYSTEMD_RENDER_ARGUMENTS_INVALID');
    }
  }
  return Object.freeze({
    activationRoot: parsed['--activation-root'],
    clientUid: Number(parsed['--client-uid']),
    daemonUid: Number(parsed['--daemon-uid']),
    identityOutput: parsed['--identity-output'],
    memoryBodyRoot: parsed['--memory-body-root'],
    nodeBinary: parsed['--node'],
    output: parsed['--output'],
    pluginRoot: parsed['--plugin-root'],
    socketGid: Number(parsed['--socket-gid']),
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
      const stateRoot = resolve(root, 'state');
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
      const currentUid = process.getuid();
      const daemonUid = currentUid === 0 ? 2001 : currentUid;
      const socketGid = process.getgid() === 0 ? 2002 : process.getgid();
      if (currentUid === 0) {
        // These three empty roots were created above in this disposable fixture.
        for (const directory of [activationRoot, witnessRoot, memoryBodyRoot]) {
          chownSync(directory, daemonUid, socketGid);
        }
      }
      const config = {
        activationRoot,
        buildId: integrity.buildId,
        daemonUid,
        clientUid: currentUid === 0 ? 2002 : daemonUid === 65534 ? 65533 : 65534,
        socketGid,
        memoryBodyRoot,
        nodeBinary: process.execPath,
        pluginRoot,
        witnessRoot
      };
      renderSystemdUnit(config);
      renderDaemonIdentityPolicy(config);
    } finally {
      rmSync(root, { force: true, recursive: true });
    }
    process.stdout.write('SYSTEMD_UNIT_STRUCTURAL_CHECK_PASSED; NOT_INSTALLATION_QUALIFICATION\n');
    return;
  }
  validateOutputTargets([args.output, args.identityOutput]);
  const config = {
    activationRoot: args.activationRoot,
    buildId: integrity.buildId,
    clientUid: args.clientUid,
    daemonUid: args.daemonUid,
    memoryBodyRoot: args.memoryBodyRoot,
    nodeBinary: args.nodeBinary,
    pluginRoot: args.pluginRoot,
    socketGid: args.socketGid,
    witnessRoot: args.witnessRoot
  };
  const rendered = renderSystemdUnit(config);
  const identity = `${JSON.stringify(renderDaemonIdentityPolicy(config), null, 2)}\n`;
  for (const [output, contents] of [
    [args.output, rendered], [args.identityOutput, identity]
  ]) {
    const temporary = `${output}.tmp-${process.pid}`;
    let created = false;
    try {
      writeFileSync(temporary, contents, { flag: 'wx', mode: 0o644 });
      created = true;
      chmodSync(temporary, 0o644);
      renameSync(temporary, output);
    } finally {
      if (created) rmSync(temporary, { force: true });
    }
  }
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch {
    process.stderr.write('SYSTEMD_UNIT_RENDER_FAILED\n');
    process.exit(1);
  }
}
