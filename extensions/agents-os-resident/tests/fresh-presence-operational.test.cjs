'use strict';

const assert = require('node:assert/strict');
const { fork, spawn, spawnSync } = require('node:child_process');
const { createHash, randomBytes } = require('node:crypto');
const { EventEmitter } = require('node:events');
const {
  chmodSync,
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync
} = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  ACTIVATION_CONFIRMATION,
  ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
  createResidentLifecycle
} = require('../activation');
const { createResidentAdapter } = require('../companion/adapter');
const { createCompanionClient } = require('../companion/client');
const { verifyCompanionIntegrity } = require('../companion/integrity');
const { MemoryBodyWriter } = require('../companion/memory-body-writer');
const {
  RETRIEVAL_ANNOTATIONS_PROPERTY,
  RETRIEVAL_ANNOTATIONS_SCHEMA,
  canonicalBytes,
  domainDigest,
  isPresenceCarrierMessage,
  retrievalItemDigest
} = require('../companion/presence-context');
const { createCompanionServer } = require('../companion/server');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const DAEMON_PATH = path.join(PACKAGE_ROOT, 'companion', 'resident-daemon.js');
const FETCH_HARNESS = Symbol.for(
  'agents-os-resident.provider-fetch-harness.v1'
);
const PRESENCE_BINDING_PROPERTY = '__agentsOsResidentPresence';
const PROFILE_ID = 'resident:LOCAL_OWNER_SESSION_V1:jenn';
const INVENTORY_ID = 'state:presence:memory-adopted:v1';
const ONERING_ID = 'state:presence:onering-binding:v1';
const MEMORY_CANDIDATE_SCHEMA = 'AGENTS_OS_MEMORY_CANDIDATE_V1';
const MEMORY_AUTHORITY_SCHEMA = 'AGENTS_OS_MEMORY_AUTHORITY_STATE_V1';
const MEMORY_INVENTORY_SCHEMA = 'AGENTS_OS_MEMORY_PRESENCE_INVENTORY_V2';
const ONERING_SCHEMA = 'AGENTS_OS_ONERING_IDENTITY_BINDING_V1';
const WORKER_MODE = process.env.AGENTS_OS_M4_WORKER_MODE || null;

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

function sha256Text(value) {
  return `sha256:${sha256(Buffer.from(value, 'utf8'))}`;
}

function token(label, runId) {
  return sha256(Buffer.from(`${label}\0${runId}`, 'utf8'));
}

function mode(filePath) {
  return lstatSync(filePath).mode & 0o777;
}

function activationConfig(config) {
  return {
    AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION: ACTIVATION_CONFIRMATION,
    AGENTS_OS_RESIDENT_ACTIVATION_MODE:
      ACTIVATION_MODE_LOCAL_OWNER_SESSION_V1,
    AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT: config.memoryBodyRoot,
    AGENTS_OS_RESIDENT_ROOT: config.residentRoot,
    AGENTS_OS_RESIDENT_WITNESS_ROOT: config.witnessRoot
  };
}

function fixtureConfig({ quarantine, runId }) {
  const memoryDigest = token('M4/memory', runId);
  const candidateDigest = token('M4/candidate', runId);
  const oneRingKey = `m4-${token('M4/external-key', runId)}`;
  const externalKeyDigest = sha256(Buffer.from(oneRingKey, 'utf8'));
  const foreignOneRingKey = `m4-${token('M4/foreign-external-key', runId)}`;
  const frontendPlane = 'VCPCHAT_M4_SYNTHETIC';
  const displayName = 'Synthetic M4 Same Display Name';
  const frontends = ['A', 'B'].map((name) => ({
    agentName: displayName,
    displayName,
    externalKeyDigest,
    frontendPlane,
    frontendPrincipalDigest: token(`M4/frontend-principal/${name}`, runId),
    frontendSource: `synthetic-m4-fresh-frontend-${name.toLowerCase()}-${runId.slice(0, 12)}`,
    oneRingKey,
    requestHash: token(`M4/request/${name}`, runId),
    turnId: `turn:synthetic:m4:${name.toLowerCase()}:${runId.slice(0, 24)}`
  }));
  const providerWorkspaceRoot =
    process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT
      ? path.resolve(process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT)
      : path.resolve(PACKAGE_ROOT, '../../../VCPToolBox-Selected-Source-Reconciliation');
  const oneRingNativeModuleRoot = path.resolve(
    process.env.AGENTS_OS_RESIDENT_ONERING_NATIVE_MODULE_ROOT
      || path.resolve(
        PACKAGE_ROOT,
        '../../../src/vcptoolbox-mmr-audit/probe-runtime/node_modules/better-sqlite3'
      )
  );
  const oneRingRoot = path.join(quarantine, 'isolated-vcp');
  return {
    runId,
    quarantine,
    residentRoot: path.join(
      quarantine,
      'resident',
      'agents-os-resident-local-owner-v1'
    ),
    witnessRoot: path.join(quarantine, 'protected-witness'),
    memoryBodyRoot: path.join(quarantine, 'private-memory-bodies'),
    authorityFile: path.join(quarantine, 'genesis-authority.json'),
    databasePath: path.join(
      quarantine,
      'resident',
      'agents-os-resident-local-owner-v1',
      'agents-os-resident-local-owner-v1.sqlite3'
    ),
    sockets: {
      A: path.join(quarantine, 'run-a', 'agents-os-resident', 'control.sock'),
      B: path.join(quarantine, 'run-b', 'agents-os-resident', 'control.sock'),
      C: path.join(quarantine, 'run-c', 'agents-os-resident', 'control.sock'),
      duplicate: path.join(
        quarantine,
        'run-duplicate',
        'agents-os-resident',
        'control.sock'
      )
    },
    memoryId: `memory:v1:${memoryDigest}`,
    candidateId: `state:candidate:memory:v1:${candidateDigest}`,
    subjectRef: 'subject:synthetic:P2-F',
    bodyText: `M4_PRIVATE_MEMORY_BODY_MUST_NOT_LEAK_${runId}\n`,
    conversation: {
      A: {
        assistant: `M4_ONERING_A_ASSISTANT_${token('M4/conversation/A/assistant', runId)}`,
        user: `M4_ONERING_A_USER_${token('M4/conversation/A/user', runId)}`
      },
      B: {
        assistant: `M4_ONERING_B_ASSISTANT_${token('M4/conversation/B/assistant', runId)}`,
        user: `M4_ONERING_B_USER_${token('M4/conversation/B/user', runId)}`
      },
      C: {
        assistant: `M4_ONERING_C_ASSISTANT_${token('M4/conversation/C/assistant', runId)}`,
        user: `M4_ONERING_C_USER_${token('M4/conversation/C/user', runId)}`
      }
    },
    workSentinels: {
      goalTitle: `M4_PRIVATE_GOAL_TITLE_MUST_NOT_LEAK_${runId}`,
      goalDescription: `M4_PRIVATE_GOAL_DESCRIPTION_MUST_NOT_LEAK_${runId}`,
      taskTitle: `M4_PRIVATE_TASK_TITLE_MUST_NOT_LEAK_${runId}`,
      taskDescription: `M4_PRIVATE_TASK_DESCRIPTION_MUST_NOT_LEAK_${runId}`,
      activityContext: `M4_PRIVATE_ACTIVITY_CONTEXT_MUST_NOT_LEAK_${runId}`,
      resultSummary: `M4_PRIVATE_RESULT_SUMMARY_MUST_NOT_LEAK_${runId}`
    },
    frontends,
    foreign: {
      authorityFile: path.join(quarantine, 'foreign-genesis-authority.json'),
      databasePath: path.join(
        quarantine,
        'foreign-resident',
        'agents-os-resident-local-owner-v1',
        'agents-os-resident-local-owner-v1.sqlite3'
      ),
      frontend: {
        agentName: displayName,
        displayName,
        externalKeyDigest: sha256(Buffer.from(foreignOneRingKey, 'utf8')),
        frontendPlane,
        frontendPrincipalDigest: token('M4/frontend-principal/C', runId),
        frontendSource: `synthetic-m4-foreign-frontend-c-${runId.slice(0, 12)}`,
        oneRingKey: foreignOneRingKey,
        requestHash: token('M4/request/C', runId),
        turnId: `turn:synthetic:m4:c:${runId.slice(0, 24)}`
      },
      foreignIdentity: `resident:v1:${token('M4/foreign-identity', runId)}`,
      memoryBodyRoot: path.join(quarantine, 'foreign-private-memory-bodies'),
      residentRoot: path.join(
        quarantine,
        'foreign-resident',
        'agents-os-resident-local-owner-v1'
      ),
      witnessRoot: path.join(quarantine, 'foreign-protected-witness')
    },
    oneRingNativeModuleRoot,
    oneRingRoot,
    providerWorkspaceRoot,
    sessionContract: {
      acceptedPriorTurnCount: 1,
      maxContextBlocks: 8,
      maxDbRecords: 32,
      minimumProviderResponseLatencyMs: 1100,
      requiredOrder: ['A_USER', 'A_ASSISTANT', 'B_USER'],
      schema: 'AGENTS_OS_M4_SYNTHETIC_ONERING_RETENTION_CONTRACT_V1'
    },
    unmanagedDailyNote: {
      bodyText: `M4_UNMANAGED_DAILYNOTE_${token('M4/unmanaged-dailynote', runId)}`,
      path: path.join(
        oneRingRoot,
        'synthetic-dailynotes',
        'same-display-name',
        'unmanaged-control.md'
      )
    }
  };
}

function foreignConfig(config) {
  return {
    ...config,
    authorityFile: config.foreign.authorityFile,
    databasePath: config.foreign.databasePath,
    frontends: [config.foreign.frontend],
    memoryBodyRoot: config.foreign.memoryBodyRoot,
    residentRoot: config.foreign.residentRoot,
    runId: `${config.runId}f`,
    sockets: { C: config.sockets.C },
    witnessRoot: config.foreign.witnessRoot
  };
}

