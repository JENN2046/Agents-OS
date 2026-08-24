'use strict';

const path = require('node:path');

const { createCompanionClient } = require('./client');
const { resolveDefaultSocketPath } = require('./constants');
const { verifyCompanionIntegrity } = require('./integrity');

const CATEGORY_BY_CODE = Object.freeze({
  RESIDENT_BUILD_MISMATCH: 'RESIDENT_PROBE_BUILD_MISMATCH',
  RESIDENT_COMPANION_UNAVAILABLE: 'RESIDENT_PROBE_UNAVAILABLE',
  RESIDENT_INTEGRITY_MISMATCH: 'RESIDENT_PROBE_INTEGRITY_MISMATCH',
  RESIDENT_INTEGRITY_UNAVAILABLE: 'RESIDENT_PROBE_INTEGRITY_UNAVAILABLE',
  RESIDENT_PROTOCOL_REJECTED: 'RESIDENT_PROBE_PROTOCOL_REJECTED',
  RESIDENT_RUNTIME_DIR_UNAVAILABLE: 'RESIDENT_PROBE_UNAVAILABLE',
  RESIDENT_RUNTIME_INACTIVE: 'RESIDENT_PROBE_RUNTIME_INACTIVE',
  RESIDENT_SOCKET_UNTRUSTED: 'RESIDENT_PROBE_SOCKET_UNTRUSTED'
});

function parseProbeArgs(argv) {
  if (argv.length === 0) {
    return Object.freeze({ socketPath: resolveDefaultSocketPath() });
  }
  if (argv.length !== 2
    || argv[0] !== '--socket'
    || typeof argv[1] !== 'string'
    || !path.isAbsolute(argv[1])
    || path.normalize(argv[1]) !== argv[1]) {
    const error = new Error('RESIDENT_PROBE_ARGUMENTS_INVALID');
    error.code = 'RESIDENT_PROBE_ARGUMENTS_INVALID';
    throw error;
  }
  return Object.freeze({ socketPath: argv[1] });
}

async function runProbe({
  argv = process.argv.slice(2),
  verifyIntegrity = verifyCompanionIntegrity,
  createClient = (options) => createCompanionClient(options)
} = {}) {
  try {
    const { socketPath } = parseProbeArgs(argv);
    const integrity = verifyIntegrity();
    const client = createClient({ socketPath, integrity });
    const response = await client.status();
    if (response.activationState !== 'ACTIVE_LOCAL_OWNER'
      || response.runtimeUsable !== false
      || response.localGoalTaskUsable !== true
      || response.commandChannelEnabled !== true
      || response.authenticationAssurance !== 'LOCAL_OWNER_SESSION_ONLY') {
      return 'RESIDENT_PROBE_RUNTIME_INACTIVE';
    }
    return 'RESIDENT_PROBE_ACTIVE';
  } catch (error) {
    return CATEGORY_BY_CODE[error?.code] ?? 'RESIDENT_PROBE_FAILED';
  }
}

async function main() {
  const category = await runProbe();
  process.stdout.write(`${category}\n`);
  process.exit(category === 'RESIDENT_PROBE_ACTIVE' ? 0 : 1);
}

if (require.main === module) {
  void main();
}

module.exports = Object.freeze({
  parseProbeArgs,
  runProbe
});
