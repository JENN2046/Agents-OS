'use strict';

const assert = require('node:assert/strict');
const {
  chmodSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  rmSync,
  statSync
} = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');

const { createResidentAdapter } = require('../companion/adapter');
const { createCompanionClient } = require('../companion/client');
const { verifyCompanionIntegrity } = require('../companion/integrity');
const { startDaemon } = require('../companion/resident-daemon');

const ALLOWED_STATE = new Set([
  'agents-os-resident-local-owner-v1.lock',
  'agents-os-resident-local-owner-v1.sqlite3',
  'agents-os-resident-local-owner-v1.sqlite3-journal'
]);

function createGoalRequest() {
  return {
    operation: 'PROPOSE_GOAL_MUTATION',
    mutation: {
      mutationType: 'CREATE_GOAL_BUNDLE',
      payload: {
        title: 'Windows target quarantine Goal',
        description: 'Deterministic in-process integration only',
        successCriteria: [
          {
            description: 'One synthetic task accepted',
            selectedTaskOrdinal: 1
          }
        ],
        tasks: [
          {
            title: 'Observe the quarantine integration',
            description: 'No external effect',
            supportsCriteria: [1]
          }
        ]
      }
    }
  };
}

function quarantineGenesisEvidence() {
  return JSON.stringify({
    availability: 'AVAILABLE',
    evidenceId: 'evidence:windows-quarantine:genesis',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'EMPTY',
    witnessId: 'witness:SELFTEST:RESIDENT'
  });
}

function quarantineGenesisProvisioning() {
  return JSON.stringify({
    authorityId: 'authority:SELFTEST:RESIDENT',
    protocol: 'MMR0_GENESIS_PROVISIONING_V1',
    provisioningId: 'provisioning:windows-quarantine',
    residentId: 'resident:LOCAL_OWNER_SESSION_V1:jenn'
  });
}

function quarantineRestartEvidence(anchor) {
  return JSON.stringify({
    ancestorAnchors: [],
    availability: 'AVAILABLE',
    current: anchor,
    evidenceId: 'evidence:windows-quarantine:restart',
    protocol: 'MMR0_CONTINUITY_EVIDENCE_V1',
    state: 'PRESENT',
    witnessId: 'witness:SELFTEST:RESIDENT'
  });
}

async function startQuarantineDaemon({
  buildId,
  rootPath,
  socketPath,
  continuityEvidence = quarantineGenesisEvidence(),
  genesisProvisioningAuthority = quarantineGenesisProvisioning()
}) {
  const argv = [
    '--root',
    rootPath,
    '--socket',
    socketPath,
    '--expected-build-id',
    buildId,
    '--continuity-evidence',
    continuityEvidence
  ];
  if (genesisProvisioningAuthority !== null
    && genesisProvisioningAuthority !== undefined) {
    argv.push('--genesis-provisioning-authority', genesisProvisioningAuthority);
  }
  return startDaemon({ argv });
}