function createProtectedDirectories(config) {
  mkdirSync(config.residentRoot, { recursive: true, mode: 0o700 });
  mkdirSync(config.witnessRoot, { mode: 0o700 });
  mkdirSync(config.memoryBodyRoot, { mode: 0o700 });
  for (const socketPath of Object.values(config.sockets)) {
    mkdirSync(path.dirname(socketPath), { recursive: true, mode: 0o700 });
    chmodSync(path.dirname(path.dirname(socketPath)), 0o700);
    chmodSync(path.dirname(socketPath), 0o700);
  }
  chmodSync(config.quarantine, 0o700);
  chmodSync(path.dirname(config.residentRoot), 0o700);
  chmodSync(config.residentRoot, 0o700);
  chmodSync(config.witnessRoot, 0o700);
  chmodSync(config.memoryBodyRoot, 0o700);
}

function createIsolatedVcpFixtures(config) {
  const pluginRoot = path.join(config.oneRingRoot, 'Plugin', 'OneRing');
  mkdirSync(path.join(pluginRoot, 'data'), { recursive: true, mode: 0o700 });
  chmodSync(config.oneRingRoot, 0o700);
  chmodSync(path.join(config.oneRingRoot, 'Plugin'), 0o700);
  chmodSync(pluginRoot, 0o700);
  chmodSync(path.join(pluginRoot, 'data'), 0o700);
  writeFileSync(
    path.join(pluginRoot, 'OneRingConfig.json'),
    JSON.stringify({
      asyncOnlyMode: false,
      enabled: true,
      maxContextBlocks: config.sessionContract.maxContextBlocks,
      tailTagPlacement: 'inline',
      timeInsert: true
    }),
    { flag: 'wx', mode: 0o600 }
  );
  mkdirSync(path.dirname(config.unmanagedDailyNote.path), {
    recursive: true,
    mode: 0o700
  });
  writeFileSync(
    config.unmanagedDailyNote.path,
    config.unmanagedDailyNote.bodyText,
    { flag: 'wx', mode: 0o600 }
  );
  chmodSync(config.unmanagedDailyNote.path, 0o600);
}

function genesisAuthority(config) {
  return {
    authorityId: `authority:SELFTEST:M4:${config.runId.slice(0, 24)}`,
    protocol: 'MMR0_GENESIS_PROVISIONING_V1',
    provisioningId: `provisioning:M4:${config.runId.slice(0, 24)}`,
    residentId: PROFILE_ID
  };
}

function runProvision(config, integrity) {
  const bytes = JSON.stringify(genesisAuthority(config));
  writeFileSync(config.authorityFile, bytes, { flag: 'wx', mode: 0o600 });
  chmodSync(config.authorityFile, 0o600);
  const result = spawnSync(process.execPath, [
    DAEMON_PATH,
    '--operation', 'provision',
    '--root', config.residentRoot,
    '--witness-root', config.witnessRoot,
    '--memory-body-root', config.memoryBodyRoot,
    '--expected-build-id', integrity.buildId,
    '--genesis-authority-file', config.authorityFile
  ], {
    cwd: PACKAGE_ROOT,
    encoding: 'utf8',
    env: { ...process.env },
    timeout: 15000
  });
  assert.equal(result.error, undefined);
  assert.equal(result.status, 0);
  assert.equal(result.signal, null);
  assert.equal(result.stdout, 'RESIDENT_WITNESS_PROVISIONED\n');
  assert.equal(result.stderr, '');
  assert.equal(mode(config.authorityFile), 0o600);
  assert.equal(readFileSync(config.authorityFile, 'utf8'), bytes);
  assert.equal(readdirSync(config.witnessRoot).length, 1);
  assert.match(readdirSync(config.witnessRoot)[0], /^[0-9a-f]{64}\.witness\.json$/u);
}

function snapshotFile(filePath) {
  const stat = statSync(filePath, { bigint: true });
  return {
    sha256: sha256(readFileSync(filePath)),
    ctimeNs: String(stat.ctimeNs),
    dev: String(stat.dev),
    ino: String(stat.ino),
    mode: Number(stat.mode & 0o7777n),
    mtimeNs: String(stat.mtimeNs),
    nlink: String(stat.nlink),
    size: String(stat.size)
  };
}

function snapshotDirectory(root) {
  const entries = [];
  function visit(directory, relative) {
    for (const name of readdirSync(directory).sort()) {
      const absolute = path.join(directory, name);
      const childRelative = relative ? `${relative}/${name}` : name;
      const stat = lstatSync(absolute, { bigint: true });
      if (stat.isDirectory()) {
        entries.push({ path: `${childRelative}/`, mode: Number(stat.mode & 0o7777n) });
        visit(absolute, childRelative);
      } else {
        entries.push({ path: childRelative, ...snapshotFile(absolute) });
      }
    }
  }
  visit(root, '');
  return entries;
}

function witnessSnapshot(config) {
  const entries = readdirSync(config.witnessRoot);
  assert.equal(entries.length, 1);
  const witnessPath = path.join(config.witnessRoot, entries[0]);
  assert.equal(mode(witnessPath), 0o600);
  assert.equal(statSync(witnessPath).nlink, 1);
  return {
    listing: [...entries].sort(),
    file: snapshotFile(witnessPath)
  };
}

function provenance(config) {
  const actor = `actor:synthetic-test-harness:M4:${config.runId.slice(0, 24)}`;
  const sourceRef = `source:synthetic-test:M4:${config.runId.slice(0, 24)}`;
  const basisRef = `basis:synthetic-test:M4:${config.runId.slice(0, 24)}`;
  return {
    interpreter: { ref: actor, type: 'SYNTHETIC_TEST_HARNESS' },
    mutationActor: { ref: actor, type: 'SYNTHETIC_TEST_HARNESS' },
    source: { ref: sourceRef, type: 'SYNTHETIC_TEST' },
    sourceAuthority: {
      recordRef: `source-authority-record:M4:${config.runId.slice(0, 24)}`,
      sourceRef,
      sourceType: 'SYNTHETIC_TEST',
      supportingBasisRef: basisRef
    },
    subject: { ref: config.subjectRef },
    supportingBasis: { ref: basisRef }
  };
}

function authority(config, operation, targetStateId, scope) {
  return {
    authorityBasisRef:
      `authority-basis:synthetic-fixture:M4:${operation}:${config.runId.slice(0, 16)}`,
    authorityBasisType: 'ADMITTED_SYNTHETIC_FIXTURE',
    grant: {
      grantId: `grant:M4:${operation}:${targetStateId}`,
      granteeActorRef:
        `actor:synthetic-test-harness:M4:${config.runId.slice(0, 24)}`,
      operation,
      right: 'MMR_DURABLE_STATE_MUTATION',
      scope,
      subjectRef: config.subjectRef,
      targetStateId
    }
  };
}

function candidateMutation(config, identity, generation, descriptor) {
  const operationId = `operation:M4:memory:candidate:${config.runId.slice(0, 24)}`;
  return {
    operationId,
    request: {
      attachmentGeneration: 1,
      request: {
        operation: 'PROPOSE_MMR_MUTATION_CORE',
        mutation: {
          components: {
            authority: authority(
              config,
              'CREATE_CANDIDATE',
              config.candidateId,
              'CANDIDATE_STATE'
            ),
            content: { value: {
              authorityGeneration: generation,
              bodyDescriptor: descriptor,
              identityOpaqueId: identity,
              memoryId: config.memoryId,
              motivatingEvidenceRef: null,
              schema: MEMORY_CANDIDATE_SCHEMA
            } },
            lifecycle: {
              epistemicState: 'UNASSESSED',
              lifecycleState: 'CANDIDATE'
            },
            plane: {
              claimScope: 'CANDIDATE',
              controllerRole: 'NON_CONTROLLER',
              interpretationOwnerRef: null,
              objectKind: 'CANDIDATE_STATE',
              sharedEventStateId: null
            },
            provenance: provenance(config),
            transition: {
              predecessorStateFingerprint: null,
              supersedesStateFingerprint: null
            }
          },
          expectedCurrentFingerprint: null,
          mutationType: 'CREATE_CANDIDATE',
          operationId,
          targetStateId: config.candidateId
        }
      }
    }
  };
}

function stateMutation(config, {
  content,
  expectedCurrentFingerprint,
  mutationType,
  operationId,
  targetStateId
}) {
  const lifecycleState = {
    CREATE: 'P2_B_CREATED',
    REVISE: 'P2_B_SUCCESSOR',
    RETIRE: 'P2_D_RETIRED'
  }[mutationType];
  return {
    operationId,
    request: {
      attachmentGeneration: 1,
      request: {
        operation: 'PROPOSE_MMR_MUTATION_CORE',
        mutation: {
          components: {
            authority: authority(
              config,
              mutationType,
              targetStateId,
              'MMR_STATE_CORE'
            ),
            content: { value: content },
            lifecycle: {
              epistemicState: 'UNASSESSED',
              lifecycleState
            },
            plane: {
              claimScope: 'MMR_STATE_CORE',
              controllerRole: 'NON_CONTROLLER',
              interpretationOwnerRef: null,
              objectKind: 'SCOPED_CLAIM',
              sharedEventStateId: null
            },
            provenance: provenance(config),
            transition: {
              predecessorStateFingerprint: expectedCurrentFingerprint,
              supersedesStateFingerprint:
                mutationType === 'RETIRE' ? null : expectedCurrentFingerprint
            }
          },
          expectedCurrentFingerprint,
          mutationType,
          operationId,
          targetStateId
        }
      }
    }
  };
}

function inventoryContent(config, identity, generation, adoptedMemoryId) {
  return {
    adoptedMemoryId,
    authorityGeneration: generation,
    candidateIds: [config.candidateId],
    identityOpaqueId: identity,
    schema: MEMORY_INVENTORY_SCHEMA
  };
}

function memoryAuthorityContent(
  config,
  identity,
  generation,
  descriptor,
  candidateFingerprint
) {
  return {
    authorityGeneration: generation,
    authorityStatus: 'ADOPTED',
    bodyDescriptor: descriptor,
    candidateRef: {
      candidateFactFingerprint: candidateFingerprint,
      candidateId: config.candidateId
    },
    identityOpaqueId: identity,
    memoryId: config.memoryId,
    schema: MEMORY_AUTHORITY_SCHEMA
  };
}

function scopedPrincipal(frontendPlane, rawPrincipalDigest) {
  return domainDigest(
    'agents-os.local-owner.onering-frontend-principal.v1',
    canonicalBytes({
      frontendPlane,
      principalDigest: `sha256:${rawPrincipalDigest}`
    })
  );
}

