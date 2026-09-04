'use strict';

const assert = require('node:assert/strict');
const {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readlinkSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync
} = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const test = require('node:test');

const { createCompanionClient } = require('../companion/client');
const { verifyCompanionIntegrity } = require('../companion/integrity');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const DAEMON_PATH = path.resolve(PACKAGE_ROOT, 'companion/resident-daemon.js');
const PROBE_PATH = path.resolve(PACKAGE_ROOT, 'companion/probe.js');
const HOST_RUNNER_PATH = path.resolve(
  PACKAGE_ROOT,
  'tests/fixtures/host-adapter-runner.cjs'
);
const ALLOWED_STATE = new Set([
  'agents-os-resident-local-owner-v1.lock',
  'agents-os-resident-local-owner-v1.sqlite3',
  'agents-os-resident-local-owner-v1.sqlite3-journal'
]);

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function childEnvironment(extra = {}) {
  return Object.freeze({
    LANG: 'C',
    LC_ALL: 'C',
    NODE_ENV: 'test',
    ...extra
  });
}

function spawnDaemon({
  rootPath,
  socketPath,
  buildId,
  continuityEvidence,
  genesisProvisioningAuthority,
  memoryBodyRootPath,
  witnessRootPath
}) {
  const args = [
    DAEMON_PATH,
    '--root',
    rootPath,
    '--socket',
    socketPath,
    '--expected-build-id',
    buildId
  ];
  if (continuityEvidence !== undefined) {
    args.push('--continuity-evidence', continuityEvidence);
  }
  if (genesisProvisioningAuthority !== undefined) {
    args.push(
      '--genesis-provisioning-authority',
      genesisProvisioningAuthority
    );
  }
  if (memoryBodyRootPath !== undefined) {
    args.push('--memory-body-root', memoryBodyRootPath);
  }
  if (witnessRootPath !== undefined) {
    args.push('--witness-root', witnessRootPath);
  }
  return spawn(process.execPath, args, {
    cwd: PACKAGE_ROOT,
    env: childEnvironment(),
    stdio: 'ignore'
  });
}

function runProvision({
  rootPath,
  buildId,
  authorityFilePath,
  memoryBodyRootPath,
  witnessRootPath
}) {
  return spawnSync(process.execPath, [
    DAEMON_PATH,
    '--operation',
    'provision',
    '--root',
    rootPath,
    '--witness-root',
    witnessRootPath,
    '--memory-body-root',
    memoryBodyRootPath,
    '--expected-build-id',
    buildId,
    '--genesis-authority-file',
    authorityFilePath
  ], {
    cwd: PACKAGE_ROOT,
    encoding: 'utf8',
    env: childEnvironment(),
    timeout: 10000
  });
}

function snapshotFile(filePath) {
  const metadata = statSync(filePath, { bigint: true });
  return Object.freeze({
    bytes: readFileSync(filePath),
    identity: Object.freeze({
      ctimeNs: metadata.ctimeNs,
      dev: metadata.dev,
      ino: metadata.ino,
      mode: metadata.mode,
      mtimeNs: metadata.mtimeNs,
      nlink: metadata.nlink,
      size: metadata.size
    })
  });
}

function assertFileUnchanged(filePath, snapshot) {
  const metadata = statSync(filePath, { bigint: true });
  assert.deepEqual(readFileSync(filePath), snapshot.bytes);
  assert.deepEqual({
    ctimeNs: metadata.ctimeNs,
    dev: metadata.dev,
    ino: metadata.ino,
    mode: metadata.mode,
    mtimeNs: metadata.mtimeNs,
    nlink: metadata.nlink,
    size: metadata.size
  }, snapshot.identity);
}

// Canonical external fixtures mirroring src/local_owner/p1_tests.rs. These are
// supplied through the real daemon transport (CLI args -> activationConfig ->
// activation.js -> native addon -> LocalOwnerKernel::start). The daemon only
// transports them; it never fabricates or interprets admission semantics.
function genesisContinuityEvidence() {
  return JSON.stringify({
    availability: 'AVAILABLE',
    evidenceId: 'evidence:companion-it:genesis',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'EMPTY',
    witnessId: 'witness:SELFTEST:RESIDENT'
  });
}

