'use strict';

const { createCompanionClient } = require('../../companion/client');
const { runProbe } = require('../../companion/probe');
const { authenticateFixtureDaemon } = require('./transport-identity.cjs');

const expectedPid = Number(process.env.AGENTS_OS_RESIDENT_TEST_DAEMON_PID);
if (!Number.isSafeInteger(expectedPid) || expectedPid < 1) {
  throw new Error('TEST_DAEMON_PID_REQUIRED');
}

// Exercise the real probe against a disposable same-UID transport fixture.
void runProbe({
  createClient: (options) => createCompanionClient({
    ...options,
    loadIdentityPolicy: () => null,
    authenticateDaemon: (socket, socketPath) => authenticateFixtureDaemon(
      socket, socketPath, { expectedPid }
    )
  })
}).then((category) => {
  process.stdout.write(`${category}\n`);
  process.exitCode = category === 'RESIDENT_PROBE_ACTIVE' ? 0 : 1;
});