function oneRingContent(config, identity, generation) {
  return {
    authorityGeneration: generation,
    bindingId: `binding:onering:synthetic:m4:${config.runId.slice(0, 24)}`,
    bindingRevision: 1,
    bindingStatus: 'ACTIVE',
    externalKeyClass: 'OPAQUE_V1',
    externalKeySha256: `sha256:${config.frontends[0].externalKeyDigest}`,
    externalPlane: 'ONERING',
    frontendPlane: config.frontends[0].frontendPlane,
    frontendPrincipalSha256: config.frontends.map((frontend) =>
      scopedPrincipal(frontend.frontendPlane, frontend.frontendPrincipalDigest)),
    frontendSourceSha256: config.frontends.map((frontend) =>
      domainDigest(
        'agents-os.local-owner.onering-frontend-source.v1',
        Buffer.from(frontend.frontendSource, 'utf8')
      )),
    identityOpaqueId: identity,
    retired: false,
    schema: ONERING_SCHEMA
  };
}

async function applyMmr(lifecycle, fixture) {
  const prepared = await lifecycle.prepareMmrMutation(fixture.request);
  assert.equal(prepared.resultCode, 'MMR_MUTATION_CORE_PROPOSAL_PREPARED');
  const result = await lifecycle.submitMmrMutationConsent({
    attachmentGeneration: 1,
    ingress: 'TYPED_TEXT',
    operationId: fixture.operationId,
    transcript: prepared.consentPrompt
  });
  assert.equal(
    result.result.resultCode,
    'APPLIED_LOCALLY_NOT_MMR_COMMITTED_PROOF'
  );
  return result;
}

async function commitGoalTaskMutation(lifecycle, operation, mutationType, payload) {
  const prepared = await lifecycle.prepareProposal({
    attachmentGeneration: 1,
    request: {
      operation,
      mutation: { mutationType, payload }
    }
  });
  assert.equal(prepared.resultCode, 'PROPOSAL_PREPARED');
  return lifecycle.submitConsent({
    attachmentGeneration: 1,
    ingress: 'TYPED_TEXT',
    transcript: prepared.consentPrompt
  });
}

async function createValidatedWork(lifecycle, config) {
  const created = await commitGoalTaskMutation(
    lifecycle,
    'PROPOSE_GOAL_MUTATION',
    'CREATE_GOAL_BUNDLE',
    {
      title: config.workSentinels.goalTitle,
      description: config.workSentinels.goalDescription,
      successCriteria: [{
        description: `criterion-${config.runId}`,
        selectedTaskOrdinal: 1
      }],
      tasks: [{
        title: config.workSentinels.taskTitle,
        description: config.workSentinels.taskDescription,
        supportsCriteria: [1]
      }]
    }
  );
  const goalId = created.result.goalId;
  assert.match(goalId, /^goal:/u);
  const tasks = await lifecycle.query({
    attachmentGeneration: 1,
    request: {
      operation: 'QUERY_TASKS',
      query: { goalId, mode: 'LIST' }
    }
  });
  assert.equal(tasks.items.length, 1);
  const taskId = tasks.items[0].taskId;
  await commitGoalTaskMutation(
    lifecycle,
    'PROPOSE_GOAL_MUTATION',
    'START_GOAL',
    { goalId }
  );
  await commitGoalTaskMutation(
    lifecycle,
    'PROPOSE_TASK_MUTATION',
    'START_TASK',
    { taskId, activityContext: config.workSentinels.activityContext }
  );
  const completed = await commitGoalTaskMutation(
    lifecycle,
    'PROPOSE_TASK_MUTATION',
    'COMPLETE_TASK_MANUALLY',
    { taskId, resultSummary: config.workSentinels.resultSummary }
  );
  assert.equal(completed.result.taskStatus, 'DONE');
  assert.equal(completed.result.validationDecision, 'PASSED');
  return { goalId, taskId };
}

function directPresenceRequest(config, frontend, label) {
  return {
    attachmentGeneration: 1,
    expectedSlots: {
      lifeFactFingerprint: null,
      memoryFactFingerprint: null,
      oneRingFactFingerprint: null,
      workSourceCutFingerprint: null
    },
    freshPresenceId: `fresh-presence:r1:${token(`M4/presence/${label}`, config.runId)}`,
    oneRing: frontend ? {
      externalKeyDigest: frontend.externalKeyDigest,
      frontendPlane: frontend.frontendPlane,
      frontendPrincipalDigest: frontend.frontendPrincipalDigest,
      frontendSource: frontend.frontendSource,
      requestHash: frontend.requestHash,
      turnId: frontend.turnId
    } : {
      externalKeyDigest: null,
      frontendPlane: null,
      frontendPrincipalDigest: null,
      frontendSource: null,
      requestHash: null,
      turnId: null
    },
    transcriptDigest: token(`M4/transcript/${label}`, config.runId)
  };
}

async function queryCore(lifecycle, operation, query) {
  return lifecycle.queryMmrMutationCore({ operation, query });
}

async function authoritySnapshot(lifecycle, config, presenceRequest) {
  const status = await lifecycle.status();
  return {
    continuityAnchor: status.continuityAnchor,
    persistence: await queryCore(
      lifecycle,
      'QUERY_MMR_PERSISTENCE_INSPECT',
      {}
    ),
    candidate: await queryCore(
      lifecycle,
      'QUERY_MMR_CANDIDATE_CORE',
      { stateId: config.candidateId }
    ),
    inventory: await queryCore(
      lifecycle,
      'QUERY_MMR_CURRENT_CORE',
      { stateId: INVENTORY_ID }
    ),
    memoryAuthority: await queryCore(
      lifecycle,
      'QUERY_MMR_CURRENT_CORE',
      { stateId: config.memoryId }
    ),
    presence: await lifecycle.queryPresenceContext(presenceRequest),
    database: snapshotFile(config.databasePath),
    residentListing: readdirSync(config.residentRoot).sort(),
    witness: witnessSnapshot(config),
    memoryBodies: snapshotDirectory(config.memoryBodyRoot)
  };
}

class SyntheticUpstreamResponse {
  constructor(body) {
    this.status = 200;
    this.statusText = 'OK';
    this.ok = true;
    this.bodyText = JSON.stringify(body);
    this.headers = Object.freeze({
      forEach(callback) {
        callback('application/json', 'content-type');
      },
      get(name) {
        return String(name).toLowerCase() === 'content-type'
          ? 'application/json'
          : null;
      }
    });
  }

  async arrayBuffer() {
    const bytes = Buffer.from(this.bodyText, 'utf8');
    return bytes.buffer.slice(
      bytes.byteOffset,
      bytes.byteOffset + bytes.byteLength
    );
  }

  clone() {
    const clone = Object.create(SyntheticUpstreamResponse.prototype);
    Object.assign(clone, this);
    return clone;
  }

  async text() {
    return this.bodyText;
  }
}

class MockResponse extends EventEmitter {
  constructor() {
    super();
    this.bodyChunks = [];
    this.destroyed = false;
    this.headers = new Map();
    this.headersSent = false;
    this.statusCode = 200;
    this.writableEnded = false;
  }

  status(code) {
    this.statusCode = code;
    return this;
  }

  setHeader(name, value) {
    this.headers.set(String(name).toLowerCase(), value);
    return this;
  }

  getHeader(name) {
    return this.headers.get(String(name).toLowerCase());
  }

  getHeaders() {
    return Object.fromEntries(this.headers);
  }

  write(chunk, encoding, callback) {
    if (typeof encoding === 'function') callback = encoding;
    this.headersSent = true;
    if (chunk !== undefined && chunk !== null) {
      this.bodyChunks.push(Buffer.isBuffer(chunk)
        ? Buffer.from(chunk)
        : Buffer.from(String(chunk)));
    }
    callback?.();
    return true;
  }

  end(chunk, encoding, callback) {
    if (typeof chunk === 'function') {
      callback = chunk;
      chunk = undefined;
    } else if (typeof encoding === 'function') {
      callback = encoding;
    }
    if (chunk !== undefined && chunk !== null) this.write(chunk);
    this.headersSent = true;
    this.writableEnded = true;
    callback?.();
    this.emit('finish');
    return this;
  }

  send(body) {
    if (body !== undefined && body !== null) this.write(body);
    return this.end();
  }

  json(body) {
    this.setHeader('content-type', 'application/json');
    return this.send(Buffer.from(JSON.stringify(body)));
  }

  text() {
    return Buffer.concat(this.bodyChunks).toString('utf8');
  }
}

function completion(frontendName, content) {
  return {
    id: `chatcmpl-m4-${frontendName.toLowerCase()}`,
    object: 'chat.completion',
    created: 1788220800,
    model: 'synthetic-m4-provider-model',
    choices: [{
      index: 0,
      message: {
        role: 'assistant',
        content
      },
      finish_reason: 'stop'
    }]
  };
}

function createSyntheticDailyNotePreprocessor(config) {
  return Object.freeze({
    async processMessages(messages) {
      const body = readFileSync(config.unmanagedDailyNote.path, 'utf8');
      assert.equal(body, config.unmanagedDailyNote.bodyText);
      const output = [...messages];
      const messageIndex = output.findIndex(({ role }) => role !== 'system');
      const insertionIndex = messageIndex < 0 ? output.length : messageIndex;
      const message = {
        role: 'system',
        content: [
          '<!-- VCP_RAG_BLOCK_START source=SYNTHETIC_DAILYNOTE -->',
          body,
          '<!-- VCP_RAG_BLOCK_END -->'
        ].join('\n')
      };
      output.splice(insertionIndex, 0, message);
      const annotation = Object.freeze({
        itemDigest: retrievalItemDigest(message),
        messageIndex: insertionIndex,
        sourceClass: 'VCP_DAILYNOTE'
      });
      Object.defineProperty(output, RETRIEVAL_ANNOTATIONS_PROPERTY, {
        configurable: false,
        enumerable: false,
        value: Object.freeze({
          items: Object.freeze([annotation]),
          schema: RETRIEVAL_ANNOTATIONS_SCHEMA
        }),
        writable: false
      });
      return output;
    }
  });
}