function genesisProvisioningAuthority() {
  return JSON.stringify({
    authorityId: 'authority:SELFTEST:RESIDENT',
    protocol: 'MMR0_GENESIS_PROVISIONING_V1',
    provisioningId: 'provisioning:companion-it',
    residentId: 'resident:LOCAL_OWNER_SESSION_V1:jenn'
  });
}

function restartContinuityEvidence(anchor) {
  return JSON.stringify({
    ancestorAnchors: [],
    availability: 'AVAILABLE',
    current: anchor,
    evidenceId: 'evidence:companion-it:restart',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'PRESENT',
    witnessId: 'witness:SELFTEST:RESIDENT'
  });
}

function waitForMessage(child, expected, timeoutMs = 5000) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('CHILD_MESSAGE_TIMEOUT')), timeoutMs);
    const onMessage = (message) => {
      if (message?.event !== expected) {
        clearTimeout(timeout);
        reject(new Error('CHILD_MESSAGE_UNEXPECTED'));
        return;
      }
      clearTimeout(timeout);
      resolve(message);
    };
    child.once('message', onMessage);
  });
}

function requestHost(child, method, args, context = undefined, timeoutMs = 5000) {
  const requestId = `${process.pid}-${Date.now()}-${Math.random()}`;
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('HOST_RESPONSE_TIMEOUT')), timeoutMs);
    const onMessage = (message) => {
      if (message?.event !== 'HOST_RESPONSE' || message.requestId !== requestId) return;
      child.off('message', onMessage);
      clearTimeout(timeout);
      if (message.errorCategory) reject(new Error(message.errorCategory));
      else resolve(message.result);
    };
    child.on('message', onMessage);
    child.send({ requestId, method, args, context });
  });
}

function waitForExit(child, timeoutMs = 5000) {
  return new Promise((resolve, reject) => {
    if (child.exitCode !== null) {
      resolve({ code: child.exitCode, signal: child.signalCode });
      return;
    }
    const timeout = setTimeout(() => reject(new Error('CHILD_EXIT_TIMEOUT')), timeoutMs);
    child.once('exit', (code, signal) => {
      clearTimeout(timeout);
      resolve({ code, signal });
    });
  });
}

async function waitForActive({ socketPath, integrity, child, timeoutMs = 5000 }) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() <= deadline) {
    if (child.exitCode !== null) throw new Error('DAEMON_EXITED_BEFORE_READY');
    if (existsSync(socketPath)) {
      try {
        const client = createCompanionClient({ socketPath, integrity });
        const response = await client.status();
        if (response.activationState === 'ACTIVE_LOCAL_OWNER') return response;
      } catch {
        // Readiness remains the only fact observed during bounded retry.
      }
    }
    await delay(25);
  }
  throw new Error('DAEMON_READY_TIMEOUT');
}

function createRuntimeDirectory(parent, name) {
  const runtimeParent = path.join(parent, name);
  const runtimeDirectory = path.join(runtimeParent, 'agents-os-resident');
  mkdirSync(runtimeDirectory, { recursive: true, mode: 0o700 });
  chmodSync(runtimeParent, 0o700);
  chmodSync(runtimeDirectory, 0o700);
  return path.join(runtimeDirectory, 'control.sock');
}

function createGoalRequest() {
  return {
    operation: 'PROPOSE_GOAL_MUTATION',
    mutation: {
      mutationType: 'CREATE_GOAL_BUNDLE',
      payload: {
        title: 'Quarantine Goal',
        description: 'Actual native companion integration',
        successCriteria: [
          { description: 'One task accepted', selectedTaskOrdinal: 1 }
        ],
        tasks: [
          {
            title: 'Quarantine Task',
            description: 'No external effect',
            supportsCriteria: [1]
          }
        ]
      }
    }
  };
}

