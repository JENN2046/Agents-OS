'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const net = require('node:net');
const path = require('node:path');
const { tmpdir } = require('node:os');
const test = require('node:test');
const { createCompanionClient } = require('../companion/client');
const { authenticateConnectedDaemon, connectedPeerCredentials,
  parsePeerCredentials } = require('../companion/daemon-peer-auth');
const { parseIdentityPolicy, requirePolicyRole, requireRootOwnedPath,
  requireProtectedStatePath, SOCKET_PATH } = require('../companion/daemon-identity-policy');
const { authenticateFixtureDaemon } = require('./fixtures/transport-identity.cjs');
const { createCompanionServer } = require('../companion/server');

const INTEGRITY = Object.freeze({ buildId: `sha256:${'e'.repeat(64)}`,
  packageVersion: '0.3.0-local-owner.0' });
const POLICY = Object.freeze({
  schema: 'agents-os-resident.daemon-identity.v1',
  daemonUid: process.getuid() + 10000, clientUid: process.getuid(),
  socketGid: process.getgid(), packageRoot: path.resolve(__dirname, '..'),
  nodeBinary: process.execPath, buildId: INTEGRITY.buildId
});

async function socketFixture(t) {
  const root = fs.mkdtempSync(path.join(tmpdir(), 'resident-peer-auth-'));
  fs.chmodSync(root, 0o700);
  const socketPath = path.join(root, 'control.sock');
  const accepted = new Set();
  let received = 0;
  const server = net.createServer((socket) => {
    accepted.add(socket);
    socket.on('error', () => {});
    socket.on('data', (chunk) => { received += chunk.length; });
    socket.on('close', () => accepted.delete(socket));
  });
  let client;
  t.after(async () => {
    client?.destroy();
    for (const socket of accepted) socket.destroy();
    await new Promise((resolve) => server.close(resolve));
    fs.rmSync(root, { recursive: true, force: true });
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject); server.listen(socketPath, resolve);
  });
  fs.chmodSync(socketPath, 0o600);
  client = net.createConnection({ path: socketPath });
  await new Promise((resolve, reject) => {
    client.once('connect', resolve); client.once('error', reject);
  });
  return { root, socketPath, client, received: () => received };
}

test('identity policy requires distinct non-root principals and exact schema', () => {
  assert.deepEqual(parseIdentityPolicy(Buffer.from(JSON.stringify(POLICY))), POLICY);
  for (const delta of [
    { daemonUid: POLICY.clientUid }, { daemonUid: 0 }, { clientUid: 0 },
    { socketGid: -1 }, { daemonUid: 0xffffffff }, { clientUid: 1.2 },
    { packageRoot: '/opt/../home/untrusted' }, { nodeBinary: 'node' },
    { buildId: 'wrong' }, { MainPID: 123 }, { secret: 'unused' }
  ]) {
    assert.throws(() => parseIdentityPolicy(Buffer.from(JSON.stringify({
      ...POLICY, ...delta
    }))), /RESIDENT_DAEMON_IDENTITY_UNTRUSTED/);
  }
  assert.throws(() => parseIdentityPolicy(Buffer.alloc(8193)), /UNTRUSTED/);
  assert.throws(() => requirePolicyRole(POLICY, 'daemon'), /UNTRUSTED/);
  requirePolicyRole(POLICY, 'client');
});

test('root-owned leaf cannot launder writable, symlink, or host-owned ancestors', () => {
  const target = '/etc/agents-os-resident/daemon-identity.json';
  const base = (name) => ({ uid: 0, mode: name === target ? 0o644 : 0o755,
    nlink: 1, isDirectory: () => name !== target,
    isFile: () => name === target, isSymbolicLink: () => false });
  requireRootOwnedPath(target, 'file', { stat: base });
  for (const name of ['/', '/etc', '/etc/agents-os-resident', target]) {
    for (const delta of [{ uid: POLICY.clientUid }, { mode: 0o775 },
      { mode: 0o777 }, { isSymbolicLink: () => true }]) {
      assert.throws(() => requireRootOwnedPath(target, 'file', {
        stat: (queried) => ({ ...base(queried), ...(queried === name ? delta : {}) })
      }), /RESIDENT_DAEMON_IDENTITY_UNTRUSTED/);
    }
  }
  assert.throws(() => requireRootOwnedPath(target, 'file', {
    stat: (name) => ({ ...base(name), ...(name === target ? { nlink: 2 } : {}) })
  }), /UNTRUSTED/);
});

