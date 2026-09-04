'use strict';

const {
  closeSync,
  constants: fsConstants,
  fstatSync,
  lstatSync,
  openSync,
  readSync,
  realpathSync
} = require('node:fs');
const path = require('node:path');
const { TextDecoder } = require('node:util');

const { createResidentLifecycle } = require('../activation');
const {
  ACTIVATION_CONFIRMATION,
  ACTIVATION_MODE,
  fixedError
} = require('./constants');
const { verifyCompanionIntegrity } = require('./integrity');
const { createCompanionServer } = require('./server');

const GENESIS_PROVISIONING_PROTOCOL = 'MMR0_GENESIS_PROVISIONING_V1';
const LOCAL_OWNER_RESIDENT_ID = 'resident:LOCAL_OWNER_SESSION_V1:jenn';
const MAX_AUTHORITY_FILE_BYTES = 4096;
const MAX_AUTHORITY_TOKEN_BYTES = 300;
const PREPARE_ROOTS_RESULT = 'RESIDENT_PROTECTED_ROOTS_PREPARED';
const PROVISIONING_RESULT = 'RESIDENT_WITNESS_PROVISIONED';

const ALL_DAEMON_ARGUMENTS = new Set([
  '--continuity-evidence',
  '--expected-build-id',
  '--genesis-authority-file',
  '--genesis-provisioning-authority',
  '--memory-body-root',
  '--operation',
  '--root',
  '--socket',
  '--witness-root'
]);
const SERVE_ARGUMENTS = new Set([
  '--continuity-evidence',
  '--expected-build-id',
  '--genesis-provisioning-authority',
  '--memory-body-root',
  '--root',
  '--socket',
  '--witness-root'
]);
const PROVISION_ARGUMENTS = new Set([
  '--expected-build-id',
  '--genesis-authority-file',
  '--memory-body-root',
  '--operation',
  '--root',
  '--witness-root'
]);
const PROVISION_REQUIRED_ARGUMENTS = [...PROVISION_ARGUMENTS];
const PREPARE_ROOTS_ARGUMENTS = new Set([
  '--expected-build-id',
  '--memory-body-root',
  '--operation',
  '--root',
  '--witness-root'
]);
const PREPARE_ROOTS_REQUIRED_ARGUMENTS = [...PREPARE_ROOTS_ARGUMENTS];
const AUTHORITY_KEYS = [
  'authorityId',
  'protocol',
  'provisioningId',
  'residentId'
];

const AUTHORITY_OPEN_FLAGS = fsConstants.O_RDONLY
  | fsConstants.O_NOFOLLOW
  | (fsConstants.O_CLOEXEC ?? 0)
  | (fsConstants.O_NONBLOCK ?? 0);
const PROTECTED_ROOT_OPEN_FLAGS = fsConstants.O_RDONLY
  | fsConstants.O_DIRECTORY
  | fsConstants.O_NOFOLLOW
  | (fsConstants.O_CLOEXEC ?? 0)
  | (fsConstants.O_NONBLOCK ?? 0);