test('actual companion + Host attachment consent flow is atomic, replayable and stable', async (t) => {
  const quarantine = mkdtempSync(path.join(tmpdir(), 'agents-os-resident-owner-it-'));
  chmodSync(quarantine, 0o700);
  const rootPath = path.join(quarantine, 'agents-os-resident-local-owner-v1');
  mkdirSync(rootPath, { mode: 0o700 });
  const socketPath = createRuntimeDirectory(quarantine, 'run-primary');
  const secondSocketPath = createRuntimeDirectory(quarantine, 'run-secondary');
  const integrity = verifyCompanionIntegrity();
  const children = new Set();

  t.after(async () => {
    for (const child of children) {
      if (child.exitCode === null) {
        child.kill('SIGTERM');
        try {
          await waitForExit(child);
        } catch {
          child.kill('SIGKILL');
        }
      }
    }
    rmSync(quarantine, { recursive: true, force: true });
  });

  const first = spawnDaemon({
    rootPath,
    socketPath,
    buildId: integrity.buildId,
    continuityEvidence: genesisContinuityEvidence(),
    genesisProvisioningAuthority: genesisProvisioningAuthority()
  });
  children.add(first);
  const ready = await waitForActive({ socketPath, integrity, child: first });
  assert.equal(ready.runtimeUsable, false);
  assert.equal(ready.localGoalTaskUsable, true);
  assert.equal(ready.authenticationAssurance, 'LOCAL_OWNER_SESSION_ONLY');
  assert.ok(readdirSync(rootPath).every((name) => ALLOWED_STATE.has(name)));
  assert.equal(statSync(rootPath).mode & 0o777, 0o700);
  for (const name of [
    'agents-os-resident-local-owner-v1.lock',
    'agents-os-resident-local-owner-v1.sqlite3'
  ]) {
    assert.equal(statSync(path.join(rootPath, name)).mode & 0o777, 0o600);
  }
  assert.equal(
    readFileSync(`/proc/${first.pid}/maps`, 'utf8')
      .includes('agents-os-resident.linux-x64-gnu.node'),
    true
  );

  const probe = spawnSync(process.execPath, [PROBE_PATH, '--socket', socketPath], {
    cwd: PACKAGE_ROOT,
    env: childEnvironment(),
    encoding: 'utf8'
  });
  assert.equal(probe.status, 0);
  assert.equal(probe.stdout, 'RESIDENT_PROBE_ACTIVE\n');
  assert.equal(probe.stderr, '');

  const host = spawn(process.execPath, [HOST_RUNNER_PATH], {
    cwd: PACKAGE_ROOT,
    env: childEnvironment({
      XDG_RUNTIME_DIR: path.dirname(path.dirname(socketPath))
    }),
    stdio: ['ignore', 'ignore', 'ignore', 'ipc']
  });
  children.add(host);
  await waitForMessage(host, 'HOST_ADAPTER_ATTACHED');
  assert.equal(
    readFileSync(`/proc/${host.pid}/maps`, 'utf8')
      .includes('agents-os-resident.linux-x64-gnu.node'),
    false
  );
  const hostDescriptors = readdirSync(`/proc/${host.pid}/fd`).flatMap((fd) => {
    try {
      return [readlinkSync(`/proc/${host.pid}/fd/${fd}`)];
    } catch {
      return [];
    }
  });
  assert.equal(
    hostDescriptors.some((descriptor) => descriptor.startsWith(rootPath)),
    false
  );

  const discovery = await requestHost(host, 'processMessages', [
    {
      role: 'user',
      content: '请通过 AGENTSOSResident 发起一次 Goal proposal'
    }
  ]);
  assert.equal(discovery.length, 2);
  assert.equal(discovery[0].role, 'user');
  assert.equal(discovery[1].role, 'system');
  assert.match(discovery[1].content, /discovery-bootstrap\.v1/);
  assert.match(discovery[1].content, /PROPOSE_GOAL_MUTATION/);
  const beforeDiscoveryMutation = await requestHost(host, 'processToolCall', {
    operation: 'QUERY_GOALS',
    query: { mode: 'LIST' }
  });
  assert.equal(beforeDiscoveryMutation.items.length, 0);

  const agentProposal = await requestHost(
    host,
    'processToolCall',
    createGoalRequest(),
    { sourceNode: 'post' }
  );
  assert.equal(agentProposal.resultCode, 'PROPOSAL_PREPARED');
  assert.equal(agentProposal.challengeIssued, true);
  assert.equal(Object.hasOwn(agentProposal, 'consentPrompt'), false);
  assert.match(
    agentProposal.data.content[0].text,
    /agents-os-resident\.proposal-observation\.v1/
  );
  assert.doesNotMatch(
    JSON.stringify(agentProposal),
    /consentPrompt|proposalFingerprint|确认创建/
  );

  const proposal = await requestHost(
    host,
    'processToolCall',
    createGoalRequest(),
    { sourceNode: 'human/tool' }
  );
  assert.equal(proposal.resultCode, 'PROPOSAL_PREPARED');
  assert.equal(proposal.replacedPendingProposal, true);
  const prompt = proposal.consentPrompt;
  assert.match(prompt, /^确认创建，..、..、..$/u);

  const wrong = await requestHost(host, 'processMessages', [
    { role: 'user', content: '确认创建，错误、口令、组合' }
  ]);
  assert.equal(
    wrong[0].content,
    '[AGENTSOSResident owner-consent ingress redacted]'
  );
  assert.equal(JSON.stringify(wrong).includes('确认创建，错误、口令、组合'), false);
  assert.match(wrong.at(-1).content, /"resultCode":"CONSENT_REJECTED"/);
  const before = await requestHost(host, 'processToolCall', {
    operation: 'QUERY_GOALS',
    query: { mode: 'LIST' }
  });
  assert.equal(before.items.length, 0);

  const correct = await requestHost(host, 'processMessages', [
    { role: 'user', content: prompt }
  ]);
  assert.equal(
    correct[0].content,
    '[AGENTSOSResident owner-consent ingress redacted]'
  );
  assert.equal(JSON.stringify(correct).includes(prompt), false);
  for (const challengeWord of prompt.slice('确认创建，'.length).split('、')) {
    assert.equal(JSON.stringify(correct).includes(challengeWord), false);
  }
  assert.match(
    correct.at(-1).content,
    /agents-os-resident\.owner-consent-observation\.v1/
  );
  assert.match(correct.at(-1).content, /"resultCode":"COMMITTED"/);
  const after = await requestHost(host, 'processToolCall', {
    operation: 'QUERY_GOALS',
    query: { mode: 'LIST' }
  });
  assert.equal(after.items.length, 1);

  const client = createCompanionClient({ socketPath, integrity });
  const second = spawnDaemon({
    rootPath,
    socketPath: secondSocketPath,
    buildId: integrity.buildId,
    continuityEvidence: restartContinuityEvidence(ready.continuityAnchor)
  });
  children.add(second);
  const secondExit = await waitForExit(second);
  assert.notEqual(secondExit.code, 0);

  const stabilityMs = Number.parseInt(
    process.env.AGENTS_OS_RESIDENT_STABILITY_MS ?? '250',
    10
  );
  assert.ok(Number.isSafeInteger(stabilityMs) && stabilityMs >= 0);
  await delay(stabilityMs);
  assert.equal((await client.status()).activationState, 'ACTIVE_LOCAL_OWNER');

  host.send('shutdown');
  await waitForMessage(host, 'HOST_ADAPTER_DETACHED');
  assert.deepEqual(await waitForExit(host), { code: 0, signal: null });
  assert.equal((await client.status()).adapterAttachmentState, 'DETACHED');

  first.kill('SIGTERM');
  assert.deepEqual(await waitForExit(first), { code: 0, signal: null });
  assert.equal(existsSync(socketPath), false);

  const restarted = spawnDaemon({
    rootPath,
    socketPath,
    buildId: integrity.buildId,
    continuityEvidence: restartContinuityEvidence(ready.continuityAnchor)
  });
  children.add(restarted);
  await waitForActive({ socketPath, integrity, child: restarted });
  const replayClient = createCompanionClient({ socketPath, integrity });
  await replayClient.attach();
  const replay = await replayClient.submitConsent({
    ingress: 'FINAL_VOICE_TRANSCRIPT',
    transcript: prompt
  });
  assert.equal(replay.resultCode, 'REPLAYED_COMMITTED');
  replayClient.detach();
  restarted.kill('SIGTERM');
  assert.deepEqual(await waitForExit(restarted), { code: 0, signal: null });
});