function createSelectedOneRing(config, frontend) {
  const pluginRoot = path.join(
    config.providerWorkspaceRoot,
    'runtime',
    'VCPToolBox',
    'Plugin',
    'OneRing'
  );
  const selectedDatabaseModuleRoot = path.join(
    config.providerWorkspaceRoot,
    'runtime',
    'VCPToolBox',
    'node_modules',
    'better-sqlite3'
  );
  const nativeDatabaseModuleRoot = config.oneRingNativeModuleRoot;
  const selectedDatabasePackageBytes = readFileSync(
    path.join(selectedDatabaseModuleRoot, 'package.json'),
    'utf8'
  );
  const nativeDatabasePackageBytes = readFileSync(
    path.join(nativeDatabaseModuleRoot, 'package.json'),
    'utf8'
  );
  const selectedDatabasePackage = JSON.parse(selectedDatabasePackageBytes);
  const nativeDatabasePackage = JSON.parse(nativeDatabasePackageBytes);
  const nativeBindingPath = path.join(
    nativeDatabaseModuleRoot,
    'build',
    'Release',
    'better_sqlite3.node'
  );
  assert.equal(nativeDatabasePackage.name, 'better-sqlite3');
  assert.equal(nativeDatabasePackage.version, selectedDatabasePackage.version);
  assert.equal(nativeDatabasePackageBytes, selectedDatabasePackageBytes);
  assert.equal(
    sha256(readFileSync(path.join(nativeDatabaseModuleRoot, 'lib', 'database.js'))),
    sha256(readFileSync(path.join(selectedDatabaseModuleRoot, 'lib', 'database.js')))
  );
  assert.equal(existsSync(nativeBindingPath), true);
  const selectedDatabaseEntry = require.resolve(selectedDatabaseModuleRoot);
  const nativeDatabaseEntry = require.resolve(nativeDatabaseModuleRoot);
  require(nativeDatabaseEntry);
  assert.ok(require.cache[nativeDatabaseEntry]);
  require.cache[selectedDatabaseEntry] = require.cache[nativeDatabaseEntry];
  const selected = require(path.join(pluginRoot, 'OneRing.js'));
  const database = require(path.join(pluginRoot, 'OneRingDB.js'));
  selected.initialize({
    DebugMode: 'false',
    ONERING_ALLOW_CONTEXT_PATCH: 'true',
    ONERING_DEDUP_SIMILARITY: '0.92',
    ONERING_MAX_DB_RECORDS: String(config.sessionContract.maxDbRecords),
    ONERING_MAX_UNKNOWN_RATIO: '0.35',
    ONERING_RECORD_ONLY: 'false',
    ONERING_USER_NAME: 'SyntheticM4Owner',
    PROJECT_BASE_PATH: config.oneRingRoot
  }, {});
  const pending = new Set();
  let lastExtractedMeta = null;
  let lastProcessError = null;
  const track = (promise) => {
    const tracked = Promise.resolve(promise);
    pending.add(tracked);
    void tracked.finally(() => pending.delete(tracked));
    return tracked;
  };
  return Object.freeze({
    async drain() {
      while (pending.size > 0) await Promise.all([...pending]);
    },
    diagnostics() {
      return {
        extracted: lastExtractedMeta,
        processError: lastProcessError
      };
    },
    extractMetaFromMessages(messages) {
      const meta = selected.extractMetaFromMessages(messages);
      lastExtractedMeta = meta;
      if (!meta
        || meta.agentName !== frontend.oneRingKey
        || meta.frontendSource !== frontend.frontendSource) return null;
      return {
        ...meta,
        externalKeyDigest: frontend.externalKeyDigest,
        frontendPlane: frontend.frontendPlane,
        frontendPrincipalDigest: frontend.frontendPrincipalDigest
      };
    },
    async processMessages(messages, requestConfig) {
      try {
        return await selected.processMessages(messages, requestConfig);
      } catch (error) {
        lastProcessError = error.stack || error.message;
        throw error;
      }
    },
    readRecent(limit = 16) {
      return database.getRecentMessages(
        frontend.oneRingKey,
        limit,
        config.oneRingRoot
      ).map(({ content, frontendSource, role, senderName }) => ({
        content,
        frontendSource,
        role,
        senderName
      }));
    },
    runtimeDependency() {
      return {
        nativeBindingSha256: sha256(readFileSync(nativeBindingPath)),
        packageVersion: selectedDatabasePackage.version
      };
    },
    recordAIResponseFromMessages(messages, aiText) {
      return track(selected.recordAIResponseFromMessages(messages, aiText));
    },
    recordAIResponseWithMeta(meta, aiText) {
      return track(selected.recordAIResponseWithMeta(meta, aiText));
    },
    shutdown() {
      selected.shutdown();
    }
  });
}

function observedResidentAdapter(adapter, observation) {
  const wrapper = {
    async processMessages(...args) {
      const output = await adapter.processMessages(...args);
      const descriptor = Object.getOwnPropertyDescriptor(
        output,
        PRESENCE_BINDING_PROPERTY
      );
      assert.ok(descriptor);
      assert.equal(descriptor.enumerable, false);
      assert.equal(descriptor.configurable, false);
      assert.equal(descriptor.writable, false);
      observation.binding = descriptor.value;
      observation.carriers = output.filter(isPresenceCarrierMessage);
      return output;
    }
  };
  Object.defineProperty(wrapper, 'sealProviderAttempt', {
    configurable: false,
    enumerable: false,
    writable: false,
    async value(input) {
      observation.trace.push('seal-start');
      observation.sealInputs.push(input);
      const result = await adapter.sealProviderAttempt(input);
      observation.sealResults.push(result);
      observation.trace.push('seal-ok');
      return result;
    }
  });
  return Object.freeze(wrapper);
}

function loadCanonicalHandler(config) {
  const hostRoot = path.join(config.providerWorkspaceRoot, 'runtime', 'VCPToolBox');
  const vcpChatRoot = path.join(config.providerWorkspaceRoot, 'runtime', 'VCPChat');
  const handlerPath = path.join(hostRoot, 'modules', 'chatCompletionHandler.js');
  const recordStorePath = path.join(hostRoot, 'modules', 'toolCallRecordStore.js');
  assert.equal(existsSync(handlerPath), true);
  assert.equal(existsSync(vcpChatRoot), true);
  process.env.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT =
    config.providerWorkspaceRoot;
  process.env.AGENTS_OS_RESIDENT_VCPCHAT_ROOT = vcpChatRoot;
  require('../tools/provider-capability-sandbox-preload.cjs');
  const resolvedRecordStore = require.resolve(recordStorePath);
  require.cache[resolvedRecordStore] = {
    children: [],
    exports: {
      beginRecord() { return null; },
      finishRecord() {}
    },
    filename: resolvedRecordStore,
    id: resolvedRecordStore,
    loaded: true,
    paths: []
  };
  return require(handlerPath);
}

function providerPluginManager({ config, frontend, oneRing, residentModule }) {
  const preprocessors = new Map([
    ['SyntheticDailyNoteRAG', createSyntheticDailyNotePreprocessor(config)],
    ['OneRing', oneRing],
    ['AGENTSOSResident', residentModule]
  ]);
  return {
    messagePreprocessors: preprocessors,
    vectorDBManager: null,
    async executeMessagePreprocessor(name, messages, config) {
      return preprocessors.get(name).processMessages(messages, config);
    },
    getAllPlaceholderValues() { return new Map(); },
    getIndividualPluginDescriptions() { return new Map(); },
    getPlugin(name) { return preprocessors.get(name) || null; },
    getResolvedPluginConfigValue() { return null; },
    getServiceModule(name) { return preprocessors.get(name) || null; },
    getVCPLogFunctions() { return null; },
    async processToolCall() {
      throw new Error('M4_UNEXPECTED_TOOL_CALL');
    }
  };
}

function providerHandlerOptions(pluginManager) {
  return {
    apiConnectionTimeoutMs: 5000,
    apiKey: 'synthetic-m4-provider-key-not-a-real-credential',
    apiRetries: 0,
    apiRetryDelay: 0,
    apiUrl: 'https://provider.invalid',
    activeRequests: new Map(),
    cachedEmojiLists: new Map(),
    chinaModel1: [],
    chinaModel1Cot: false,
    DEBUG_MODE: false,
    detectors: [],
    enableRoleDivider: false,
    enableRoleDividerInLoop: false,
    handleDiaryFromAIResponse: async () => {},
    maxVCPLoopNonStream: 1,
    maxVCPLoopStream: 1,
    modelRedirectHandler: {
      redirectModelForBackend(model) { return model; }
    },
    multiModalForceTranslateModels: [],
    pluginManager,
    RAGMemoRefresh: false,
    responseReplayCacheEnabled: false,
    roleDividerIgnoreList: [],
    roleDividerRemoveDisabledTags: false,
    roleDividerScanSwitches: {},
    roleDividerSwitches: {},
    semanticModelRouter: null,
    SHOW_VCP_OUTPUT: false,
    superDetectors: [],
    VCPToolCode: false,
    webSocketServer: {
      broadcast() {},
      formatDistributedServerListForPrompt() { return ''; }
    },
    writeChatLog: () => {},
    writeDebugLog: async () => {}
  };
}

function parseCarrier(carrier) {
  const lines = carrier.content.split('\n');
  assert.equal(lines.length, 3);
  return JSON.parse(lines[2]);
}

function assertWorkLife(modelFacing) {
  const work = modelFacing.workLife.sources.find(
    ({ sourceClass }) => sourceClass === 'RESIDENT_WORK'
  );
  const life = modelFacing.workLife.sources.find(
    ({ sourceClass }) => sourceClass === 'RESIDENT_LIFE'
  );
  assert.equal(work.currentness, 'CURRENT');
  const last = work.facts.find(
    ({ category }) => category === 'LAST_VALIDATED_RESULT'
  );
  assert.equal(last.categoryState, 'PRESENT');
  assert.equal(last.factCurrentness, 'CURRENT');
  assert.match(last.boundedRef, /^validation-result:sha256:/u);
  for (const category of [
    'ACTIVE_COMMITMENT',
    'CURRENT_FOCUS_PROJECT_TASK',
    'NEXT_STEP',
    'WAITING_OR_BLOCKER'
  ]) {
    const fact = work.facts.find((entry) => entry.category === category);
    assert.equal(fact.categoryState, 'UNKNOWN');
    assert.equal(fact.factCurrentness, 'UNKNOWN');
  }
  assert.equal(life.currentness, 'UNKNOWN');
  assert.equal(life.facts[0].categoryState, 'UNKNOWN');
  assert.equal(life.facts[0].factCurrentness, 'UNKNOWN');
  assert.deepEqual(
    life.facts[0].reasonCodes,
    ['NO_ACCEPTED_CLOSED_WORLD_LIFE_SOURCE']
  );
}