test('Windows-target build completes actual native + companion + Host integration in disposable state', async (t) => {
  const quarantine = mkdtempSync(
    path.join(tmpdir(), 'agents-os-resident-windows-target-it-')
  );
  chmodSync(quarantine, 0o700);
  const rootPath = path.join(
    quarantine,
    'agents-os-resident-local-owner-v1'
  );
  const runtimePath = path.join(quarantine, 'runtime');
  const socketPath = path.join(runtimePath, 'control.sock');
  mkdirSync(rootPath, { mode: 0o700 });
  mkdirSync(runtimePath, { mode: 0o700 });

  let adapter = null;
  let controller = null;
  let replayClient = null;
  t.after(async () => {
    replayClient?.detach();
    await adapter?.shutdown();
    await controller?.shutdown();
    rmSync(quarantine, { recursive: true, force: true });
  });

  const integrity = verifyCompanionIntegrity();
  await assert.rejects(
    startQuarantineDaemon({
      buildId: `sha256:${'0'.repeat(64)}`,
      rootPath,
      socketPath
    }),
    { code: 'RESIDENT_INTEGRITY_MISMATCH' }
  );

  controller = await startQuarantineDaemon({
    buildId: integrity.buildId,
    rootPath,
    socketPath
  });
  const statusClient = createCompanionClient({ socketPath, integrity });
  const status = await statusClient.status();
  assert.equal(status.activationState, 'ACTIVE_LOCAL_OWNER');
  assert.equal(status.runtimeUsable, false);
  assert.equal(status.localGoalTaskUsable, true);
  assert.equal(status.providerEnabled, false);
  assert.equal(status.memoryEnabled, false);
  assert.equal(status.externalEffectsEnabled, false);

  adapter = createResidentAdapter({
    createClient: () => createCompanionClient({ socketPath, integrity }),
    retryWindowMs: 0
  });
  const attached = await adapter.initialize();
  assert.equal(attached.initialized, true);
  assert.equal(attached.attachmentState, 'ATTACHED');

  const before = await adapter.processToolCall({
    operation: 'QUERY_GOALS',
    query: { mode: 'LIST' }
  });
  assert.deepEqual(before.items, []);

  const presentations = [];
  const modelProposal = await adapter.processToolCall(
    createGoalRequest(),
    {
      sourceNode: 'post',
      async emitEphemeralPresentation(presentation) {
        presentations.push(presentation);
        return true;
      }
    }
  );
  assert.equal(presentations.length, 1);
  assert.equal(
    presentations[0].schema,
    'agents-os-resident.host-presentation.v1'
  );
  assert.equal(presentations[0].kind, 'OWNER_CONSENT_CHALLENGE');
  assert.match(presentations[0].challenge, /^确认创建，..、..、..$/u);
  assert.equal(modelProposal.resultCode, 'PROPOSAL_PREPARED');
  assert.equal(Object.hasOwn(modelProposal, 'consentPrompt'), false);
  assert.doesNotMatch(
    JSON.stringify(modelProposal),
    /确认创建|proposalFingerprint/u
  );

  const wrong = await adapter.processMessages([
    { role: 'user', content: '确认创建，错误、口令、组合' }
  ]);
  assert.equal(
    wrong[0].content,
    '[AGENTSOSResident owner-consent ingress redacted]'
  );
  assert.doesNotMatch(
    JSON.stringify(wrong),
    /确认创建，错误、口令、组合/u
  );
  assert.match(wrong.at(-1).content, /"resultCode":"CONSENT_REJECTED"/u);
  assert.deepEqual((await adapter.processToolCall({
    operation: 'QUERY_GOALS',
    query: { mode: 'LIST' }
  })).items, []);

  const challenge = presentations[0].challenge;
  const committed = await adapter.processMessages([
    { role: 'user', content: challenge }
  ]);
  assert.equal(
    committed[0].content,
    '[AGENTSOSResident owner-consent ingress redacted]'
  );
  assert.doesNotMatch(JSON.stringify(committed), new RegExp(challenge, 'u'));
  assert.match(committed.at(-1).content, /"resultCode":"COMMITTED"/u);
  const after = await adapter.processToolCall({
    operation: 'QUERY_GOALS',
    query: { mode: 'LIST' }
  });
  assert.equal(after.items.length, 1);

  assert.ok(readdirSync(rootPath).every((name) => ALLOWED_STATE.has(name)));
  assert.equal(statSync(rootPath).mode & 0o777, 0o700);
  for (const name of [
    'agents-os-resident-local-owner-v1.lock',
    'agents-os-resident-local-owner-v1.sqlite3'
  ]) {
    assert.equal(statSync(path.join(rootPath, name)).mode & 0o777, 0o600);
  }

  assert.deepEqual(await adapter.shutdown(), {
    shutdown: true,
    attachmentState: 'DETACHED',
    runtimeUsable: false,
    localGoalTaskUsable: false,
    commandChannelEnabled: false,
    residentContinuesOnHostShutdown: true
  });
  adapter = null;
  await controller.shutdown();
  controller = null;
  assert.equal(existsSync(socketPath), false);

  controller = await startQuarantineDaemon({
    buildId: integrity.buildId,
    rootPath,
    socketPath,
    continuityEvidence: quarantineRestartEvidence(status.continuityAnchor),
    genesisProvisioningAuthority: null
  });
  replayClient = createCompanionClient({ socketPath, integrity });
  await replayClient.attach();
  const replay = await replayClient.submitConsent({
    ingress: 'FINAL_VOICE_TRANSCRIPT',
    transcript: challenge
  });
  assert.equal(replay.resultCode, 'REPLAYED_COMMITTED');
  replayClient.detach();
  replayClient = null;
  await controller.shutdown();
  controller = null;
  assert.equal(existsSync(socketPath), false);
});
