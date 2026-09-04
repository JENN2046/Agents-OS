'use strict';

const assert = require('node:assert/strict');
const {
  chmodSync,
  mkdtempSync,
  rmSync
} = require('node:fs');
const net = require('node:net');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { createCompanionClient } = require('../companion/client');
const {
  authenticateConnectedDaemon,
  connectedPeerPid,
  parseSystemdMainPid,
  peerPidFromSs,
  systemdMainPid
} = require('../companion/daemon-peer-auth');
const { createCompanionServer } = require('../companion/server');

const INTEGRITY = Object.freeze({
  buildId: `sha256:${'e'.repeat(64)}`,
  packageVersion: '0.3.0-local-owner.0'
});

function temporarySocket() {
  const root = mkdtempSync(path.join(tmpdir(), 'resident-peer-auth-'));
  chmodSync(root, 0o700);
  return { root, socketPath: path.join(root, 'control.sock') };
}

function activeProjection() {
  return {
    activationState: 'ACTIVE_LOCAL_OWNER',
    runtimeUsable: false,
    localGoalTaskUsable: true,
    commandChannelEnabled: true,
    commandChannelMode: 'LOCAL_GOAL_TASK_V1',
    ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
    authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY',
    providerEnabled: false,
    memoryEnabled: false,
    externalEffectsEnabled: false
  };
}

function lifecycleDouble() {
  const calls = [];
  return {
    calls,
    async initialize() { return activeProjection(); },
    async status() { return activeProjection(); },
    async prepareProposal() { return {}; },
    async submitConsent() { return {}; },
    async query() { calls.push('query'); return {}; },
    async queryMmrMutationCore() { return {}; },
    async queryPresenceContext(input) { return input; },
    async sealProviderAttempt(input) { return input; },
    async invalidate() { return {}; },
    async shutdown() { return {}; }
  };
}

test('systemd identity parsing is property-name bound and fail closed', () => {
  assert.equal(parseSystemdMainPid([
    'SubState=running',
    'MainPID=4123',
    'ActiveState=active'
  ].join('\n')), 4123);
  for (const output of [
    'MainPID=4123\nActiveState=inactive\nSubState=dead\n',
    'MainPID=0\nActiveState=active\nSubState=running\n',
    'MainPID=4123\nMainPID=4123\nActiveState=active\nSubState=running\n',
    '4123\nactive\nrunning\n'
  ]) {
    assert.throws(
      () => parseSystemdMainPid(output),
      /RESIDENT_DAEMON_IDENTITY_UNAVAILABLE/u
    );
  }
});

test('systemd identity lookup uses the exact unit and strips loader injection', () => {
  const prior = process.env.LD_PRELOAD;
  process.env.LD_PRELOAD = '/untrusted/preload.so';
  try {
    const pid = systemdMainPid({
      execute(executable, args, options) {
        assert.equal(executable, '/usr/bin/systemctl');
        assert.deepEqual(args, [
          '--user',
          'show',
          'agents-os-resident.service',
          '--property=MainPID',
          '--property=ActiveState',
          '--property=SubState',
          '--no-pager'
        ]);
        assert.equal(options.env.LD_PRELOAD, undefined);
        return 'MainPID=4123\nActiveState=active\nSubState=running\n';
      }
    });
    assert.equal(pid, 4123);
  } finally {
    if (prior === undefined) delete process.env.LD_PRELOAD;
    else process.env.LD_PRELOAD = prior;
  }
});

test('ss identity parsing selects only the connected client inode', () => {
  const output = [
    'u_str ESTAB 0 0 /run/user/1000/agents-os-resident/control.sock 111 * 222 users:(("node",pid=4123,fd=9))',
    'u_str ESTAB 0 0 /run/user/1000/agents-os-resident/control.sock 333 * 444 users:(("node",pid=4999,fd=8))'
  ].join('\n');
  assert.equal(peerPidFromSs(output, '222'), 4123);
  assert.throws(
    () => peerPidFromSs(`${output}\n${output.split('\n')[0]}`, '222'),
    /RESIDENT_DAEMON_IDENTITY_UNAVAILABLE/u
  );
  assert.throws(
    () => peerPidFromSs(output, '999'),
    /RESIDENT_DAEMON_IDENTITY_UNAVAILABLE/u
  );
});