test('actual host-writable checkout is rejected as an installation trust anchor', () => {
  assert.throws(() => requireRootOwnedPath(POLICY.packageRoot, 'directory'), /UNTRUSTED/);
});

test('protected daemon-owned roots reject host-controlled ancestor directories', () => {
  const root = '/var/lib/resident/private-root';
  const metadata = (name) => ({
    uid: name === root ? POLICY.daemonUid : 0,
    mode: name === root ? 0o700 : 0o755,
    isDirectory: () => true, isSymbolicLink: () => false
  });
  requireProtectedStatePath(root, POLICY.daemonUid, { stat: metadata });
  for (const delta of [{ uid: POLICY.clientUid }, { mode: 0o777 },
    { mode: 0o775 }, { isSymbolicLink: () => true }]) {
    assert.throws(() => requireProtectedStatePath(root, POLICY.daemonUid, {
      stat: (name) => ({ ...metadata(name), ...(name === '/var/lib/resident' ? delta : {}) })
    }), /IDENTITY_UNTRUSTED/);
  }
});

test('peer credential parser rejects unbounded and invalid output', () => {
  assert.deepEqual(parsePeerCredentials('{"pid":123,"uid":456,"gid":789}\n'),
    { pid: 123, uid: 456, gid: 789 });
  for (const value of ['', 'null', '[]', 'x'.repeat(129),
    '{"pid":0,"uid":456,"gid":789}', '{"pid":123,"uid":-1,"gid":789}',
    '{"pid":123,"uid":456,"gid":789,"trusted":true}']) {
    assert.throws(() => parsePeerCredentials(value), /IDENTITY_UNAVAILABLE/);
  }
});

test('native helper identifies a real connected Unix peer without external tools', async (t) => {
  const { client } = await socketFixture(t);
  assert.deepEqual(connectedPeerCredentials(client), {
    pid: process.pid, uid: process.getuid(), gid: process.getgid()
  });
  // The process environment is replaced; no PATH, loader, Node or D-Bus input.
  connectedPeerCredentials(client, { execute(executable, args, options) {
    assert.equal(path.basename(executable), 'resident-peer-credentials');
    assert.deepEqual(args, []);
    assert.deepEqual(options.env, { LANG: 'C', LC_ALL: 'C' });
    assert.deepEqual(options.stdio, [client._handle.fd, 'pipe', 'pipe']);
    return '{"pid":123,"uid":456,"gid":789}';
  } });
});

test('connection identity survives pathname replacement', async (t) => {
  const { client, socketPath, root } = await socketFixture(t);
  fs.renameSync(socketPath, path.join(root, 'old.sock'));
  fs.writeFileSync(socketPath, 'untrusted replacement');
  assert.equal(connectedPeerCredentials(client).pid, process.pid);
});

test('same-UID peer fails even if an attacker controls the claimed MainPID', async (t) => {
  const { client } = await socketFixture(t);
  assert.throws(() => authenticateConnectedDaemon(client, SOCKET_PATH, {
    policy: POLICY, expectedPid: process.pid,
    // An obsolete option must never become authority again.
    resolveExpectedPid: () => process.pid
  }), /RESIDENT_DAEMON_IDENTITY_REJECTED/);
});

test('only enrolled distinct credentials pass; attachment PID remains pinned', () => {
  const peer = { pid: 7123, uid: POLICY.daemonUid, gid: POLICY.socketGid };
  const authenticate = (value, expectedPid) => authenticateConnectedDaemon({}, SOCKET_PATH, {
    policy: POLICY, expectedPid, resolvePeerCredentials: () => value
  });
  assert.deepEqual(authenticate(peer), peer);
  assert.deepEqual(authenticate(peer, 7123), peer);
  for (const value of [{ ...peer, uid: POLICY.clientUid },
    { ...peer, uid: peer.uid + 1 }, { ...peer, gid: peer.gid + 1 },
    { ...peer, pid: 0 }]) {
    assert.throws(() => authenticate(value), /IDENTITY_REJECTED/);
  }
  assert.throws(() => authenticate(peer, 7999), /IDENTITY_REJECTED/);
});