function isPlainObject(value) {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

// Transport-layer decode of an optional serialized-JSON daemon argument. The
// daemon only moves the bytes: it never interprets continuity MATCH, genesis
// authorization, or admission semantics. Canonical validation remains in the
// P1/native admission path, and a malformed transport form fails closed.
function parseOptionalJson(result, key) {
  if (!Object.hasOwn(result, key)) {
    return null;
  }
  let parsed;
  try {
    parsed = JSON.parse(result[key]);
  } catch {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  if (!isPlainObject(parsed)) {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  return parsed;
}

function parseOptionalAbsolutePath(result, key) {
  if (!Object.hasOwn(result, key)) {
    return null;
  }
  const value = result[key];
  if (!path.isAbsolute(value) || path.normalize(value) !== value) {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  return value;
}

function pathsOverlap(left, right) {
  const leftToRight = path.relative(left, right);
  const rightToLeft = path.relative(right, left);
  const descends = (relative) => relative === ''
    || (relative !== '..'
      && !relative.startsWith(`..${path.sep}`)
      && !path.isAbsolute(relative));
  return descends(leftToRight) || descends(rightToLeft);
}

function requireDisjointRoots(...roots) {
  const present = roots.filter((root) => root !== null);
  for (let left = 0; left < present.length; left += 1) {
    for (let right = left + 1; right < present.length; right += 1) {
      if (pathsOverlap(present[left], present[right])) {
        throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
      }
    }
  }
}

function parseArgumentPairs(argv) {
  if (!Array.isArray(argv) || argv.length % 2 !== 0) {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!ALL_DAEMON_ARGUMENTS.has(key)
      || typeof value !== 'string'
      || value.length === 0
      || value.includes('\0')
      || Object.hasOwn(result, key)) {
      throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
    }
    result[key] = value;
  }
  return result;
}

function validExpectedBuildId(result) {
  return Object.hasOwn(result, '--expected-build-id')
    && /^sha256:[0-9a-f]{64}$/.test(result['--expected-build-id']);
}

function parseProvisionArgs(result) {
  if (result['--operation'] !== 'provision'
    || Object.keys(result).length !== PROVISION_REQUIRED_ARGUMENTS.length
    || PROVISION_REQUIRED_ARGUMENTS.some((key) => !Object.hasOwn(result, key))
    || Object.keys(result).some((key) => !PROVISION_ARGUMENTS.has(key))
    || !validExpectedBuildId(result)) {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  const rootPath = parseOptionalAbsolutePath(result, '--root');
  const witnessRootPath = parseOptionalAbsolutePath(result, '--witness-root');
  const memoryBodyRootPath = parseOptionalAbsolutePath(result, '--memory-body-root');
  const authorityFilePath = parseOptionalAbsolutePath(result, '--genesis-authority-file');
  if ([rootPath, witnessRootPath, memoryBodyRootPath, authorityFilePath]
    .some((value) => value === null)
    || path.basename(rootPath) !== 'agents-os-resident-local-owner-v1') {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  requireDisjointRoots(rootPath, witnessRootPath, memoryBodyRootPath);
  return Object.freeze({
    authorityFilePath,
    continuityEvidence: null,
    expectedBuildId: result['--expected-build-id'],
    genesisProvisioningAuthority: null,
    memoryBodyRootPath,
    operation: 'provision',
    rootPath,
    socketPath: null,
    witnessRootPath
  });
}

function parsePrepareRootsArgs(result) {
  if (result['--operation'] !== 'prepare-roots'
    || Object.keys(result).length !== PREPARE_ROOTS_REQUIRED_ARGUMENTS.length
    || PREPARE_ROOTS_REQUIRED_ARGUMENTS.some(
      (key) => !Object.hasOwn(result, key)
    )
    || Object.keys(result).some((key) => !PREPARE_ROOTS_ARGUMENTS.has(key))
    || !validExpectedBuildId(result)) {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  const rootPath = parseOptionalAbsolutePath(result, '--root');
  const witnessRootPath = parseOptionalAbsolutePath(result, '--witness-root');
  const memoryBodyRootPath = parseOptionalAbsolutePath(result, '--memory-body-root');
  if ([rootPath, witnessRootPath, memoryBodyRootPath]
    .some((value) => value === null)
    || path.basename(rootPath) !== 'agents-os-resident-local-owner-v1') {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  requireDisjointRoots(rootPath, witnessRootPath, memoryBodyRootPath);
  return Object.freeze({
    authorityFilePath: null,
    continuityEvidence: null,
    expectedBuildId: result['--expected-build-id'],
    genesisProvisioningAuthority: null,
    memoryBodyRootPath,
    operation: 'prepare-roots',
    rootPath,
    socketPath: null,
    witnessRootPath
  });
}

function parseServeArgs(result) {
  if (Object.hasOwn(result, '--operation')
    || Object.keys(result).some((key) => !SERVE_ARGUMENTS.has(key))
    || !['--expected-build-id', '--root', '--socket']
      .every((key) => Object.hasOwn(result, key))
    || !validExpectedBuildId(result)) {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  const rootPath = parseOptionalAbsolutePath(result, '--root');
  const socketPath = parseOptionalAbsolutePath(result, '--socket');
  const continuityEvidence = parseOptionalJson(result, '--continuity-evidence');
  const memoryBodyRootPath = parseOptionalAbsolutePath(result, '--memory-body-root');
  const witnessRootPath = parseOptionalAbsolutePath(result, '--witness-root');
  const genesisProvisioningAuthority = parseOptionalJson(
    result,
    '--genesis-provisioning-authority'
  );
  if (rootPath === null
    || socketPath === null
    || (memoryBodyRootPath !== null && witnessRootPath === null)
    || (witnessRootPath !== null
      && (continuityEvidence !== null || genesisProvisioningAuthority !== null))) {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  requireDisjointRoots(rootPath, witnessRootPath, memoryBodyRootPath);
  return Object.freeze({
    authorityFilePath: null,
    continuityEvidence,
    expectedBuildId: result['--expected-build-id'],
    genesisProvisioningAuthority,
    memoryBodyRootPath,
    operation: 'serve',
    rootPath,
    socketPath,
    witnessRootPath
  });
}

function parseDaemonArgs(argv) {
  const result = parseArgumentPairs(argv);
  if (!Object.hasOwn(result, '--operation')) {
    return parseServeArgs(result);
  }
  return result['--operation'] === 'prepare-roots'
    ? parsePrepareRootsArgs(result)
    : parseProvisionArgs(result);
}

function sameDescriptor(left, right) {
  return [
    'dev',
    'ino',
    'mode',
    'nlink',
    'uid',
    'gid',
    'size',
    'mtimeNs',
    'ctimeNs'
  ].every((key) => left[key] === right[key]);
}

function validAuthorityDescriptor(stat) {
  return stat.isFile()
    && !stat.isSymbolicLink()
    && stat.uid === BigInt(process.geteuid())
    && (stat.mode & 0o7777n) === 0o600n
    && stat.nlink === 1n
    && stat.size > 0n
    && stat.size <= BigInt(MAX_AUTHORITY_FILE_BYTES);
}

function validProtectedRootDescriptor(stat) {
  return stat.isDirectory()
    && !stat.isSymbolicLink()
    && stat.uid === BigInt(process.geteuid())
    && (stat.mode & 0o7777n) === 0o700n;
}

function inspectProtectedRoot(rootPath) {
  let fd = null;
  let accepted = false;
  let identity = null;
  try {
    if (process.platform !== 'linux'
      || typeof process.geteuid !== 'function'
      || typeof rootPath !== 'string'
      || rootPath.length === 0
      || rootPath.includes('\0')
      || !path.isAbsolute(rootPath)
      || path.normalize(rootPath) !== rootPath) {
      throw fixedError('RESIDENT_PROVISIONING_ROOT_REJECTED');
    }
    const before = lstatSync(rootPath, { bigint: true });
    if (realpathSync.native(rootPath) !== rootPath
      || !validProtectedRootDescriptor(before)) {
      throw fixedError('RESIDENT_PROVISIONING_ROOT_REJECTED');
    }
    fd = openSync(rootPath, PROTECTED_ROOT_OPEN_FLAGS);
    const opened = fstatSync(fd, { bigint: true });
    const after = lstatSync(rootPath, { bigint: true });
    if (realpathSync.native(rootPath) !== rootPath
      || !validProtectedRootDescriptor(opened)
      || !validProtectedRootDescriptor(after)
      || !sameDescriptor(before, opened)
      || !sameDescriptor(opened, after)) {
      throw fixedError('RESIDENT_PROVISIONING_ROOT_REJECTED');
    }
    identity = Object.freeze({
      dev: opened.dev,
      ino: opened.ino,
      path: rootPath
    });
    closeSync(fd);
    fd = null;
    accepted = true;
  } catch {
    accepted = false;
  } finally {
    if (fd !== null) {
      try {
        closeSync(fd);
      } catch {
        accepted = false;
      }
    }
  }
  if (!accepted) {
    throw fixedError('RESIDENT_PROVISIONING_ROOT_REJECTED');
  }
  return identity;
}

function validateProvisioningRoots(rootPaths) {
  const identities = rootPaths.map(inspectProtectedRoot);
  for (let left = 0; left < identities.length; left += 1) {
    for (let right = left + 1; right < identities.length; right += 1) {
      if ((identities[left].dev === identities[right].dev
          && identities[left].ino === identities[right].ino)
        || pathsOverlap(identities[left].path, identities[right].path)) {
        throw fixedError('RESIDENT_PROVISIONING_ROOT_REJECTED');
      }
    }
  }
}

function inspectRootPlan(rootPath) {
  try {
    lstatSync(rootPath, { bigint: true });
    return Object.freeze({
      created: false,
      identity: inspectProtectedRoot(rootPath),
      parentIdentity: null,
      rootPath
    });
  } catch (error) {
    if (error?.code !== 'ENOENT') {
      throw fixedError('RESIDENT_PROVISIONING_ROOT_REJECTED');
    }
  }
  return Object.freeze({
    created: true,
    identity: null,
    parentIdentity: inspectProtectedRoot(path.dirname(rootPath)),
    rootPath
  });
}

function sameRootIdentity(left, right) {
  return left.dev === right.dev
    && left.ino === right.ino
    && left.path === right.path;
}

function createProtectedRoot(plan, prepareProtectedRootAt) {
  if (!plan.created) return plan.identity;
  try {
    prepareProtectedRootAt(
      path.dirname(plan.rootPath),
      plan.parentIdentity.dev.toString(10),
      plan.parentIdentity.ino.toString(10),
      path.basename(plan.rootPath)
    );
    const parentAfter = inspectProtectedRoot(path.dirname(plan.rootPath));
    if (!sameRootIdentity(plan.parentIdentity, parentAfter)) {
      throw fixedError('RESIDENT_PROVISIONING_ROOT_REJECTED');
    }
    return inspectProtectedRoot(plan.rootPath);
  } catch {
    throw fixedError('RESIDENT_PROVISIONING_ROOT_REJECTED');
  }
}

function prepareProtectedRoots(
  rootPaths,
  loadNative = () => require('../agents-os-resident.linux-x64-gnu.node')
) {
  const plans = rootPaths.map(inspectRootPlan);
  if (plans.some((plan) => plan.created)) {
    const binding = loadNative();
    if (typeof binding?.prepare_protected_root_at !== 'function') {
      throw fixedError('RESIDENT_PROVISIONING_ROOT_REJECTED');
    }
    plans.forEach((plan) => createProtectedRoot(
      plan,
      binding.prepare_protected_root_at
    ));
  }
  validateProvisioningRoots(rootPaths);
}

function readExactFile(fd, byteLength) {
  const bytes = Buffer.alloc(byteLength);
  let offset = 0;
  while (offset < byteLength) {
    const count = readSync(fd, bytes, offset, byteLength - offset, offset);
    if (count === 0) {
      throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
    }
    offset += count;
  }
  const trailing = Buffer.alloc(1);
  if (readSync(fd, trailing, 0, 1, byteLength) !== 0) {
    trailing.fill(0);
    throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
  }
  trailing.fill(0);
  return bytes;
}

function validTypedToken(value, prefix) {
  return typeof value === 'string'
    && value.startsWith(prefix)
    && Buffer.byteLength(value, 'utf8') > Buffer.byteLength(prefix, 'utf8')
    && Buffer.byteLength(value, 'utf8') <= MAX_AUTHORITY_TOKEN_BYTES
    && value.normalize('NFC') === value
    && !/[\p{C}\p{White_Space}]/u.test(value);
}

function parseCanonicalAuthority(text) {
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
  }
  const actualKeys = isPlainObject(parsed) ? Object.keys(parsed).sort() : [];
  if (actualKeys.length !== AUTHORITY_KEYS.length
    || actualKeys.some((key, index) => key !== AUTHORITY_KEYS[index])
    || parsed.protocol !== GENESIS_PROVISIONING_PROTOCOL
    || parsed.residentId !== LOCAL_OWNER_RESIDENT_ID
    || !validTypedToken(parsed.authorityId, 'authority:')
    || !validTypedToken(parsed.provisioningId, 'provisioning:')) {
    throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
  }
  const canonical = {
    authorityId: parsed.authorityId,
    protocol: parsed.protocol,
    provisioningId: parsed.provisioningId,
    residentId: parsed.residentId
  };
  if (JSON.stringify(canonical) !== text) {
    throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
  }
  return Object.freeze(canonical);
}

function readGenesisAuthorityFile(authorityFilePath) {
  let fd = null;
  let firstBytes = null;
  let secondBytes = null;
  let authority = null;
  let accepted = false;
  try {
    if (process.platform !== 'linux'
      || typeof process.geteuid !== 'function'
      || typeof authorityFilePath !== 'string'
      || authorityFilePath.length === 0
      || authorityFilePath.includes('\0')
      || !path.isAbsolute(authorityFilePath)
      || path.normalize(authorityFilePath) !== authorityFilePath) {
      throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
    }
    const before = lstatSync(authorityFilePath, { bigint: true });
    if (realpathSync.native(authorityFilePath) !== authorityFilePath
      || !validAuthorityDescriptor(before)) {
      throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
    }
    fd = openSync(authorityFilePath, AUTHORITY_OPEN_FLAGS);
    const opened = fstatSync(fd, { bigint: true });
    const linked = lstatSync(authorityFilePath, { bigint: true });
    if (!validAuthorityDescriptor(opened)
      || !validAuthorityDescriptor(linked)
      || !sameDescriptor(before, opened)
      || !sameDescriptor(opened, linked)) {
      throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
    }

    const byteLength = Number(opened.size);
    firstBytes = readExactFile(fd, byteLength);
    const afterFirstRead = fstatSync(fd, { bigint: true });
    secondBytes = readExactFile(fd, byteLength);
    const afterSecondRead = fstatSync(fd, { bigint: true });
    const linkedAfter = lstatSync(authorityFilePath, { bigint: true });
    if (realpathSync.native(authorityFilePath) !== authorityFilePath
      || !validAuthorityDescriptor(linkedAfter)
      || !sameDescriptor(opened, afterFirstRead)
      || !sameDescriptor(afterFirstRead, afterSecondRead)
      || !sameDescriptor(afterSecondRead, linkedAfter)
      || !firstBytes.equals(secondBytes)) {
      throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
    }
    const text = new TextDecoder('utf-8', {
      fatal: true,
      ignoreBOM: true
    }).decode(firstBytes);
    authority = parseCanonicalAuthority(text);
    closeSync(fd);
    fd = null;
    accepted = true;
  } catch {
    accepted = false;
  } finally {
    firstBytes?.fill(0);
    secondBytes?.fill(0);
    if (fd !== null) {
      try {
        closeSync(fd);
      } catch {
        accepted = false;
      }
    }
  }
  if (!accepted) {
    throw fixedError('RESIDENT_PROVISIONING_AUTHORITY_REJECTED');
  }
  return authority;
}

function exitCodeFor(error) {
  if ([
    'RESIDENT_DAEMON_CONFIGURATION_INVALID',
    'RESIDENT_INTEGRITY_MISMATCH',
    'RESIDENT_INTEGRITY_UNAVAILABLE',
    'RESIDENT_PROVISIONING_AUTHORITY_REJECTED',
    'RESIDENT_PROVISIONING_ROOT_REJECTED'
  ].includes(error?.code)) {
    return 64;
  }
  if ([
    'NATIVE_ACTIVATION_FAILED',
    'NATIVE_LIFECYCLE_UNAVAILABLE',
    'RESIDENT_RUNTIME_INACTIVE',
    'RESIDENT_PROVISIONING_FAILED',
    'RESIDENT_SERVER_START_FAILED',
    'RESIDENT_SOCKET_BIND_FAILED',
    'RESIDENT_SOCKET_IN_USE',
    'RESIDENT_SOCKET_UNTRUSTED'
  ].includes(error?.code)) {
    return 73;
  }
  return 70;
}

async function startDaemon({
  argv = process.argv.slice(2),
  verifyIntegrity = verifyCompanionIntegrity,
  createLifecycle = () => createResidentLifecycle(),
  createServer = createCompanionServer
} = {}) {
  const args = parseDaemonArgs(argv);
  if (args.operation !== 'serve') {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  const integrity = verifyIntegrity();
  if (integrity.buildId !== args.expectedBuildId) {
    throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
  }

  const lifecycle = createLifecycle();
  let server;
  let fatal = false;
  const stopForRuntimeFailure = async () => {
    if (fatal) {
      return;
    }
    fatal = true;
    try {
      await server?.stop();
    } finally {
      if (require.main === module) {
        process.exit(70);
      }
    }
  };

  server = createServer({
    socketPath: args.socketPath,
    integrity,
    lifecycle,
    activationConfig: {
      AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION: ACTIVATION_CONFIRMATION,
      AGENTS_OS_RESIDENT_ACTIVATION_MODE: ACTIVATION_MODE,
      AGENTS_OS_RESIDENT_ROOT: args.rootPath,
      ...(args.continuityEvidence !== null
        ? { AGENTS_OS_RESIDENT_CONTINUITY_EVIDENCE: args.continuityEvidence }
        : {}),
      ...(args.genesisProvisioningAuthority !== null
        ? { AGENTS_OS_RESIDENT_GENESIS_PROVISIONING_AUTHORITY: args.genesisProvisioningAuthority }
        : {}),
      ...(args.memoryBodyRootPath !== null
        ? { AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT: args.memoryBodyRootPath }
        : {}),
      ...(args.witnessRootPath !== null
        ? { AGENTS_OS_RESIDENT_WITNESS_ROOT: args.witnessRootPath }
        : {})
    },
    onRuntimeFailure: stopForRuntimeFailure
  });
  await server.start();
  return Object.freeze({
    integrity,
    server,
    shutdown: () => server.stop()
  });
}

async function provisionResident({
  argv = process.argv.slice(2),
  verifyIntegrity = verifyCompanionIntegrity,
  loadNative = () => require('../agents-os-resident.linux-x64-gnu.node'),
  createLifecycle = () => createResidentLifecycle(),
  // Negative-control injection only: this profile must never create a server.
  createServer = createCompanionServer
} = {}) {
  void createServer;
  const args = parseDaemonArgs(argv);
  if (args.operation !== 'provision') {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  const integrity = verifyIntegrity();
  if (integrity.buildId !== args.expectedBuildId) {
    throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
  }
  prepareProtectedRoots([
    args.rootPath,
    args.witnessRootPath,
    args.memoryBodyRootPath
  ], loadNative);
  const genesisProvisioningAuthority = readGenesisAuthorityFile(
    args.authorityFilePath
  );
  try {
    const lifecycle = createLifecycle();
    await lifecycle.initialize({
      AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION: ACTIVATION_CONFIRMATION,
      AGENTS_OS_RESIDENT_ACTIVATION_MODE: ACTIVATION_MODE,
      AGENTS_OS_RESIDENT_GENESIS_PROVISIONING_AUTHORITY:
        genesisProvisioningAuthority,
      AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT: args.memoryBodyRootPath,
      AGENTS_OS_RESIDENT_ROOT: args.rootPath,
      AGENTS_OS_RESIDENT_WITNESS_ROOT: args.witnessRootPath
    });
    await lifecycle.shutdown();
  } catch {
    throw fixedError('RESIDENT_PROVISIONING_FAILED');
  }
  return Object.freeze({
    operation: 'provision',
    result: PROVISIONING_RESULT
  });
}

function prepareResidentRoots({
  argv = process.argv.slice(2),
  verifyIntegrity = verifyCompanionIntegrity,
  loadNative = () => require('../agents-os-resident.linux-x64-gnu.node')
} = {}) {
  const args = parseDaemonArgs(argv);
  if (args.operation !== 'prepare-roots') {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  const integrity = verifyIntegrity();
  if (integrity.buildId !== args.expectedBuildId) {
    throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
  }
  prepareProtectedRoots([
    args.rootPath,
    args.witnessRootPath,
    args.memoryBodyRootPath
  ], loadNative);
  return Object.freeze({
    operation: 'prepare-roots',
    result: PREPARE_ROOTS_RESULT
  });
}

async function main() {
  const argv = process.argv.slice(2);
  let requested;
  try {
    requested = parseDaemonArgs(argv);
  } catch (error) {
    process.exit(exitCodeFor(error));
    return;
  }

  if (requested.operation === 'provision') {
    try {
      await provisionResident({ argv });
      process.stdout.write(`${PROVISIONING_RESULT}\n`);
    } catch (error) {
      process.exit(exitCodeFor(error));
    }
    return;
  }

  if (requested.operation === 'prepare-roots') {
    try {
      const result = prepareResidentRoots({ argv });
      process.stdout.write(`${result.result}\n`);
    } catch (error) {
      process.exit(exitCodeFor(error));
    }
    return;
  }

  let controller = null;
  let stopping = false;

  const shutdownAndExit = async (exitCode) => {
    if (stopping) {
      return;
    }
    stopping = true;
    try {
      await controller?.shutdown();
    } catch {
      if (exitCode === 0) {
        exitCode = 70;
      }
    }
    process.exit(exitCode);
  };

  process.once('SIGTERM', () => {
    void shutdownAndExit(0);
  });
  process.once('SIGINT', () => {
    void shutdownAndExit(0);
  });
  process.once('uncaughtException', () => {
    void shutdownAndExit(70);
  });
  process.once('unhandledRejection', () => {
    void shutdownAndExit(70);
  });

  try {
    controller = await startDaemon({ argv });
  } catch (error) {
    process.exit(exitCodeFor(error));
  }
}

if (require.main === module) {
  void main();
}

module.exports = Object.freeze({
  exitCodeFor,
  main,
  parseDaemonArgs,
  prepareResidentRoots,
  provisionResident,
  startDaemon
});
