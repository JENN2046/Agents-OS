'use strict';

// Runs exclusively inside the disposable Docker test. Never run on a host:
// the root orchestrator prepares synthetic root-owned public installation data.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const net = require('node:net');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const PACKAGE = '/opt/resident';
const SOCKET = '/run/agents-os-resident/control.sock';
const POLICY = '/etc/agents-os-resident/daemon-identity.json';
const DAEMON_UID = 2001;
const CLIENT_UID = 2002;
const GID = 2002;
const mode = process.argv[2];
const active = Object.freeze({ activationState: 'ACTIVE_LOCAL_OWNER',
  runtimeUsable: false, localGoalTaskUsable: true, commandChannelEnabled: true,
  commandChannelMode: 'LOCAL_GOAL_TASK_V1', ownerConsentMode: 'SPOKEN_CHALLENGE_V1',
  authenticationAssurance: 'LOCAL_OWNER_SESSION_ONLY', providerEnabled: false,
  memoryEnabled: false, externalEffectsEnabled: false });
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
function send(value) { process.send(value); }
function moduleAt(name) { return require(`${PACKAGE}/companion/${name}`); }

async function daemon() {
  const { loadDaemonIdentityPolicy } = moduleAt('daemon-identity-policy');
  const identityPolicy = loadDaemonIdentityPolicy({ role: 'daemon' });
  const integrity = moduleAt('integrity').verifyCompanionIntegrity();
  let statusCalls = 0;
  let queryCalls = 0;
  const lifecycle = {
    initialize: async () => active,
    status: async () => { statusCalls += 1; return active; },
    query: async () => { queryCalls += 1; return { fixtureQuery: true }; },
    shutdown: async () => ({}), prepareProposal: async () => ({}),
    submitConsent: async () => ({}), queryMmrMutationCore: async () => ({}),
    queryPresenceContext: async () => ({}), sealProviderAttempt: async () => ({}),
    invalidate: async () => ({})
  };
  const server = moduleAt('server').createCompanionServer({
    socketPath: SOCKET, identityPolicy, integrity, lifecycle,
    activationConfig: {}, healthIntervalMs: 600000
  });
  process.on('message', async (command) => {
    if (command === 'counts') send({ statusCalls, queryCalls });
    if (command === 'stop') {
      await server.stop(); send({ stopped: true }); process.disconnect();
    }
  });
  await server.start();
  send({ ready: true });
}

async function client() {
  // No injected policy loader, peer resolver, socket path or integrity result.
  const connection = moduleAt('client').createCompanionClient();
  try {
    const attach = await connection.attach();
    assert.equal(attach.daemonIdentity.uid, DAEMON_UID);
    assert.equal(attach.daemonIdentity.gid, GID);
    const status = await connection.status();
    assert.equal(status.buildId, attach.response.buildId);
    const query = await connection.query({ operation: 'QUERY_GOALS', query: { mode: 'LIST' } });
    assert.deepEqual(query, { fixtureQuery: true });
    send({ positiveExchanges: 3 });
  } finally { connection.detach(); }
}

async function wrongClient() {
  // Deliberately bypass client-side admission to exercise daemon admission.
  // GID allows connecting, but the real peer UID is unregistered.
  const policy = JSON.parse(fs.readFileSync(POLICY, 'utf8'));
  const socket = net.createConnection(SOCKET);
  let receivedBytes = 0;
  await new Promise((resolve, reject) => {
    socket.on('error', (error) => {
      if (!['ECONNRESET', 'EPIPE'].includes(error.code)) reject(error);
    });
    socket.on('data', (bytes) => { receivedBytes += bytes.length; });
    socket.once('connect', () => socket.write(moduleAt('protocol').encodeFrame({
      schema: moduleAt('constants').PROTOCOL_SCHEMA,
      operation: 'status', requestId: 'a'.repeat(32), expectedBuildId: policy.buildId
    })));
    socket.once('close', resolve);
    socket.setTimeout(3000, () => { socket.destroy(); reject(new Error('wrong UID not rejected')); });
  });
  assert.equal(receivedBytes, 0);
  send({ rejected: true });
}