function carrierForbiddenDisclosureValues(config, frontend) {
  return [
    config.bodyText.trim(),
    config.unmanagedDailyNote.bodyText,
    ...Object.values(config.workSentinels),
    PROFILE_ID,
    config.witnessRoot,
    config.residentRoot,
    config.memoryBodyRoot,
    frontend.oneRingKey,
    frontend.externalKeyDigest,
    frontend.frontendPrincipalDigest,
    frontend.frontendSource,
    frontend.requestHash,
    frontend.turnId,
    'synthetic-m4-provider-key-not-a-real-credential'
  ];
}

function providerForbiddenDisclosureValues(config, frontend) {
  return [
    config.bodyText.trim(),
    ...Object.values(config.workSentinels),
    PROFILE_ID,
    config.witnessRoot,
    config.residentRoot,
    config.memoryBodyRoot,
    frontend.externalKeyDigest,
    frontend.frontendPrincipalDigest,
    frontend.requestHash,
    frontend.turnId,
    'synthetic-m4-provider-key-not-a-real-credential'
  ];
}

function assertLowDisclosure(config, frontend, carrierContent, providerBody) {
  const forbiddenFields = [
    'attachmentGeneration',
    'authorityGeneration',
    'bindingIdDigest',
    'bodyRef',
    'bodySha256',
    'candidateDigest',
    'contextId',
    'externalKeySha256',
    'factFingerprint',
    'frontendPrincipalSha256',
    'freshPresenceId',
    'mappingFactFingerprint',
    'projectionDigest',
    'requestHashSha256',
    'sourceCutFingerprint',
    'transcriptDigest',
    'turnIdSha256',
    'witnessDigest',
    'credentialSlot',
    'sealId'
  ];
  for (const field of forbiddenFields) {
    assert.equal(carrierContent.includes(field), false);
    assert.equal(providerBody.includes(field), false);
  }
  for (const value of carrierForbiddenDisclosureValues(config, frontend)) {
    assert.equal(carrierContent.includes(value), false);
  }
  for (const value of providerForbiddenDisclosureValues(config, frontend)) {
    assert.equal(providerBody.includes(value), false);
  }
}

async function runCanonicalProvider({ adapter, config, frontend, label, oneRing }) {
  const ChatCompletionHandler = loadCanonicalHandler(config);
  const observation = {
    binding: null,
    carriers: [],
    fetchCalls: [],
    sealInputs: [],
    sealResults: [],
    trace: []
  };
  const residentModule = observedResidentAdapter(adapter, observation);
  const handler = new ChatCompletionHandler(providerHandlerOptions(
    providerPluginManager({ config, frontend, oneRing, residentModule })
  ));
  const request = new EventEmitter();
  request.aborted = false;
  request.body = {
    requestId: `m4-provider-request-${label.toLowerCase()}`,
    model: 'synthetic-m4-provider-model',
    stream: false,
    messages: [
      {
        role: 'system',
        content:
          `[[OneRing::${frontend.oneRingKey}::${frontend.frontendSource}]]`
      },
      {
        role: 'user',
        content: config.conversation[label].user
      }
    ],
    agentsOsResidentPresenceContext: { requested: true }
  };
  request.headers = {
    accept: 'application/json',
    'user-agent': 'agents-os-resident-m4-synthetic-test'
  };
  request.ip = '127.0.0.1';
  const response = new MockResponse();
  globalThis[FETCH_HARNESS] = async (url, options) => {
    observation.trace.push('fetch');
    observation.fetchCalls.push({
      body: options.body,
      method: options.method,
      url: String(url)
    });
    await new Promise((resolve) => setTimeout(
      resolve,
      config.sessionContract.minimumProviderResponseLatencyMs
    ));
    return new SyntheticUpstreamResponse(completion(
      label,
      config.conversation[label].assistant
    ));
  };
  const originalConsole = {
    error: console.error,
    log: console.log,
    warn: console.warn
  };
  console.error = () => {};
  console.log = () => {};
  console.warn = () => {};
  try {
    await handler.handle(request, response);
    await oneRing.drain();
  } finally {
    console.error = originalConsole.error;
    console.log = originalConsole.log;
    console.warn = originalConsole.warn;
    delete globalThis[FETCH_HARNESS];
  }
  assert.equal(response.statusCode, 200, JSON.stringify({
    bindingObserved: observation.binding !== null,
    carrierCount: observation.carriers.length,
    response: response.text(),
    sealInputCount: observation.sealInputs.length,
    sealResultCount: observation.sealResults.length,
    oneRingMeta: oneRing.diagnostics(),
    trace: observation.trace
  }));
  assert.equal(response.text().includes(config.conversation[label].assistant), true);
  assert.deepEqual(observation.trace, ['seal-start', 'seal-ok', 'fetch']);
  assert.equal(observation.carriers.length, 1);
  assert.equal(observation.sealInputs.length, 1);
  assert.equal(observation.sealResults.length, 1);
  assert.equal(observation.fetchCalls.length, 1);
  assert.equal(observation.fetchCalls[0].method, 'POST');
  assert.equal(
    observation.sealInputs[0].finalBodyText,
    observation.fetchCalls[0].body
  );
  assert.equal(
    observation.sealResults[0].body,
    observation.fetchCalls[0].body
  );
  assert.equal(observation.sealResults[0].seal.providerInvoked, false);
  const providerBody = observation.fetchCalls[0].body;
  const parsedBody = JSON.parse(providerBody);
  assert.equal(Object.hasOwn(parsedBody, 'agentsOsResidentPresenceContext'), false);
  assert.equal(parsedBody.messages.filter(isPresenceCarrierMessage).length, 1);
  const modelFacing = parseCarrier(observation.carriers[0]);
  assert.equal(modelFacing.session.binding, 'BOUND');
  assert.equal(modelFacing.session.availability, 'AVAILABLE');
  assert.equal(modelFacing.admission.admitted, true);
  assert.equal(modelFacing.memory.candidates.length, 1);
  assert.equal(modelFacing.memory.candidates[0].semanticStatus, 'CANDIDATE');
  assert.equal(modelFacing.memory.candidates[0].adopted, false);
  assert.equal(modelFacing.memory.candidates[0].executionAuthority, false);
  assert.equal(modelFacing.memory.candidates[0].promotionAuthority, false);
  assert.equal(modelFacing.memory.items[0].semanticStatus, 'ADOPTED');
  assert.equal(modelFacing.memory.items[0].currentRelation, 'SELECTED');
  assert.equal(modelFacing.memory.items[0].currentness, 'CURRENT');
  assert.equal(modelFacing.memory.items[0].bodyAvailability, 'VERIFIED');
  assert.deepEqual(modelFacing.memory.items[1], {
    authoritative: false,
    bodyAvailability: 'UNKNOWN',
    currentRelation: 'UNKNOWN',
    currentness: 'UNKNOWN',
    memoryRef: null,
    semanticStatus: 'UNMANAGED',
    sourceClass: 'VCP_DAILYNOTE'
  });
  assert.equal(providerBody.includes(config.unmanagedDailyNote.bodyText), true);
  assert.equal(
    observation.carriers[0].content.includes(
      config.unmanagedDailyNote.bodyText
    ),
    false
  );
  assertWorkLife(modelFacing);
  assertLowDisclosure(
    config,
    frontend,
    observation.carriers[0].content,
    providerBody
  );
  return {
    binding: observation.binding,
    bodySha256: sha256Text(providerBody),
    carrier: modelFacing,
    providerMessages: parsedBody.messages,
    seal: observation.sealResults[0].seal,
    trace: observation.trace
  };
}

async function runRejectedCanonicalProvider({ adapter, config, frontend, oneRing }) {
  const ChatCompletionHandler = loadCanonicalHandler(config);
  const pluginManager = providerPluginManager({
    config,
    frontend,
    oneRing,
    residentModule: adapter
  });
  const handler = new ChatCompletionHandler(providerHandlerOptions(pluginManager));
  const request = new EventEmitter();
  request.aborted = false;
  request.body = {
    requestId: 'm4-provider-request-c-negative',
    model: 'synthetic-m4-provider-model',
    stream: false,
    messages: [
      {
        role: 'system',
        content:
          `[[OneRing::${frontend.oneRingKey}::${frontend.frontendSource}]]`
      },
      { role: 'user', content: config.conversation.C.user }
    ],
    agentsOsResidentPresenceContext: { requested: true }
  };
  request.headers = {
    accept: 'application/json',
    'user-agent': 'agents-os-resident-m4-synthetic-negative-test'
  };
  request.ip = '127.0.0.1';
  const response = new MockResponse();
  let fetchCalls = 0;
  globalThis[FETCH_HARNESS] = async () => {
    fetchCalls += 1;
    throw new Error('M4_NEGATIVE_CONTROL_FETCH_FORBIDDEN');
  };
  const originalConsole = {
    error: console.error,
    log: console.log,
    warn: console.warn
  };
  console.error = () => {};
  console.log = () => {};
  console.warn = () => {};
  try {
    await handler.handle(request, response);
    await oneRing.drain();
  } finally {
    console.error = originalConsole.error;
    console.log = originalConsole.log;
    console.warn = originalConsole.warn;
    delete globalThis[FETCH_HARNESS];
  }
  assert.equal(fetchCalls, 0);
  assert.equal(response.statusCode, 500);
  assert.match(response.text(), /RESIDENT_PROVIDER_ATTEMPT_DENIED/u);
  return {
    fetchCalls,
    responseStatus: response.statusCode,
    resultCode: 'RESIDENT_PROVIDER_ATTEMPT_DENIED'
  };
}

function oneRingDatabasePath(config, frontend) {
  return path.join(
    config.oneRingRoot,
    'Plugin',
    'OneRing',
    'data',
    `${frontend.oneRingKey}.db`
  );
}