test('missing helper and invalid descriptor fail closed', async (t) => {
  const { client, root } = await socketFixture(t);
  assert.throws(() => connectedPeerCredentials(client, {
    helperPath: path.join(root, 'absent-helper')
  }), /RESIDENT_DAEMON_IDENTITY_UNAVAILABLE/);
  assert.throws(() => connectedPeerCredentials({}), /IDENTITY_UNAVAILABLE/);
});

test('a same-UID impersonator receives no attach or status request bytes', async (t) => {
  const fixture = await socketFixture(t);
  const client = createCompanionClient({
    socketPath: fixture.socketPath, integrity: INTEGRITY,
    // Only bypass installation filesystem setup; use real kernel credentials.
    loadIdentityPolicy: () => null,
    authenticateDaemon(socket) {
      return authenticateConnectedDaemon(socket, SOCKET_PATH, { policy: POLICY });
    }
  });
  await assert.rejects(client.attach(), /RESIDENT_DAEMON_IDENTITY_REJECTED/);
  await assert.rejects(client.status(), /RESIDENT_DAEMON_IDENTITY_REJECTED/);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(fixture.received(), 0);
});

test('client authenticates attach, status, and protected exchanges', async (t) => {
  const root = fs.mkdtempSync(path.join(tmpdir(), 'resident-auth-exchanges-'));
  fs.chmodSync(root, 0o700);
  const socketPath = path.join(root, 'control.sock');
  const active = { activationState: 'ACTIVE_LOCAL_OWNER', runtimeUsable: false,
    localGoalTaskUsable: true, commandChannelEnabled: true,
    commandChannelMode: 'LOCAL_GOAL_TASK_V1', ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
    authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY', providerEnabled: false,
    memoryEnabled: false, externalEffectsEnabled: false };
  const calls = [];
  const lifecycle = { initialize: async () => active, status: async () => active,
    prepareProposal: async () => ({}), submitConsent: async () => ({}),
    query: async () => ({}), queryMmrMutationCore: async () => ({}),
    queryPresenceContext: async () => ({}), sealProviderAttempt: async () => ({}),
    invalidate: async () => ({}), shutdown: async () => ({}) };
  const server = createCompanionServer({ socketPath, integrity: INTEGRITY,
    lifecycle, activationConfig: {} });
  const client = createCompanionClient({ socketPath, integrity: INTEGRITY,
    loadIdentityPolicy: () => null,
    authenticateDaemon(socket, connectedPath, options) {
      calls.push(options.expectedPid);
      return authenticateFixtureDaemon(socket, connectedPath, options);
    }
  });
  t.after(async () => {
    client.detach(); await server.stop(); fs.rmSync(root, { recursive: true, force: true });
  });
  await server.start();
  await client.attach(); await client.status();
  await client.query({ operation: 'QUERY_GOALS', query: { mode: 'LIST' } });
  assert.deepEqual(calls, [undefined, undefined, process.pid]);
});

test('unsolicited response during pending authentication fails before any request bytes', async (t) => {
  const root = fs.mkdtempSync(path.join(tmpdir(), 'resident-early-response-'));
  fs.chmodSync(root, 0o700);
  const socketPath = path.join(root, 'control.sock');
  let received = 0;
  const server = net.createServer((socket) => {
    socket.on('error', () => {});
    socket.on('data', (bytes) => { received += bytes.length; });
    socket.write('untrusted early response\n');
  });
  t.after(async () => {
    await new Promise((resolve) => server.close(resolve));
    fs.rmSync(root, { recursive: true, force: true });
  });
  await new Promise((resolve) => server.listen(socketPath, resolve));
  fs.chmodSync(socketPath, 0o600);
  let finishAuthentication;
  const pending = new Promise((resolve) => { finishAuthentication = resolve; });
  const client = createCompanionClient({ socketPath, integrity: INTEGRITY,
    loadIdentityPolicy: () => null, authenticateDaemon: () => pending });
  await assert.rejects(client.attach(), /RESIDENT_DAEMON_IDENTITY_REJECTED/);
  finishAuthentication({ pid: process.pid });
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(received, 0);
});