test('daemon without canonical continuity inputs fails closed before READY', async (t) => {
  const quarantine = mkdtempSync(path.join(tmpdir(), 'agents-os-resident-owner-neg-'));
  chmodSync(quarantine, 0o700);
  const rootPath = path.join(quarantine, 'agents-os-resident-local-owner-v1');
  mkdirSync(rootPath, { mode: 0o700 });
  const socketPath = createRuntimeDirectory(quarantine, 'run-negative');
  const integrity = verifyCompanionIntegrity();
  const child = spawnDaemon({ rootPath, socketPath, buildId: integrity.buildId });
  const exit = await waitForExit(child);
  assert.notEqual(exit.code, 0);
  assert.equal(exit.signal, null);
  assert.equal(existsSync(socketPath), false);
  t.after(() => rmSync(quarantine, { recursive: true, force: true }));
});

test('one-shot provisioning enrolls Witness once and ordinary daemon restarts without genesis', async (t) => {
  const quarantine = mkdtempSync(path.join(tmpdir(), 'agents-os-resident-witness-it-'));
  chmodSync(quarantine, 0o700);
  const rootPath = path.join(quarantine, 'agents-os-resident-local-owner-v1');
  const witnessRootPath = path.join(quarantine, 'protected-witness');
  const memoryBodyRootPath = path.join(quarantine, 'private-memory-bodies');
  mkdirSync(rootPath, { mode: 0o700 });
  mkdirSync(witnessRootPath, { mode: 0o700 });
  mkdirSync(memoryBodyRootPath, { mode: 0o700 });
  const socketPath = createRuntimeDirectory(quarantine, 'run-witness-primary');
  const restartSocketPath = createRuntimeDirectory(quarantine, 'run-witness-restart');
  const invalidSocketPath = createRuntimeDirectory(quarantine, 'run-witness-invalid');
  const wrongRootSocketPath = createRuntimeDirectory(quarantine, 'run-witness-wrong-root');
  const wrongRootParent = path.join(quarantine, 'wrong-resident');
  const wrongRootPath = path.join(wrongRootParent, 'agents-os-resident-local-owner-v1');
  mkdirSync(wrongRootPath, { recursive: true, mode: 0o700 });
  chmodSync(wrongRootParent, 0o700);
  chmodSync(wrongRootPath, 0o700);
  const authorityFilePath = path.join(quarantine, 'genesis-authority.json');
  writeFileSync(authorityFilePath, genesisProvisioningAuthority(), {
    flag: 'wx',
    mode: 0o600
  });
  chmodSync(authorityFilePath, 0o600);
  const integrity = verifyCompanionIntegrity();
  const children = new Set();

  t.after(async () => {
    for (const child of children) {
      if (child.exitCode === null) {
        child.kill('SIGTERM');
        try {
          await waitForExit(child);
        } catch {
          child.kill('SIGKILL');
        }
      }
    }
    rmSync(quarantine, { recursive: true, force: true });
  });

  const inlineAuthority = spawnDaemon({
    rootPath,
    socketPath: invalidSocketPath,
    buildId: integrity.buildId,
    genesisProvisioningAuthority: genesisProvisioningAuthority(),
    memoryBodyRootPath,
    witnessRootPath
  });
  children.add(inlineAuthority);
  assert.notEqual((await waitForExit(inlineAuthority)).code, 0);
  assert.equal(existsSync(invalidSocketPath), false);
  assert.deepEqual(readdirSync(witnessRootPath), []);
  assert.deepEqual(readdirSync(rootPath), []);

  const provisioned = runProvision({
    rootPath,
    buildId: integrity.buildId,
    authorityFilePath,
    memoryBodyRootPath,
    witnessRootPath
  });
  assert.equal(provisioned.error, undefined);
  assert.equal(provisioned.status, 0);
  assert.equal(provisioned.signal, null);
  assert.equal(provisioned.stdout, 'RESIDENT_WITNESS_PROVISIONED\n');
  assert.equal(provisioned.stderr, '');
  assert.equal(existsSync(socketPath), false);
  assert.deepEqual(readdirSync(memoryBodyRootPath), []);

  const witnessEntries = readdirSync(witnessRootPath);
  assert.equal(witnessEntries.length, 1);
  assert.match(witnessEntries[0], /^[0-9a-f]{64}\.witness\.json$/u);
  const witnessPath = path.join(witnessRootPath, witnessEntries[0]);
  const databasePath = path.join(
    rootPath,
    'agents-os-resident-local-owner-v1.sqlite3'
  );
  const witnessSnapshot = snapshotFile(witnessPath);
  const databaseSnapshot = snapshotFile(databasePath);
  assert.equal(statSync(witnessPath).mode & 0o777, 0o600);
  assert.equal(statSync(witnessPath).nlink, 1);
  assert.equal(statSync(databasePath).mode & 0o777, 0o600);
  assert.equal(statSync(databasePath).nlink, 1);
  assert.equal(statSync(rootPath).mode & 0o777, 0o700);
  assert.equal(statSync(witnessRootPath).mode & 0o777, 0o700);
  assert.equal(statSync(memoryBodyRootPath).mode & 0o777, 0o700);

  const first = spawnDaemon({
    rootPath,
    socketPath,
    buildId: integrity.buildId,
    memoryBodyRootPath,
    witnessRootPath
  });
  children.add(first);
  const ready = await waitForActive({ socketPath, integrity, child: first });
  assert.equal(typeof ready.continuityAnchor?.eventSequence, 'number');
  assertFileUnchanged(witnessPath, witnessSnapshot);
  assertFileUnchanged(databasePath, databaseSnapshot);

  const wrongResident = spawnDaemon({
    rootPath: wrongRootPath,
    socketPath: wrongRootSocketPath,
    buildId: integrity.buildId,
    memoryBodyRootPath,
    witnessRootPath
  });
  children.add(wrongResident);
  assert.notEqual((await waitForExit(wrongResident)).code, 0);
  assert.deepEqual(readdirSync(wrongRootPath), [
    'agents-os-resident-local-owner-v1.lock'
  ]);
  assert.equal(
    existsSync(path.join(wrongRootPath, 'agents-os-resident-local-owner-v1.sqlite3')),
    false
  );
  assert.deepEqual(readdirSync(witnessRootPath), witnessEntries);
  assertFileUnchanged(witnessPath, witnessSnapshot);
  assertFileUnchanged(databasePath, databaseSnapshot);

  first.kill('SIGTERM');
  assert.deepEqual(await waitForExit(first), { code: 0, signal: null });
  const restarted = spawnDaemon({
    rootPath,
    socketPath: restartSocketPath,
    buildId: integrity.buildId,
    memoryBodyRootPath,
    witnessRootPath
  });
  children.add(restarted);
  const restartedReady = await waitForActive({
    socketPath: restartSocketPath,
    integrity,
    child: restarted
  });
  assert.deepEqual(restartedReady.continuityAnchor, ready.continuityAnchor);
  assert.deepEqual(readdirSync(witnessRootPath), witnessEntries);
  assertFileUnchanged(witnessPath, witnessSnapshot);
  assertFileUnchanged(databasePath, databaseSnapshot);
  restarted.kill('SIGTERM');
  assert.deepEqual(await waitForExit(restarted), { code: 0, signal: null });

  const replayedProvision = runProvision({
    rootPath,
    buildId: integrity.buildId,
    authorityFilePath,
    memoryBodyRootPath,
    witnessRootPath
  });
  assert.equal(replayedProvision.error, undefined);
  assert.equal(replayedProvision.status, 73);
  assert.equal(replayedProvision.signal, null);
  assert.equal(replayedProvision.stdout, '');
  assert.equal(replayedProvision.stderr, '');
  assertFileUnchanged(witnessPath, witnessSnapshot);
  assertFileUnchanged(databasePath, databaseSnapshot);
  assert.deepEqual(readdirSync(memoryBodyRootPath), []);
});