async function seedForeignOneRingBinding(lifecycle, config) {
  const identityProjection = await lifecycle.queryPresenceContext(
    directPresenceRequest(config, null, 'foreign-initial-identity')
  );
  const admittedIdentity = identityProjection.identity.opaqueId;
  const generation = identityProjection.identity.authorityGeneration;
  const foreignIdentity = config.foreign.foreignIdentity;
  assert.notEqual(foreignIdentity, admittedIdentity);
  await applyMmr(lifecycle, stateMutation(config, {
    content: oneRingContent(config, foreignIdentity, generation),
    expectedCurrentFingerprint: null,
    mutationType: 'CREATE',
    operationId: `operation:M4:onering:foreign:${config.runId.slice(0, 24)}`,
    targetStateId: ONERING_ID
  }));
  const presenceRequest = directPresenceRequest(
    config,
    config.frontends[0],
    'foreign-different-identity-negative'
  );
  const presence = await lifecycle.queryPresenceContext(presenceRequest);
  assert.equal(presence.identity.opaqueId, admittedIdentity);
  assert.equal(presence.oneRing.binding, 'MISMATCH');
  assert.equal(presence.oneRing.sessionAvailability, 'UNKNOWN');
  assert.equal(presence.providerAttemptEligible, false);
  return {
    admittedIdentity,
    foreignIdentity,
    presence,
    presenceRequest
  };
}

function exactSlotsFrom(presence) {
  return {
    lifeFactFingerprint: null,
    memoryFactFingerprint: presence.memory.mappingFactFingerprint,
    oneRingFactFingerprint: presence.oneRing.factFingerprint,
    workSourceCutFingerprint: presence.work.sourceCutFingerprint
  };
}

function assertFinalNativePresence(presence, config) {
  assert.equal(presence.accepted, true);
  assert.equal(presence.witness.admitted, true);
  assert.ok(['MATCH', 'LOCAL_DESCENDS_FROM_WITNESS'].includes(
    presence.witness.relation
  ));
  assert.equal(presence.oneRing.binding, 'BOUND');
  assert.equal(presence.oneRing.bindingStatus, 'ACTIVE');
  assert.equal(presence.oneRing.sessionAvailability, 'AVAILABLE');
  assert.equal(presence.providerAttemptEligible, true);
  assert.equal(presence.memory.adopted.authorityRelation, 'ADOPTED');
  assert.equal(presence.memory.adopted.currentRelation, 'SELECTED');
  assert.equal(presence.memory.adopted.currentness, 'CURRENT');
  assert.equal(presence.memory.adopted.bodyAvailability, 'VERIFIED');
  assert.equal(presence.memory.adopted.bodyRef, null);
  assert.equal(presence.memory.adopted.bodySha256, null);
  assert.equal(presence.memory.adopted.memoryId, config.memoryId);
  assert.equal(presence.memory.candidates.length, 1);
  assert.equal(presence.memory.candidates[0].candidateId, config.candidateId);
  assert.equal(presence.memory.candidates[0].candidateStatus, 'CANDIDATE');
  assert.equal(presence.memory.candidates[0].adopted, false);
  assert.equal(presence.memory.candidates[0].executionAuthority, false);
  assert.equal(presence.memory.candidates[0].promotionAuthority, false);
  assert.equal(presence.work.currentness, 'CURRENT');
  assert.equal(presence.work.sourceAvailability, 'AVAILABLE');
  const last = presence.work.facts.find(
    ({ category }) => category === 'LAST_VALIDATED_RESULT'
  );
  assert.equal(last.categoryState, 'PRESENT');
  assert.equal(last.factCurrentness, 'CURRENT');
  assert.match(last.boundedRef, /^validation-result:sha256:/u);
  assert.match(last.subjectRef, /^work-subject:v1:/u);
  assert.match(last.validationRef, /^work-validation:v1:/u);
  for (const category of [
    'ACTIVE_COMMITMENT',
    'CURRENT_FOCUS_PROJECT_TASK',
    'NEXT_STEP',
    'WAITING_OR_BLOCKER'
  ]) {
    const fact = presence.work.facts.find((entry) => entry.category === category);
    assert.equal(fact.categoryState, 'UNKNOWN');
    assert.equal(fact.factCurrentness, 'UNKNOWN');
  }
  assert.equal(presence.life.categoryState, 'UNKNOWN');
  assert.equal(presence.life.currentness, 'UNKNOWN');
  assert.equal(
    presence.life.currentnessReason,
    'NO_ACCEPTED_CLOSED_WORLD_LIFE_SOURCE'
  );
  const serialized = JSON.stringify(presence);
  for (const sentinel of [
    config.bodyText.trim(),
    ...Object.values(config.workSentinels)
  ]) {
    assert.equal(serialized.includes(sentinel), false);
  }
}

async function rejectUnauthorizedMemorySelection({
  lifecycle,
  config,
  identity,
  generation,
  inventoryFingerprint,
  snapshotRequest
}) {
  const before = await authoritySnapshot(lifecycle, config, snapshotRequest);
  assert.equal(before.memoryAuthority.current, null);
  assert.equal(
    before.inventory.current.state.components.content.value.adoptedMemoryId,
    null
  );
  assert.ok(before.memoryBodies.some(({ path: entryPath }) =>
    entryPath.endsWith('.body')));
  const rejected = stateMutation(config, {
    content: inventoryContent(config, identity, generation, config.memoryId),
    expectedCurrentFingerprint: inventoryFingerprint,
    mutationType: 'REVISE',
    operationId:
      `operation:M4:memory:inventory:rejected:${config.runId.slice(0, 24)}`,
    targetStateId: INVENTORY_ID
  });
  let error = null;
  try {
    await lifecycle.prepareMmrMutation(rejected.request);
  } catch (caught) {
    error = caught;
  }
  assert.ok(error);
  assert.equal(
    error.message,
    'AGENTS_OS_BOUNDARY_REJECTED: MEMORY_AUTHORITY_PROFILE_REJECTED'
  );
  const after = await authoritySnapshot(lifecycle, config, snapshotRequest);
  assert.deepEqual(after, before);
  return {
    error: error.message,
    zeroSideEffect: true
  };
}

async function seedWriterA(lifecycle, config) {
  const initial = await lifecycle.queryPresenceContext(
    directPresenceRequest(config, null, 'initial-identity')
  );
  const identity = initial.identity.opaqueId;
  const generation = initial.identity.authorityGeneration;
  const writer = new MemoryBodyWriter({
    bodyRoot: config.memoryBodyRoot,
    expectedIdentityOpaqueId: identity,
    residentRoot: config.residentRoot
  });
  const publication = writer.publish({
    body: Buffer.from(config.bodyText, 'utf8'),
    memoryId: config.memoryId,
    operationRef: `operation:M4:memory-body:${config.runId.slice(0, 24)}`
  });
  writer.close();
  assert.equal(publication.receipt.authoritative, false);
  assert.equal(publication.receipt.current, false);
  assert.equal(publication.receipt.verificationStatus, 'UNVERIFIED_WRITER_RECEIPT');

  await applyMmr(
    lifecycle,
    candidateMutation(config, identity, generation, publication.descriptor)
  );
  const candidate = await queryCore(
    lifecycle,
    'QUERY_MMR_CANDIDATE_CORE',
    { stateId: config.candidateId }
  );
  assert.equal(candidate.current.state.candidateState.status, 'CANDIDATE');
  const candidateFingerprint = candidate.current.factFingerprint;

  await applyMmr(lifecycle, stateMutation(config, {
    content: inventoryContent(config, identity, generation, null),
    expectedCurrentFingerprint: null,
    mutationType: 'CREATE',
    operationId:
      `operation:M4:memory:inventory:candidate-only:${config.runId.slice(0, 24)}`,
    targetStateId: INVENTORY_ID
  }));
  await createValidatedWork(lifecycle, config);

  const candidateOnlyRequest = directPresenceRequest(
    config,
    null,
    'candidate-only-rejection-snapshot'
  );
  const candidateOnly = await lifecycle.queryPresenceContext(candidateOnlyRequest);
  assert.equal(candidateOnly.memory.adopted.authorityRelation, null);
  assert.equal(candidateOnly.memory.candidates.length, 1);
  assert.equal(candidateOnly.memory.candidates[0].candidateStatus, 'CANDIDATE');
  assert.equal(candidateOnly.memory.candidates[0].adopted, false);
  const currentInventory = await queryCore(
    lifecycle,
    'QUERY_MMR_CURRENT_CORE',
    { stateId: INVENTORY_ID }
  );
  const rejection = await rejectUnauthorizedMemorySelection({
    lifecycle,
    config,
    identity,
    generation,
    inventoryFingerprint: currentInventory.current.factFingerprint,
    snapshotRequest: candidateOnlyRequest
  });

  await applyMmr(lifecycle, stateMutation(config, {
    content: memoryAuthorityContent(
      config,
      identity,
      generation,
      publication.descriptor,
      candidateFingerprint
    ),
    expectedCurrentFingerprint: null,
    mutationType: 'CREATE',
    operationId: `operation:M4:memory:adopt:${config.runId.slice(0, 24)}`,
    targetStateId: config.memoryId
  }));
  const inventoryAfterAuthority = await queryCore(
    lifecycle,
    'QUERY_MMR_CURRENT_CORE',
    { stateId: INVENTORY_ID }
  );
  await applyMmr(lifecycle, stateMutation(config, {
    content: inventoryContent(config, identity, generation, config.memoryId),
    expectedCurrentFingerprint:
      inventoryAfterAuthority.current.factFingerprint,
    mutationType: 'REVISE',
    operationId:
      `operation:M4:memory:inventory:select:${config.runId.slice(0, 24)}`,
    targetStateId: INVENTORY_ID
  }));

  await applyMmr(lifecycle, stateMutation(config, {
    content: oneRingContent(config, identity, generation),
    expectedCurrentFingerprint: null,
    mutationType: 'CREATE',
    operationId: `operation:M4:onering:${config.runId.slice(0, 24)}`,
    targetStateId: ONERING_ID
  }));
  return { identity, generation, publication, rejection };
}

async function exactPresence(lifecycle, config, frontend, label) {
  const preliminary = await lifecycle.queryPresenceContext(
    directPresenceRequest(config, frontend, `${label}-preliminary`)
  );
  assertFinalNativePresence(preliminary, config);
  const exactSlots = exactSlotsFrom(preliminary);
  const request = {
    ...directPresenceRequest(config, frontend, `${label}-exact`),
    expectedSlots: exactSlots
  };
  const exact = await lifecycle.queryPresenceContext(request);
  assertFinalNativePresence(exact, config);
  return { exact, exactSlots, request };
}

