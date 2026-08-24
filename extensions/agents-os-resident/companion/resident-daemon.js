'use strict';

const path = require('node:path');

const { createResidentLifecycle } = require('../activation');
const {
  ACTIVATION_CONFIRMATION,
  ACTIVATION_MODE,
  fixedError
} = require('./constants');
const { verifyCompanionIntegrity } = require('./integrity');
const { createCompanionServer } = require('./server');

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

function parseDaemonArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (![
      '--continuity-evidence',
      '--expected-build-id',
      '--genesis-provisioning-authority',
      '--root',
      '--socket'
    ].includes(key)
      || typeof value !== 'string'
      || value.length === 0
      || value.includes('\0')
      || Object.hasOwn(result, key)) {
      throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
    }
    result[key] = value;
  }
  if (!['--expected-build-id', '--root', '--socket'].every((key) => Object.hasOwn(result, key))
    || !path.isAbsolute(result['--root'])
    || path.normalize(result['--root']) !== result['--root']
    || !path.isAbsolute(result['--socket'])
    || path.normalize(result['--socket']) !== result['--socket']
    || !/^sha256:[0-9a-f]{64}$/.test(result['--expected-build-id'])) {
    throw fixedError('RESIDENT_DAEMON_CONFIGURATION_INVALID');
  }
  return Object.freeze({
    continuityEvidence: parseOptionalJson(result, '--continuity-evidence'),
    expectedBuildId: result['--expected-build-id'],
    genesisProvisioningAuthority: parseOptionalJson(
      result,
      '--genesis-provisioning-authority'
    ),
    rootPath: result['--root'],
    socketPath: result['--socket']
  });
}

function exitCodeFor(error) {
  if ([
    'RESIDENT_DAEMON_CONFIGURATION_INVALID',
    'RESIDENT_INTEGRITY_MISMATCH',
    'RESIDENT_INTEGRITY_UNAVAILABLE'
  ].includes(error?.code)) {
    return 64;
  }
  if ([
    'NATIVE_ACTIVATION_FAILED',
    'NATIVE_LIFECYCLE_UNAVAILABLE',
    'RESIDENT_RUNTIME_INACTIVE',
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

async function main() {
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
    controller = await startDaemon();
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
  startDaemon
});