async function rewriteAttempts() {
  let denied = 0;
  const paths = [POLICY, `${PACKAGE}/resident-peer-credentials`,
    `${PACKAGE}/systemd/agents-os-resident.service.template`];
  for (const file of paths) {
    const before = fs.readFileSync(file);
    for (const action of [
      () => fs.openSync(file, 'r+'),
      () => fs.renameSync(file, `${file}.host-replacement`),
      () => fs.writeFileSync(path.join(path.dirname(file), 'host-controlled'), '')
    ]) {
      assert.throws(action, (error) => ['EACCES', 'EPERM', 'EROFS'].includes(error.code));
      denied += 1;
    }
    assert.deepEqual(fs.readFileSync(file), before);
  }
  assert.throws(() => fs.unlinkSync(SOCKET),
    (error) => ['EACCES', 'EPERM'].includes(error.code));
  send({ denied });
}

async function stateAncestors() {
  const { requireProtectedStatePath } = moduleAt('daemon-identity-policy');
  assert.doesNotThrow(() => requireProtectedStatePath('/run/qualified-state', DAEMON_UID));
  const unsafe = '/run/host-state/daemon-leaf';
  assert.equal(fs.statSync(unsafe).uid, DAEMON_UID);
  assert.equal(fs.statSync(unsafe).mode & 0o777, 0o700);
  assert.throws(() => requireProtectedStatePath(unsafe, DAEMON_UID),
    /RESIDENT_DAEMON_IDENTITY_UNTRUSTED/u);
  send({ hostOwnedStateAncestorRejected: true });
}

async function impostor() {
  const socketPath = '/run/host-impostor/control.sock';
  let receivedBytes = 0;
  const sockets = new Set();
  const server = net.createServer((socket) => {
    sockets.add(socket); socket.on('error', () => {});
    socket.on('data', (bytes) => { receivedBytes += bytes.length; });
    socket.on('close', () => sockets.delete(socket));
  });
  process.on('message', async (command) => {
    if (command === 'counts') send({ receivedBytes });
    if (command === 'stop') {
      for (const socket of sockets) socket.destroy();
      await new Promise((resolve) => server.close(resolve));
      send({ stopped: true }); process.disconnect();
    }
  });
  await new Promise((resolve) => server.listen(socketPath, resolve));
  fs.chmodSync(socketPath, 0o660);
  send({ ready: true });
}

async function rejectImpostor() {
  const connection = moduleAt('client').createCompanionClient();
  // Path metadata is deliberately made plausible by the privileged fixture;
  // production authentication must still reject the actual same-UID peer.
  await assert.rejects(connection.attach(), /RESIDENT_DAEMON_IDENTITY_REJECTED/u);
  await assert.rejects(connection.status(), /RESIDENT_DAEMON_IDENTITY_REJECTED/u);
  send({ rejected: true });
}