async function startWorkerRuntime(role, config) {
  const lifecycle = createResidentLifecycle();
  const integrity = verifyCompanionIntegrity();
  let server = null;
  let adapter = null;
  let oneRing = null;
  let closed = false;
  try {
    const activation = await lifecycle.initialize(activationConfig(config));
    assert.equal(activation.continuityAdmission.result, 'PASS');
    assert.ok(['MATCH', 'LOCAL_DESCENDS_FROM_WITNESS'].includes(
      activation.continuityAdmission.relation
    ));
    let seed = null;
    if (role === 'A') seed = await seedWriterA(lifecycle, config);
    const frontend = config.frontends[role === 'B' ? 1 : 0];
    const negative = role === 'C'
      ? await seedForeignOneRingBinding(lifecycle, config)
      : null;
    const exact = role === 'C'
      ? null
      : await exactPresence(lifecycle, config, frontend, role);
    const presenceRequest = negative?.presenceRequest || exact.request;
    const statusBeforeServer = await lifecycle.status();
    server = createCompanionServer({
      activationConfig: activationConfig(config),
      integrity,
      lifecycle,
      socketPath: config.sockets[role]
    });
    await server.start();
    adapter = createResidentAdapter({
      createClient: () => createCompanionClient({
        authenticateDaemon(_socket, _socketPath, { expectedPid } = {}) {
          return Object.freeze({ pid: expectedPid ?? process.pid });
        },
        integrity,
        socketPath: config.sockets[role]
      })
    });
    const attached = await adapter.initialize();
    assert.equal(attached.activationState, 'ACTIVE_LOCAL_OWNER');
    oneRing = createSelectedOneRing(config, frontend);
    const beforeProvider = await authoritySnapshot(
      lifecycle,
      config,
      presenceRequest
    );
    const provider = role === 'C'
      ? await runRejectedCanonicalProvider({
        adapter,
        config,
        frontend,
        oneRing
      })
      : await runCanonicalProvider({
        adapter,
        config,
        frontend,
        label: role,
        oneRing
      });
    const afterProvider = await authoritySnapshot(
      lifecycle,
      config,
      presenceRequest
    );
    assert.deepEqual(afterProvider, beforeProvider);
    if (role === 'C') {
      assert.equal(negative.presence.oneRing.binding, 'MISMATCH');
      assert.equal(negative.presence.oneRing.sessionAvailability, 'UNKNOWN');
      assert.equal(negative.presence.providerAttemptEligible, false);
      assert.equal(provider.fetchCalls, 0);
    } else {
      assert.equal(
        provider.carrier.identity.opaqueRef,
        exact.exact.identity.opaqueId
      );
    }
    assert.equal((await lifecycle.status()).providerEnabled, false);
    const oneRingRows = oneRing.readRecent(config.sessionContract.maxDbRecords);
    const oneRingRuntime = oneRing.runtimeDependency();

    const shutdown = async () => {
      if (closed) return;
      closed = true;
      let firstError = null;
      try { await oneRing?.drain(); } catch (error) { firstError = error; }
      try { await adapter?.shutdown(); } catch {}
      try {
        if (server) await server.stop();
        else await lifecycle.shutdown();
      } catch (error) {
        firstError ||= error;
      }
      try { oneRing?.shutdown(); } catch (error) { firstError ||= error; }
      if (firstError) throw firstError;
    };
    const ready = {
      pid: process.pid,
      role,
      status: statusBeforeServer,
      exactPresence: exact?.exact || null,
      exactSlots: exact?.exactSlots || null,
      negative: negative ? {
        admittedIdentity: negative.admittedIdentity,
        foreignIdentity: negative.foreignIdentity,
        presence: negative.presence,
        provider
      } : null,
      oneRingRows,
      oneRingRuntime,
      provider,
      snapshot: afterProvider,
      rejectedMutation: seed?.rejection || null
    };
    process.send?.({ event: 'READY', ready });
    process.on('message', async (message) => {
      if (message?.command === 'PROBE') {
        try {
          process.send?.({
            event: 'RESPONSE',
            requestId: message.requestId,
            result: {
              server: server.getServerStatus(),
              status: await lifecycle.status(),
              snapshot: await authoritySnapshot(
                lifecycle,
                config,
                presenceRequest
              )
            }
          });
        } catch (error) {
          process.send?.({
            event: 'RESPONSE',
            requestId: message.requestId,
            error: error.stack || error.message
          });
        }
      }
      if (message?.command === 'STOP') {
        try {
          await shutdown();
          process.send?.({
            event: 'RESPONSE',
            requestId: message.requestId,
            result: { stopped: true }
          });
          process.disconnect?.();
          setImmediate(() => process.exit(0));
        } catch (error) {
          process.send?.({
            event: 'RESPONSE',
            requestId: message.requestId,
            error: error.stack || error.message
          });
          setImmediate(() => process.exit(1));
        }
      }
    });
    process.once('disconnect', () => {
      void shutdown().finally(() => process.exit(0));
    });
  } catch (error) {
    try { await oneRing?.drain(); } catch {}
    try { await adapter?.shutdown(); } catch {}
    try {
      if (server) await server.stop();
      else await lifecycle.shutdown();
    } catch {}
    try { oneRing?.shutdown(); } catch {}
    process.send?.({ event: 'FAILED', error: error.stack || error.message });
    process.exitCode = 1;
  }
}

function workerConfig() {
  return JSON.parse(Buffer.from(
    process.env.AGENTS_OS_M4_WORKER_CONFIG,
    'base64url'
  ).toString('utf8'));
}

function childDiagnostics(child) {
  return {
    stderr: child.__stderr || '',
    stdout: child.__stdout || ''
  };
}

function spawnWorker(role, config) {
  const child = fork(__filename, [], {
    cwd: PACKAGE_ROOT,
    env: {
      ...process.env,
      AGENTS_OS_M4_WORKER_MODE: role,
      AGENTS_OS_M4_WORKER_CONFIG:
        Buffer.from(JSON.stringify(config), 'utf8').toString('base64url')
    },
    stdio: ['ignore', 'pipe', 'pipe', 'ipc']
  });
  child.__stdout = '';
  child.__stderr = '';
  child.stdout.on('data', (chunk) => { child.__stdout += chunk.toString('utf8'); });
  child.stderr.on('data', (chunk) => { child.__stderr += chunk.toString('utf8'); });
  return child;
}

function waitForReady(child, timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      cleanup();
      reject(Object.assign(new Error('M4_WORKER_READY_TIMEOUT'), {
        diagnostics: childDiagnostics(child)
      }));
    }, timeoutMs);
    const onMessage = (message) => {
      if (message?.event === 'READY') {
        cleanup();
        resolve(message.ready);
      } else if (message?.event === 'FAILED') {
        cleanup();
        reject(Object.assign(new Error(message.error), {
          diagnostics: childDiagnostics(child)
        }));
      }
    };
    const onExit = (code, signal) => {
      cleanup();
      reject(Object.assign(
        new Error(`M4_WORKER_EXITED_BEFORE_READY:${code}:${signal}`),
        { diagnostics: childDiagnostics(child) }
      ));
    };
    function cleanup() {
      clearTimeout(timer);
      child.off('message', onMessage);
      child.off('exit', onExit);
    }
    child.on('message', onMessage);
    child.once('exit', onExit);
  });
}

function commandWorker(child, command, timeoutMs = 15000) {
  const requestId = randomBytes(16).toString('hex');
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      cleanup();
      reject(Object.assign(new Error(`M4_WORKER_${command}_TIMEOUT`), {
        diagnostics: childDiagnostics(child)
      }));
    }, timeoutMs);
    const onMessage = (message) => {
      if (message?.event !== 'RESPONSE' || message.requestId !== requestId) return;
      cleanup();
      if (message.error) reject(new Error(message.error));
      else resolve(message.result);
    };
    function cleanup() {
      clearTimeout(timer);
      child.off('message', onMessage);
    }
    child.on('message', onMessage);
    child.send({ command, requestId });
  });
}

function waitForExit(child, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    if (child.exitCode !== null) {
      resolve({ code: child.exitCode, signal: child.signalCode });
      return;
    }
    const timer = setTimeout(() => reject(new Error('M4_CHILD_EXIT_TIMEOUT')), timeoutMs);
    child.once('exit', (code, signal) => {
      clearTimeout(timer);
      resolve({ code, signal });
    });
  });
}

function runDuplicateWriter(config, integrity) {
  return spawnSync(process.execPath, [
    DAEMON_PATH,
    '--root', config.residentRoot,
    '--socket', config.sockets.duplicate,
    '--expected-build-id', integrity.buildId,
    '--witness-root', config.witnessRoot,
    '--memory-body-root', config.memoryBodyRoot
  ], {
    cwd: PACKAGE_ROOT,
    encoding: 'utf8',
    env: { ...process.env },
    timeout: 15000
  });
}

async function stopWorker(child) {
  const result = await commandWorker(child, 'STOP');
  assert.deepEqual(result, { stopped: true });
  assert.deepEqual(await waitForExit(child), { code: 0, signal: null });
}

function sentinelIndexes(messages, sentinel) {
  return messages.flatMap((message, index) => {
    const content = typeof message?.content === 'string'
      ? message.content
      : JSON.stringify(message?.content ?? null);
    return content.includes(sentinel) ? [index] : [];
  });
}

function oneRingRowIndexes(rows, sentinel) {
  return rows.flatMap((row, index) =>
    row.content.includes(sentinel) ? [index] : []);
}