test('kernel Unix peer identity accepts the bound daemon and rejects an impostor PID', async (t) => {
  const temporary = temporarySocket();
  let socket = null;
  const server = net.createServer((socket) => socket.on('error', () => {}));
  t.after(async () => {
    socket?.destroy();
    await new Promise((resolve) => server.close(resolve));
    rmSync(temporary.root, { recursive: true, force: true });
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(temporary.socketPath, resolve);
  });
  socket = net.createConnection({ path: temporary.socketPath });
  await new Promise((resolve, reject) => {
    socket.once('connect', resolve);
    socket.once('error', reject);
  });
  assert.equal(connectedPeerPid(socket, temporary.socketPath), process.pid);
  assert.equal(authenticateConnectedDaemon(socket, temporary.socketPath, {
    expectedPid: process.pid,
    resolveExpectedPid: () => process.pid
  }).pid, process.pid);
  assert.throws(
    () => authenticateConnectedDaemon(socket, temporary.socketPath, {
      expectedPid: process.pid + 1,
      resolveExpectedPid: () => process.pid + 1
    }),
    /RESIDENT_DAEMON_IDENTITY_REJECTED/u
  );
});

test('client authenticates attach and every protected exchange against one daemon PID', async (t) => {
  const temporary = temporarySocket();
  const lifecycle = lifecycleDouble();
  const server = createCompanionServer({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY,
    lifecycle,
    activationConfig: {}
  });
  const checks = [];
  t.after(async () => {
    await server.stop();
    rmSync(temporary.root, { recursive: true, force: true });
  });
  await server.start();
  const client = createCompanionClient({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY,
    authenticateDaemon(_socket, _socketPath, { expectedPid }) {
      checks.push(expectedPid);
      return Object.freeze({ pid: expectedPid ?? 7123 });
    }
  });
  await client.attach();
  await client.query({ operation: 'QUERY_GOALS', query: { mode: 'LIST' } });
  assert.deepEqual(checks, [undefined, 7123]);
  client.detach();
});

test('a protected exchange requires the pinned PID to remain the current systemd MainPID', () => {
  const calls = [];
  assert.throws(() => authenticateConnectedDaemon({}, '/run/user/1000/agents-os-resident/control.sock', {
    expectedPid: 7123,
    resolvePeerPid() {
      calls.push('peer');
      return 7123;
    },
    resolveExpectedPid() {
      calls.push('systemd');
      return 7999;
    }
  }), /RESIDENT_DAEMON_IDENTITY_REJECTED/u);
  assert.deepEqual(calls, ['peer', 'systemd']);
});

test('a changed current MainPID rejects a protected request before daemon dispatch', async (t) => {
  const temporary = temporarySocket();
  const lifecycle = lifecycleDouble();
  const server = createCompanionServer({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY,
    lifecycle,
    activationConfig: {}
  });
  let activeMainPid = process.pid;
  t.after(async () => {
    await server.stop();
    rmSync(temporary.root, { recursive: true, force: true });
  });
  await server.start();
  const client = createCompanionClient({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY,
    authenticateDaemon(socket, connectedPath, { expectedPid } = {}) {
      return authenticateConnectedDaemon(socket, connectedPath, {
        expectedPid,
        resolveExpectedPid: () => activeMainPid
      });
    }
  });
  await client.attach();
  activeMainPid = process.pid + 1;
  await assert.rejects(
    client.query({ operation: 'QUERY_GOALS', query: { mode: 'LIST' } }),
    /RESIDENT_DAEMON_IDENTITY_REJECTED/u
  );
  assert.deepEqual(lifecycle.calls, []);
  client.detach();
});

test('an unbound same-UID socket receives no attach request bytes', async (t) => {
  const temporary = temporarySocket();
  let receivedBytes = 0;
  const server = net.createServer((socket) => {
    socket.on('data', (chunk) => { receivedBytes += chunk.length; });
  });
  t.after(async () => {
    await new Promise((resolve) => server.close(resolve));
    rmSync(temporary.root, { recursive: true, force: true });
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(temporary.socketPath, () => {
      chmodSync(temporary.socketPath, 0o600);
      resolve();
    });
  });
  const client = createCompanionClient({
    socketPath: temporary.socketPath,
    integrity: INTEGRITY,
    authenticateDaemon(socket, connectedPath) {
      return authenticateConnectedDaemon(socket, connectedPath, {
        expectedPid: process.pid + 1,
        resolveExpectedPid: () => process.pid + 1
      });
    }
  });
  await assert.rejects(
    client.attach(),
    /RESIDENT_DAEMON_IDENTITY_REJECTED/u
  );
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(receivedBytes, 0);
});
