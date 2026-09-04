'use strict';

const {
  connectedPeerCredentials
} = require('../../companion/daemon-peer-auth');

// Disposable fixtures run under the test UID, outside the installed daemon's
// root-owned policy. Still identify the connected peer through the real kernel
// credential helper; a fixture PID claim alone never establishes identity.
function authenticateFixtureDaemon(socket, _socketPath, { expectedPid = process.pid } = {}) {
  const peer = connectedPeerCredentials(socket);
  if (!Number.isSafeInteger(expectedPid)
    || expectedPid < 1
    || peer.pid !== expectedPid
    || peer.uid !== process.getuid()) {
    const error = new Error('RESIDENT_DAEMON_IDENTITY_REJECTED');
    error.code = 'RESIDENT_DAEMON_IDENTITY_REJECTED';
    throw error;
  }
  return Object.freeze(peer);
}

module.exports = Object.freeze({ authenticateFixtureDaemon });