function assertRestartContinuity(a, b, config) {
  assert.notEqual(a.pid, b.pid);
  assert.notEqual(
    a.provider.binding.freshPresenceId,
    b.provider.binding.freshPresenceId
  );
  assert.notEqual(a.provider.binding.contextId, b.provider.binding.contextId);
  assert.equal(a.status.incarnationId, b.status.incarnationId);
  assert.deepEqual(a.status.continuityAnchor, b.status.continuityAnchor);
  assert.equal(a.status.continuityAdmission.result, 'PASS');
  assert.equal(b.status.continuityAdmission.result, 'PASS');
  assert.ok(['MATCH', 'LOCAL_DESCENDS_FROM_WITNESS'].includes(
    b.status.continuityAdmission.relation
  ));
  assert.equal(
    a.exactPresence.identity.opaqueId,
    b.exactPresence.identity.opaqueId
  );
  assert.equal(
    a.exactPresence.identity.authorityGeneration,
    b.exactPresence.identity.authorityGeneration
  );
  assert.deepEqual(a.exactSlots, b.exactSlots);
  assert.deepEqual(a.snapshot.persistence, b.snapshot.persistence);
  assert.deepEqual(a.snapshot.candidate, b.snapshot.candidate);
  assert.deepEqual(a.snapshot.inventory, b.snapshot.inventory);
  assert.deepEqual(a.snapshot.memoryAuthority, b.snapshot.memoryAuthority);
  assert.deepEqual(a.exactPresence.memory, b.exactPresence.memory);
  assert.deepEqual(a.exactPresence.work, b.exactPresence.work);
  assert.deepEqual(a.exactPresence.life, b.exactPresence.life);
  assert.equal(
    a.exactPresence.oneRing.factFingerprint,
    b.exactPresence.oneRing.factFingerprint
  );
  assert.equal(
    a.exactPresence.oneRing.externalKeySha256,
    `sha256:${config.frontends[0].externalKeyDigest}`
  );
  assert.equal(
    b.exactPresence.oneRing.externalKeySha256,
    `sha256:${config.frontends[1].externalKeyDigest}`
  );
  assert.notEqual(
    a.exactPresence.oneRing.frontendPrincipalSha256,
    b.exactPresence.oneRing.frontendPrincipalSha256
  );
  assert.equal(
    a.provider.carrier.identity.opaqueRef,
    b.provider.carrier.identity.opaqueRef
  );
  assert.deepEqual(a.provider.carrier.memory, b.provider.carrier.memory);
  assert.deepEqual(a.provider.carrier.workLife, b.provider.carrier.workLife);
  assert.equal(config.frontends[0].displayName, config.frontends[1].displayName);
  assert.equal(config.frontends[0].oneRingKey, config.frontends[1].oneRingKey);
  assert.equal(
    config.frontends[0].externalKeyDigest,
    config.frontends[1].externalKeyDigest
  );

  const aUserInA = oneRingRowIndexes(
    a.oneRingRows,
    config.conversation.A.user
  );
  const aAssistantInA = oneRingRowIndexes(
    a.oneRingRows,
    config.conversation.A.assistant
  );
  assert.equal(aUserInA.length, 1);
  assert.equal(aAssistantInA.length, 1);

  const requiredProviderOrder = [
    config.conversation.A.user,
    config.conversation.A.assistant,
    config.conversation.B.user
  ].map((sentinel) => {
    const indexes = sentinelIndexes(b.provider.providerMessages, sentinel);
    assert.equal(indexes.length, 1);
    return indexes[0];
  });
  assert.deepEqual(config.sessionContract.requiredOrder, [
    'A_USER',
    'A_ASSISTANT',
    'B_USER'
  ]);
  const providerOrderDiagnostics = JSON.stringify({
    indexes: requiredProviderOrder,
    roles: b.provider.providerMessages.map(({ role }) => role)
  });
  assert.ok(
    requiredProviderOrder[0] < requiredProviderOrder[1],
    providerOrderDiagnostics
  );
  assert.ok(
    requiredProviderOrder[1] < requiredProviderOrder[2],
    providerOrderDiagnostics
  );

  for (const sentinel of [
    config.conversation.A.user,
    config.conversation.A.assistant,
    config.conversation.B.user,
    config.conversation.B.assistant
  ]) {
    assert.equal(oneRingRowIndexes(b.oneRingRows, sentinel).length, 1);
  }
}

if (WORKER_MODE !== null) {
  void startWorkerRuntime(WORKER_MODE, workerConfig());
} else {
  test('M4 process-level Fresh Presence synthetic proof', {
    concurrency: false,
    timeout: 180000
  }, async (t) => {
    const quarantine = mkdtempSync(path.join(tmpdir(), 'agents-os-resident-m4-'));
    const config = fixtureConfig({
      quarantine,
      runId: randomBytes(32).toString('hex')
    });
    const foreign = foreignConfig(config);
    createProtectedDirectories(config);
    createProtectedDirectories(foreign);
    createIsolatedVcpFixtures(config);
    const integrity = verifyCompanionIntegrity();
    const children = new Set();
    t.after(async () => {
      for (const child of children) {
        if (child.exitCode === null) {
          child.kill('SIGTERM');
          try { await waitForExit(child, 5000); } catch { child.kill('SIGKILL'); }
        }
      }
      rmSync(quarantine, { recursive: true, force: true });
    });

    runProvision(config, integrity);
    runProvision(foreign, integrity);
    assert.equal(mode(config.residentRoot), 0o700);
    assert.equal(mode(config.witnessRoot), 0o700);
    assert.equal(mode(config.memoryBodyRoot), 0o700);
    const witnessAfterProvision = witnessSnapshot(config);
    const foreignWitnessAfterProvision = witnessSnapshot(foreign);

    const writerA = spawnWorker('A', config);
    children.add(writerA);
    const a = await waitForReady(writerA);
    assert.equal(a.pid, writerA.pid);
    assert.equal(a.status.lockHeld, true);
    assert.equal(a.oneRingRuntime.packageVersion, '12.4.1');
    assert.match(a.oneRingRuntime.nativeBindingSha256, /^[0-9a-f]{64}$/u);
    assert.equal(a.exactPresence.providerAttemptEligible, true);
    assert.equal(a.status.providerEnabled, false);
    assert.equal(a.rejectedMutation.zeroSideEffect, true);
    assert.equal(
      a.rejectedMutation.error,
      'AGENTS_OS_BOUNDARY_REJECTED: MEMORY_AUTHORITY_PROFILE_REJECTED'
    );
    assert.equal(
      a.snapshot.memoryAuthority.current.state.components.content.value
        .authorityStatus,
      'ADOPTED'
    );
    assert.equal(
      a.snapshot.inventory.current.state.components.content.value
        .adoptedMemoryId,
      config.memoryId
    );
    assert.deepEqual(witnessSnapshot(config), witnessAfterProvision);

    const duplicate = runDuplicateWriter(config, integrity);
    assert.equal(duplicate.error, undefined);
    assert.equal(duplicate.status, 73);
    assert.equal(duplicate.signal, null);
    assert.equal(duplicate.stdout, '');
    assert.equal(duplicate.stderr, '');
    assert.equal(existsSync(config.sockets.duplicate), false);
    const aAfterDuplicate = await commandWorker(writerA, 'PROBE');
    assert.equal(aAfterDuplicate.server.listening, true);
    assert.equal(aAfterDuplicate.server.adapterAttachmentState, 'ATTACHED');
    assert.equal(aAfterDuplicate.status.lockHeld, true);
    assert.deepEqual(aAfterDuplicate.status.continuityAnchor, a.status.continuityAnchor);
    assert.deepEqual(aAfterDuplicate.snapshot, a.snapshot);
    assert.deepEqual(witnessSnapshot(config), witnessAfterProvision);

    await stopWorker(writerA);
    const writerB = spawnWorker('B', config);
    children.add(writerB);
    const b = await waitForReady(writerB);
    assert.equal(b.pid, writerB.pid);
    assert.equal(b.status.lockHeld, true);
    assert.deepEqual(b.oneRingRuntime, a.oneRingRuntime);
    assertRestartContinuity(a, b, config);
    assert.deepEqual(witnessSnapshot(config), witnessAfterProvision);
    await stopWorker(writerB);
    assert.deepEqual(witnessSnapshot(config), witnessAfterProvision);

    const primaryOneRingPath = oneRingDatabasePath(
      config,
      config.frontends[0]
    );
    const foreignOneRingPath = oneRingDatabasePath(
      foreign,
      foreign.frontends[0]
    );
    assert.equal(existsSync(primaryOneRingPath), true);
    assert.notEqual(primaryOneRingPath, foreignOneRingPath);
    const primaryOneRingBeforeNegative = snapshotFile(primaryOneRingPath);
    const primaryResidentBeforeNegative = snapshotFile(config.databasePath);

    const writerC = spawnWorker('C', foreign);
    children.add(writerC);
    const c = await waitForReady(writerC);
    assert.equal(c.pid, writerC.pid);
    assert.notEqual(c.pid, a.pid);
    assert.notEqual(c.pid, b.pid);
    assert.equal(c.status.lockHeld, true);
    assert.deepEqual(c.oneRingRuntime, a.oneRingRuntime);
    assert.equal(
      foreign.frontends[0].displayName,
      config.frontends[0].displayName
    );
    assert.notEqual(
      foreign.frontends[0].oneRingKey,
      config.frontends[0].oneRingKey
    );
    assert.notEqual(
      foreign.frontends[0].externalKeyDigest,
      config.frontends[0].externalKeyDigest
    );
    assert.notEqual(c.negative.foreignIdentity, a.exactPresence.identity.opaqueId);
    assert.equal(
      c.negative.admittedIdentity,
      c.negative.presence.identity.opaqueId
    );
    assert.equal(c.negative.presence.oneRing.binding, 'MISMATCH');
    assert.equal(c.negative.presence.oneRing.sessionAvailability, 'UNKNOWN');
    assert.equal(c.negative.presence.providerAttemptEligible, false);
    assert.deepEqual(
      c.negative.presence.capabilities,
      a.exactPresence.capabilities
    );
    assert.equal(c.negative.provider.fetchCalls, 0);
    assert.equal(c.negative.provider.responseStatus, 500);
    assert.equal(
      c.negative.provider.resultCode,
      'RESIDENT_PROVIDER_ATTEMPT_DENIED'
    );
    assert.equal(existsSync(foreignOneRingPath), true);
    assert.equal(
      oneRingRowIndexes(c.oneRingRows, config.conversation.C.user).length,
      1
    );
    for (const sentinel of [
      config.conversation.A.user,
      config.conversation.A.assistant,
      config.conversation.B.user,
      config.conversation.B.assistant
    ]) {
      assert.equal(oneRingRowIndexes(c.oneRingRows, sentinel).length, 0);
    }
    assert.deepEqual(
      snapshotFile(primaryOneRingPath),
      primaryOneRingBeforeNegative
    );
    assert.deepEqual(
      snapshotFile(config.databasePath),
      primaryResidentBeforeNegative
    );
    assert.deepEqual(witnessSnapshot(config), witnessAfterProvision);
    assert.deepEqual(witnessSnapshot(foreign), foreignWitnessAfterProvision);
    await stopWorker(writerC);
    assert.deepEqual(
      snapshotFile(primaryOneRingPath),
      primaryOneRingBeforeNegative
    );
    assert.deepEqual(witnessSnapshot(config), witnessAfterProvision);
    assert.deepEqual(witnessSnapshot(foreign), foreignWitnessAfterProvision);
  });
}
