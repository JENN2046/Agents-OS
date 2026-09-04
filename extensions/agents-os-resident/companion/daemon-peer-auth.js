'use strict';

const { execFileSync } = require('node:child_process');
const path = require('node:path');
const { fixedError } = require('./constants');
const { HELPER_NAME, SOCKET_PATH, loadDaemonIdentityPolicy,
  requirePolicyRole } = require('./daemon-identity-policy');

function parsePeerCredentials(output) {
  let value;
  try {
    if (typeof output !== 'string' || output.length > 128) throw new Error();
    value = JSON.parse(output);
    if (!value || typeof value !== 'object' || Array.isArray(value)
      || Object.keys(value).sort().join(',') !== 'gid,pid,uid'
      || !Number.isSafeInteger(value.pid) || value.pid < 1
      || ![value.uid, value.gid].every((id) => Number.isSafeInteger(id)
        && id >= 0 && id < 0xffffffff)) throw new Error();
  } catch { throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE'); }
  return Object.freeze(value);
}

// The helper queries SO_PEERCRED on the inherited connected socket. No
// pathname re-resolution, process-table snapshot or ambient tool lookup.
function connectedPeerCredentials(socket, {
  helperPath = path.resolve(__dirname, '..', HELPER_NAME),
  execute = execFileSync
} = {}) {
  const descriptor = socket?._handle?.fd;
  if (!Number.isSafeInteger(descriptor) || descriptor < 0) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
  try {
    return parsePeerCredentials(execute(helperPath, [], {
      encoding: 'utf8', env: { LANG: 'C', LC_ALL: 'C' },
      stdio: [descriptor, 'pipe', 'pipe'], maxBuffer: 128, timeout: 1000
    }));
  } catch { throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE'); }
}

function authenticateConnectedDaemon(socket, socketPath, {
  expectedPid,
  policy = loadDaemonIdentityPolicy(),
  resolvePeerCredentials = connectedPeerCredentials
} = {}) {
  requirePolicyRole(policy, 'client');
  if (socketPath !== SOCKET_PATH) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_REJECTED');
  }
  const peer = resolvePeerCredentials(socket, {
    helperPath: path.join(policy.packageRoot, HELPER_NAME)
  });
  if (!Number.isSafeInteger(peer?.pid) || peer.pid < 1
    || peer.uid !== policy.daemonUid || peer.uid === process.getuid()
    || peer.gid !== policy.socketGid
    || (expectedPid !== undefined && peer.pid !== expectedPid)) {
    throw fixedError('RESIDENT_DAEMON_IDENTITY_REJECTED');
  }
  return peer;
}

function authenticateConnectedClient(socket, policy) {
  requirePolicyRole(policy, 'daemon');
  const peer = connectedPeerCredentials(socket, {
    helperPath: path.join(policy.packageRoot, HELPER_NAME)
  });
  if (peer.uid !== policy.clientUid || peer.uid === process.getuid()) {
    throw fixedError('RESIDENT_CLIENT_IDENTITY_REJECTED');
  }
  return peer;
}

module.exports = Object.freeze({
  authenticateConnectedClient, authenticateConnectedDaemon,
  connectedPeerCredentials, parsePeerCredentials
});