function startChild(role, uid, gid = GID) {
  const child = spawn(process.execPath, [__filename, role], {
    uid, gid, env: { LANG: 'C', LC_ALL: 'C' },
    stdio: ['ignore', 'pipe', 'pipe', 'ipc']
  });
  let errors = '';
  const queue = [];
  const readers = [];
  child.stderr.on('data', (bytes) => { errors += bytes; });
  child.stdout.on('data', (bytes) => { errors += bytes; });
  child.on('message', (message) => {
    if (readers.length) readers.shift().resolve(message);
    else queue.push(message);
  });
  const ended = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('exit', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${role} failed (${code}): ${errors}`));
      for (const reader of readers.splice(0)) reader.reject(new Error(`${role} exited: ${errors}`));
    });
  });
  // Error delivery stays observable even while orchestrator is awaiting IPC.
  ended.catch(() => {});
  return { child, ended, next: () => queue.length ? Promise.resolve(queue.shift())
    : new Promise((resolve, reject) => readers.push({ resolve, reject })) };
}
async function oneShot(role, uid) {
  const child = startChild(role, uid);
  const result = await child.next();
  await child.ended;
  return result;
}
async function request(child, value) { child.child.send(value); return child.next(); }

async function orchestrate() {
  assert.equal(process.getuid(), 0);
  assert.ok(fs.existsSync('/.dockerenv'), 'fixture requires disposable container');
  assert.equal(fs.realpathSync('/source'), '/source');
  const builder = await import(pathToFileURL('/source/tools/build-companion-integrity.mjs'));
  const manifest = builder.buildCompanionIntegrity();
  assert.deepEqual(JSON.parse(fs.readFileSync('/source/companion-integrity.json', 'utf8')),
    manifest, 'source integrity manifest must already match the reviewed package');
  for (const entry of manifest.files) {
    const dest = path.join(PACKAGE, entry.path);
    fs.mkdirSync(path.dirname(dest), { recursive: true, mode: 0o755 });
    fs.writeFileSync(dest, fs.readFileSync(path.join('/source', entry.path)),
      { mode: 0o644, flag: 'wx' });
    fs.chmodSync(dest, entry.path === 'resident-peer-credentials' ? 0o755 : 0o644);
  }
  fs.writeFileSync(`${PACKAGE}/companion-integrity.json`, builder.encodeCompanionIntegrity(manifest),
    { mode: 0o644, flag: 'wx' });
  fs.writeFileSync(POLICY, `${JSON.stringify({
    schema: 'agents-os-resident.daemon-identity.v1', daemonUid: DAEMON_UID,
    clientUid: CLIENT_UID, socketGid: GID, packageRoot: PACKAGE,
    nodeBinary: fs.realpathSync(process.execPath), buildId: manifest.buildId
  })}\n`, { mode: 0o644, flag: 'wx' });
  fs.mkdirSync(path.dirname(SOCKET), { mode: 0o750 });
  fs.chownSync(path.dirname(SOCKET), DAEMON_UID, GID);
  fs.mkdirSync('/run/qualified-state', { mode: 0o700 });
  fs.chownSync('/run/qualified-state', DAEMON_UID, GID);
  fs.mkdirSync('/run/host-state', { mode: 0o755 });
  fs.chownSync('/run/host-state', CLIENT_UID, GID);
  fs.mkdirSync('/run/host-state/daemon-leaf', { mode: 0o700 });
  fs.chownSync('/run/host-state/daemon-leaf', DAEMON_UID, GID);
  const stateEvidence = await oneShot('state-ancestors', DAEMON_UID);
  const daemonProcess = startChild('daemon', DAEMON_UID);
  assert.deepEqual(await daemonProcess.next(), { ready: true });
  const positive = await oneShot('client', CLIENT_UID);
  const rewrites = await oneShot('rewrite', CLIENT_UID);
  const before = await request(daemonProcess, 'counts');
  await oneShot('wrong-client', 2003);
  const after = await request(daemonProcess, 'counts');
  assert.deepEqual(after, before, 'wrong UID reached lifecycle dispatch');
  assert.equal(after.queryCalls, 1);
  await request(daemonProcess, 'stop');
  await daemonProcess.ended;
  fs.mkdirSync('/run/host-impostor', { mode: 0o700 });
  fs.chownSync('/run/host-impostor', CLIENT_UID, GID);
  const impostorProcess = startChild('impostor', CLIENT_UID);
  assert.deepEqual(await impostorProcess.next(), { ready: true });
  // Root-assisted fault injection only: host UID could not perform this rename.
  fs.renameSync('/run/host-impostor/control.sock', SOCKET);
  fs.chownSync(SOCKET, DAEMON_UID, GID);
  await oneShot('reject-impostor', CLIENT_UID);
  await sleep(20);
  const impostorCounts = await request(impostorProcess, 'counts');
  assert.equal(impostorCounts.receivedBytes, 0);
  await request(impostorProcess, 'stop');
  await impostorProcess.ended;
  process.stdout.write('CROSS_UID_TRANSPORT_FIXTURE_PASS\n');
  process.stdout.write(`${JSON.stringify({ ...positive, ...stateEvidence,
    wrongUidDispatched: after.statusCalls - before.statusCalls,
    impostorReceivedBytes: impostorCounts.receivedBytes,
    protectedRewriteDenials: rewrites.denied,
    installationQualification: false, buildId: manifest.buildId,
    nodeVersion: process.version,
    glibcVersion: process.report.getReport().header.glibcVersionRuntime
  })}\n`);
}

const routes = { orchestrate, daemon, client, 'wrong-client': wrongClient,
  rewrite: rewriteAttempts, impostor, 'reject-impostor': rejectImpostor,
  'state-ancestors': stateAncestors };
Promise.resolve().then(() => {
  assert.ok(Object.hasOwn(routes, mode));
  return routes[mode]();
}).then(() => {
  if (!['daemon', 'impostor', 'orchestrate'].includes(mode)) process.disconnect();
}).catch((error) => { process.stderr.write(`${error.stack}\n`); process.exit(1); });
