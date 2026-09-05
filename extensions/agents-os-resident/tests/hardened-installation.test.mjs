import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  chmodSync,
  existsSync,
  linkSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  symlinkSync,
  writeFileSync
} from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  applyIdentityPlan,
  applyStageOnly,
  createInstallationObservationReceipt,
  createIdentityPlan,
  loadInstallationContract,
  observeFilesystemPath,
  previewInstallation,
  previewInstallationObservationRequest
} from '../tools/stage-hardened-installation.mjs';

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function canonicalDigest(value) {
  const walk = (input) => Array.isArray(input) ? input.map(walk)
    : input !== null && typeof input === 'object'
      ? Object.fromEntries(Object.keys(input).sort().map((key) => [key, walk(input[key])]))
      : input;
  return `sha256:${sha256(Buffer.from(JSON.stringify(walk(value)), 'utf8'))}`;
}

function fixture(t) {
  const root = mkdtempSync(path.join(tmpdir(), 'resident-two-stage-install-'));
  chmodSync(root, 0o700);
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const virtualOwnership = new Map();
  for (const directory of ['opt', 'etc', 'etc/systemd', 'etc/systemd/system', 'var', 'var/lib']) {
    const destination = path.join(root, directory);
    mkdirSync(destination, { mode: 0o755 });
    virtualOwnership.set(destination, { uid: 0, gid: 0 });
  }

  const contract = clone(loadInstallationContract());
  contract.paths.packageRoot = path.join(root, 'opt/agents-os-resident');
  contract.paths.configRoot = path.join(root, 'etc/agents-os-resident');
  contract.paths.stateRoot = path.join(root, 'var/lib/agents-os-resident');
  contract.paths.residentRoot = path.join(contract.paths.stateRoot, 'agents-os-resident-local-owner-v1');
  contract.paths.witnessRoot = path.join(contract.paths.stateRoot, 'protected-witness');
  contract.paths.memoryBodyRoot = path.join(contract.paths.stateRoot, 'private-memory-bodies');
  contract.paths.daemonIdentity = path.join(contract.paths.configRoot, 'daemon-identity.json');
  contract.paths.systemUnit = path.join(root, 'etc/systemd/system/agents-os-resident.service');
  contract.paths.nodeBinary = path.join(
    contract.paths.packageRoot, 'runtime/node-v22.23.1-linux-x64/bin/node'
  );

  const archiveTree = path.join(root, 'archive');
  const distribution = path.join(archiveTree, 'node-v22.23.1-linux-x64');
  mkdirSync(path.join(distribution, 'bin'), { recursive: true, mode: 0o700 });
  const fixtureNode = Buffer.from('#!/bin/sh\nprintf "v22.23.1\\n"\n', 'utf8');
  writeFileSync(path.join(distribution, 'bin/node'), fixtureNode, { mode: 0o700 });
  const archive = path.join(root, 'node-v22.23.1-linux-x64.tar.xz');
  const repack = () => {
    const result = spawnSync('/usr/bin/tar', [
      '-cJf', archive, '-C', archiveTree, 'node-v22.23.1-linux-x64'
    ], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    contract.nodeRuntime.sha256 = sha256(readFileSync(archive));
  };
  repack();

  const state = {
    daemonUser: null,
    daemonGroup: null,
    clientGroup: null,
    clientUser: {
      name: 'fixture-client',
      uid: process.getuid() + 10000,
      groupNames: ['fixture-client']
    }
  };
  const operations = [];
  let failIdentityKind = null;
  let denyProtectedObservation = false;
  const named = () => ({
    daemonUser: state.daemonUser,
    daemonGroup: state.daemonGroup,
    clientGroup: state.clientGroup
  });
  const adapter = {
    inspectNamedIdentities() { return named(); },
    inspectInstallationIdentities() { return state; },
    applyIdentityOperation(operation) {
      if (operation.kind === failIdentityKind) throw new Error('FIXTURE_IDENTITY_FAILURE');
      operations.push(['identity', operation.kind, operation.executable, ...operation.argv]);
      if (operation.kind === 'create-daemon-group') {
        state.daemonGroup = {
          name: contract.identities.daemonGroup, gid: 3101, members: [], systemGroup: true
        };
      } else if (operation.kind === 'create-client-group') {
        state.clientGroup = {
          name: contract.identities.clientGroup, gid: 3102, members: [], systemGroup: true
        };
      } else if (operation.kind === 'create-daemon-user') {
        state.daemonUser = {
          name: contract.identities.daemonUser,
          uid: process.getuid(),
          gid: state.daemonGroup.gid,
          home: contract.identities.daemonHome,
          shell: contract.identities.daemonShell,
          systemAccount: true,
          supplementaryGids: [state.daemonGroup.gid]
        };
      }
    },
    observeFilesystemPath(destination) {
      if (denyProtectedObservation && path.relative(contract.paths.stateRoot, destination)
        .split(path.sep)[0] !== '..') {
        throw new Error('INSTALL_PRIVILEGED_OBSERVATION_REQUIRED');
      }
      const observed = observeFilesystemPath(destination);
      const owner = virtualOwnership.get(destination);
      return owner === undefined || !observed.exists ? observed : { ...observed, ...owner };
    },
    ensureMembership(membership) {
      operations.push(['membership', membership.user, membership.group, membership.operation]);
      if (!state.clientUser.groupNames.includes(membership.group)) {
        state.clientUser.groupNames.push(membership.group);
      }
    },
    ensureDirectory(destination, mode, uid, gid) {
      operations.push(['directory', destination, mode, uid, gid]);
      if (!existsSync(destination)) mkdirSync(destination, { mode });
      chmodSync(destination, mode);
      virtualOwnership.set(destination, { uid, gid });
    },
    installFile(destination, bytes, mode, uid, gid) {
      operations.push(['file', destination, mode, uid, gid]);
      writeFileSync(destination, bytes, { mode });
      chmodSync(destination, mode);
      virtualOwnership.set(destination, { uid, gid });
    },
    installNode(destination, bytes, mode, uid, gid) {
      operations.push(['node', destination, mode, uid, gid]);
      if (!existsSync(destination)) writeFileSync(destination, bytes, { mode });
      chmodSync(destination, mode);
      virtualOwnership.set(destination, { uid, gid });
    },
    installControlFile(destination, bytes, mode, uid, gid) {
      operations.push(['control-file', destination, mode, uid, gid]);
      if (existsSync(destination) && readFileSync(destination).equals(bytes)) return;
      writeFileSync(destination, bytes, { mode });
      chmodSync(destination, mode);
      virtualOwnership.set(destination, { uid, gid });
    },
    verifyNodeVersion(destination, expected) {
      operations.push(['node-version', destination, expected]);
      const result = spawnSync(destination, ['--version'], { encoding: 'utf8' });
      assert.equal(result.status, 0, result.stderr);
      assert.equal(result.stdout.trim(), expected);
    },
    prepareRoots(config) {
      operations.push(['prepare-roots']);
      const stagedRequire = createRequire(path.join(config.packageRoot, 'package.json'));
      const daemon = stagedRequire('./companion/resident-daemon.js');
      daemon.prepareResidentRoots({ argv: [
        '--operation', 'prepare-roots',
        '--root', config.residentRoot,
        '--witness-root', config.witnessRoot,
        '--memory-body-root', config.memoryBodyRoot,
        '--expected-build-id', config.buildId
      ] });
      for (const destination of [config.residentRoot, config.witnessRoot, config.memoryBodyRoot]) {
        virtualOwnership.set(destination, { uid: state.daemonUser.uid, gid: state.daemonGroup.gid });
      }
    },
    daemonReload() { operations.push(['daemon-reload']); }
  };
  const privilegedObserveFilesystemPath = (destination) => {
    const observed = observeFilesystemPath(destination);
    const owner = virtualOwnership.get(destination);
    return owner === undefined || !observed.exists ? observed : { ...observed, ...owner };
  };

  const stage1 = () => {
    const plan = createIdentityPlan({ identityState: named(), contract });
    return applyIdentityPlan({ plan, approvedPlanDigest: plan.planDigest, adapter, contract });
  };
  const stage2Plan = (receipt) => previewInstallation({
    clientUser: state.clientUser.name,
    identityReceipt: receipt,
    nodeArchive: archive,
    adapter,
    contract
  });
  return {
    adapter,
    archive,
    archiveTree,
    contract,
    operations,
    privilegedObserveFilesystemPath,
    repack,
    root,
    setFailIdentityKind(value) { failIdentityKind = value; },
    setDenyProtectedObservation(value) { denyProtectedObservation = value; },
    setVirtualOwner(destination, uid, gid) { virtualOwnership.set(destination, { uid, gid }); },
    stage1,
    stage2Plan,
    state
  };
}

test('contract freezes two approvals, named dynamic identities, paths, and Node source', () => {
  const contract = loadInstallationContract();
  assert.deepEqual(contract.transactions, {
    stage1: {
      preview: 'preview-identities', apply: 'apply-identities',
      scope: 'os-identities-only', receipt: 'agents-os-resident.resolved-identity-receipt.v1'
    },
    stage2: {
      preview: 'preview-install', apply: 'apply-stage-only',
      requiresStage1Receipt: true, scope: 'staged-installation-only'
    },
    observation: {
      request: 'preview-observation-request', observe: 'observe-installation',
      requestSchema: 'agents-os-resident.installation-observation-request.v1',
      receiptSchema: 'agents-os-resident.installation-observation-receipt.v1',
      observerVersion: 'HARDENED_INSTALLATION_OBSERVER_V1',
      scope: 'resident-installation-namespaces-read-only'
    }
  });
  assert.equal(contract.identities.daemonUser, 'agents-os-resident');
  assert.equal(contract.identities.daemonGroup, 'agents-os-resident');
  assert.equal(contract.identities.clientGroup, 'agents-os-resident-clients');
  assert.equal(contract.identities.allocation, 'dynamic-system');
  assert.equal(contract.paths.packageRoot, '/opt/agents-os-resident');
  assert.equal(contract.paths.configRoot, '/etc/agents-os-resident');
  assert.equal(contract.paths.stateRoot, '/var/lib/agents-os-resident');
  assert.equal(contract.nodeRuntime.version, '22.23.1');
  assert.equal(contract.nodeRuntime.distributionArchitecture, 'linux-x64');
  assert.equal(contract.nodeRuntime.officialChecksumSource,
    'https://nodejs.org/dist/v22.23.1/SHASUMS256.txt');
  assert.equal(contract.nodeRuntime.networkDuringApply, false);
  assert.deepEqual(contract.safety.activationOperations, []);
});

test('Stage 1 binds exact argv, dynamically allocates all absent identities, and emits receipt', (t) => {
  const value = fixture(t);
  const plan = createIdentityPlan({
    identityState: value.adapter.inspectNamedIdentities(), contract: value.contract
  });
  assert.deepEqual(plan.preconditions, {
    daemonUser: { exists: false }, daemonGroup: { exists: false }, clientGroup: { exists: false }
  });
  assert.deepEqual(plan.operations.map(({ executable, argv }) => [executable, argv]), [
    ['/usr/sbin/groupadd', ['--system', 'agents-os-resident']],
    ['/usr/sbin/groupadd', ['--system', 'agents-os-resident-clients']],
    ['/usr/sbin/useradd', [
      '--system', '--gid', 'agents-os-resident', '--home-dir', '/nonexistent',
      '--no-create-home', '--shell', '/usr/sbin/nologin', 'agents-os-resident'
    ]]
  ]);
  assert.doesNotMatch(JSON.stringify(plan), /UNRESOLVED|AUTO_UID|DAEMON_UID/u);
  const result = applyIdentityPlan({
    plan, approvedPlanDigest: plan.planDigest, adapter: value.adapter, contract: value.contract
  });
  assert.equal(result.result, 'RESOLVED_IDENTITY_RECEIPT');
  assert.equal(result.receipt.daemonUser.uid, process.getuid());
  assert.equal(result.receipt.daemonGroup.gid, 3101);
  assert.equal(result.receipt.clientGroup.gid, 3102);
  assert.match(result.receipt.receiptDigest, /^sha256:[0-9a-f]{64}$/u);
  assert.ok(value.operations.every((operation) => operation[0] === 'identity'));
});

test('Stage 1 reuses exact identities, rejects conflicts, and rejects preview drift before mutation', (t) => {
  const value = fixture(t);
  const first = value.stage1();
  value.operations.length = 0;
  const noopPlan = createIdentityPlan({
    identityState: value.adapter.inspectNamedIdentities(), contract: value.contract
  });
  assert.deepEqual(noopPlan.operations, []);
  const noop = applyIdentityPlan({
    plan: noopPlan, approvedPlanDigest: noopPlan.planDigest,
    adapter: value.adapter, contract: value.contract
  });
  assert.equal(noop.receipt.daemonUser.uid, first.receipt.daemonUser.uid);
  assert.deepEqual(value.operations, []);

  const conflict = clone(value.adapter.inspectNamedIdentities());
  conflict.daemonUser.shell = '/bin/bash';
  assert.throws(() => createIdentityPlan({ identityState: conflict, contract: value.contract }),
    /IDENTITY_PRECONDITION_CONFLICT/u);

  const fresh = fixture(t);
  const stalePlan = createIdentityPlan({
    identityState: fresh.adapter.inspectNamedIdentities(), contract: fresh.contract
  });
  fresh.state.daemonGroup = {
    name: fresh.contract.identities.daemonGroup, gid: 4101, members: [], systemGroup: true
  };
  assert.throws(() => applyIdentityPlan({
    plan: stalePlan, approvedPlanDigest: stalePlan.planDigest,
    adapter: fresh.adapter, contract: fresh.contract
  }), /IDENTITY_PLAN_PRECONDITION_CHANGED/u);
  assert.deepEqual(fresh.operations, []);
});

test('Stage 1 partial allocation is reported without cleanup and is resumable', (t) => {
  const value = fixture(t);
  value.setFailIdentityKind('create-client-group');
  const plan = createIdentityPlan({
    identityState: value.adapter.inspectNamedIdentities(), contract: value.contract
  });
  const partial = applyIdentityPlan({
    plan, approvedPlanDigest: plan.planDigest, adapter: value.adapter, contract: value.contract
  });
  assert.equal(partial.result, 'PARTIAL_IDENTITY_ALLOCATION');
  assert.deepEqual(partial.completedOperations, ['create-daemon-group']);
  assert.equal(partial.automaticCleanupPerformed, false);
  assert.equal(value.state.daemonGroup.gid, 3101);
  assert.equal(value.state.clientGroup, null);

  value.setFailIdentityKind(null);
  const resumedPlan = createIdentityPlan({
    identityState: value.adapter.inspectNamedIdentities(), contract: value.contract
  });
  assert.deepEqual(resumedPlan.operations.map((operation) => operation.kind), [
    'create-client-group', 'create-daemon-user'
  ]);
  const resumed = applyIdentityPlan({
    plan: resumedPlan, approvedPlanDigest: resumedPlan.planDigest,
    adapter: value.adapter, contract: value.contract
  });
  assert.equal(resumed.result, 'RESOLVED_IDENTITY_RECEIPT');
});

test('Stage 2 preview requires receipt and Node, and binds identities, artifact, and filesystem', (t) => {
  const value = fixture(t);
  const receipt = value.stage1().receipt;
  value.operations.length = 0;
  const plan = value.stage2Plan(receipt);
  assert.equal(plan.identityReceipt.receiptDigest, receipt.receiptDigest);
  assert.equal(plan.identitySnapshot.daemonUid, process.getuid());
  assert.equal(plan.identities.users[0].resolvedUid, process.getuid());
  assert.equal(plan.identities.groups[0].resolvedGid, 3101);
  assert.equal(plan.nodeArtifact.archiveSha256, value.contract.nodeRuntime.sha256);
  assert.equal(plan.nodeArtifact.validatedVersion, 'v22.23.1');
  assert.ok(plan.filesystemPreconditions.length > plan.files.length);
  assert.ok(plan.filesystemPreconditions.every((entry) =>
    Object.hasOwn(entry.observed, 'exists') && Object.hasOwn(entry.observed, 'inode')
      && Object.hasOwn(entry.observed, 'nlink')));
  assert.match(plan.planDigest, /^sha256:[0-9a-f]{64}$/u);
  assert.deepEqual(value.operations, []);

  assert.throws(() => previewInstallation({
    clientUser: value.state.clientUser.name,
    identityReceipt: { ...receipt, receiptDigest: `sha256:${'0'.repeat(64)}` },
    nodeArchive: value.archive,
    adapter: value.adapter,
    contract: value.contract
  }), /INSTALL_IDENTITY_RECEIPT_INVALID/u);
  assert.throws(() => previewInstallation({
    clientUser: value.state.clientUser.name,
    identityReceipt: receipt,
    adapter: value.adapter,
    contract: value.contract
  }));
});

test('Stage 2 rejects checksum and executable-version failures before approval', (t) => {
  const checksum = fixture(t);
  const checksumReceipt = checksum.stage1().receipt;
  checksum.operations.length = 0;
  writeFileSync(checksum.archive, Buffer.from('not the approved archive'));
  assert.throws(() => checksum.stage2Plan(checksumReceipt), /INSTALL_NODE_INTEGRITY_FAILED/u);
  assert.deepEqual(checksum.operations, []);

  const version = fixture(t);
  const versionReceipt = version.stage1().receipt;
  version.operations.length = 0;
  writeFileSync(
    path.join(version.archiveTree, 'node-v22.23.1-linux-x64/bin/node'),
    '#!/bin/sh\nprintf "v22.22.0\\n"\n',
    { mode: 0o700 }
  );
  version.repack();
  assert.throws(() => version.stage2Plan(versionReceipt), /INSTALL_NODE_VERSION_INVALID/u);
  assert.deepEqual(version.operations, []);
});

function assertStage2DriftRejected(value, plan, receipt) {
  assert.throws(() => applyStageOnly({
    plan,
    approvedPlanDigest: plan.planDigest,
    clientUser: value.state.clientUser.name,
    nodeArchive: value.archive,
    adapter: value.adapter,
    contract: value.contract
  }), /INSTALL_PLAN_PRECONDITION_CHANGED/u);
  assert.deepEqual(value.operations, []);
  assert.equal(receipt.continuityAuthority, false);
}

test('Stage 2 identity, absence, mode, symlink, unit-content, and Node drift are zero-mutation', async (t) => {
  await t.test('numeric identity drift', (t) => {
    const value = fixture(t);
    const receipt = value.stage1().receipt;
    value.operations.length = 0;
    const plan = value.stage2Plan(receipt);
    value.state.daemonUser.uid += 1;
    assertStage2DriftRejected(value, plan, receipt);
  });
  await t.test('missing path becomes present', (t) => {
    const value = fixture(t);
    const receipt = value.stage1().receipt;
    value.operations.length = 0;
    const plan = value.stage2Plan(receipt);
    mkdirSync(value.contract.paths.packageRoot, { mode: 0o755 });
    value.setVirtualOwner(value.contract.paths.packageRoot, 0, 0);
    assertStage2DriftRejected(value, plan, receipt);
  });
  await t.test('dependency directory mode changes', (t) => {
    const value = fixture(t);
    const receipt = value.stage1().receipt;
    value.operations.length = 0;
    const plan = value.stage2Plan(receipt);
    chmodSync(path.dirname(value.contract.paths.packageRoot), 0o777);
    assertStage2DriftRejected(value, plan, receipt);
  });
  await t.test('dependency directory owner changes', (t) => {
    const value = fixture(t);
    const receipt = value.stage1().receipt;
    value.operations.length = 0;
    const plan = value.stage2Plan(receipt);
    value.setVirtualOwner(path.dirname(value.contract.paths.packageRoot), 8123, 8123);
    assertStage2DriftRejected(value, plan, receipt);
  });
  await t.test('absent target becomes symlink', (t) => {
    const value = fixture(t);
    const receipt = value.stage1().receipt;
    value.operations.length = 0;
    const plan = value.stage2Plan(receipt);
    symlinkSync(path.dirname(value.contract.paths.packageRoot), value.contract.paths.packageRoot);
    assertStage2DriftRejected(value, plan, receipt);
  });
  await t.test('existing unit content changes', (t) => {
    const value = fixture(t);
    const receipt = value.stage1().receipt;
    value.operations.length = 0;
    const firstPlan = value.stage2Plan(receipt);
    applyStageOnly({
      plan: firstPlan, approvedPlanDigest: firstPlan.planDigest,
      clientUser: value.state.clientUser.name, nodeArchive: value.archive,
      adapter: value.adapter, contract: value.contract
    });
    const secondPlan = value.stage2Plan(receipt);
    value.operations.length = 0;
    writeFileSync(value.contract.paths.systemUnit, 'drifted unit\n', { mode: 0o644 });
    assertStage2DriftRejected(value, secondPlan, receipt);
  });
  await t.test('approved Node archive changes', (t) => {
    const value = fixture(t);
    const receipt = value.stage1().receipt;
    value.operations.length = 0;
    const plan = value.stage2Plan(receipt);
    writeFileSync(value.archive, Buffer.concat([readFileSync(value.archive), Buffer.from('drift')]));
    assertStage2DriftRejected(value, plan, receipt);
  });
});

test('two-stage disposable flow installs exact stage-only projection without authority', (t) => {
  const value = fixture(t);
  const stage1 = value.stage1();
  const identityMutationCount = value.operations.length;
  const plan = value.stage2Plan(stage1.receipt);
  const beforeApplyCount = value.operations.length;
  const result = applyStageOnly({
    plan,
    approvedPlanDigest: plan.planDigest,
    clientUser: value.state.clientUser.name,
    nodeArchive: value.archive,
    adapter: value.adapter,
    contract: value.contract
  });
  assert.equal(identityMutationCount, 3);
  assert.equal(beforeApplyCount, identityMutationCount);
  assert.equal(result.serviceStarted, false);
  assert.equal(result.serviceEnabled, false);
  assert.equal(result.continuityInitialized, false);
  assert.equal(result.daemonReloadPerformed, false);
  assert.ok(!value.operations.some((operation) => operation[0] === 'daemon-reload'));

  const installedManifest = JSON.parse(readFileSync(
    path.join(value.contract.paths.packageRoot, 'companion-integrity.json'), 'utf8'
  ));
  const stagedRequire = createRequire(path.join(value.contract.paths.packageRoot, 'package.json'));
  assert.equal(stagedRequire('./companion/integrity').verifyCompanionIntegrity({
    packageRoot: value.contract.paths.packageRoot
  }).buildId, installedManifest.buildId);
  const identity = JSON.parse(readFileSync(value.contract.paths.daemonIdentity, 'utf8'));
  assert.equal(identity.daemonUid, process.getuid());
  assert.equal(identity.clientUid, process.getuid() + 10000);
  assert.equal(identity.socketGid, 3102);
  const unit = readFileSync(value.contract.paths.systemUnit, 'utf8');
  assert.ok(unit.includes(`\nUser=${process.getuid()}\n`));
  assert.ok(unit.includes('\nGroup=3102\n'));
  assert.match(unit, /^RestrictSUIDSGID=no$/mu);
  for (const protectedRoot of [
    value.contract.paths.residentRoot,
    value.contract.paths.witnessRoot,
    value.contract.paths.memoryBodyRoot
  ]) {
    assert.equal(lstatSync(protectedRoot).mode & 0o7777, 0o700);
    assert.deepEqual(readdirSync(protectedRoot), []);
  }
  for (const forbidden of [
    'writer.lock', 'authority.lock', 'generation', 'event',
    'ACTIVE_LOCAL_OWNER', 'MATCH', 'witness-enrollment'
  ]) {
    assert.equal(existsSync(path.join(value.contract.paths.stateRoot, forbidden)), false);
  }
});

test('repeat preview fails closed for client EACCES and succeeds with bounded observation receipt', (t) => {
  const value = fixture(t);
  const receipt = value.stage1().receipt;
  const firstPlan = value.stage2Plan(receipt);
  applyStageOnly({
    plan: firstPlan, approvedPlanDigest: firstPlan.planDigest,
    clientUser: value.state.clientUser.name, nodeArchive: value.archive,
    adapter: value.adapter, contract: value.contract
  });
  value.operations.length = 0;
  value.setDenyProtectedObservation(true);
  assert.throws(() => value.stage2Plan(receipt), /INSTALL_PRIVILEGED_OBSERVATION_REQUIRED/u);
  assert.deepEqual(value.operations, []);

  const request = previewInstallationObservationRequest({
    clientUser: value.state.clientUser.name, identityReceipt: receipt,
    nodeArchive: value.archive, adapter: value.adapter, contract: value.contract
  });
  const observationReceipt = createInstallationObservationReceipt({
    request, observer: value.privilegedObserveFilesystemPath, contract: value.contract
  });
  const repeatPlan = previewInstallation({
    clientUser: value.state.clientUser.name, identityReceipt: receipt,
    nodeArchive: value.archive, adapter: value.adapter,
    observationReceipt, contract: value.contract
  });
  assert.equal(repeatPlan.planDigest.startsWith('sha256:'), true);
  assert.equal(observationReceipt.continuityAuthority, false);
  assert.deepEqual(request.paths.map((entry) => entry.path).sort(), [
    value.contract.paths.stateRoot,
    value.contract.paths.residentRoot,
    value.contract.paths.witnessRoot,
    value.contract.paths.memoryBodyRoot
  ].sort());
});

test('privileged observation request rejects paths outside Resident namespaces', (t) => {
  const value = fixture(t);
  const receipt = value.stage1().receipt;
  const request = clone(previewInstallationObservationRequest({
    clientUser: value.state.clientUser.name, identityReceipt: receipt,
    nodeArchive: value.archive, adapter: value.adapter, contract: value.contract
  }));
  request.paths[0] = { path: '/etc/shadow', expectedKind: 'control-file' };
  const unsigned = clone(request);
  delete unsigned.requestDigest;
  request.requestDigest = canonicalDigest(unsigned);
  assert.throws(() => createInstallationObservationReceipt({
    request, observer: value.privilegedObserveFilesystemPath, contract: value.contract
  }), /INSTALL_OBSERVATION_REQUEST_INVALID/u);
  const privateBodyRequest = clone(previewInstallationObservationRequest({
    clientUser: value.state.clientUser.name, identityReceipt: receipt,
    nodeArchive: value.archive, adapter: value.adapter, contract: value.contract
  }));
  privateBodyRequest.paths.push({
    path: path.join(value.contract.paths.memoryBodyRoot, 'private-body'),
    expectedKind: 'package-file'
  });
  privateBodyRequest.paths.sort((left, right) => left.path.localeCompare(right.path));
  const privateUnsigned = clone(privateBodyRequest);
  delete privateUnsigned.requestDigest;
  privateBodyRequest.requestDigest = canonicalDigest(privateUnsigned);
  assert.throws(() => createInstallationObservationReceipt({
    request: privateBodyRequest,
    observer: value.privilegedObserveFilesystemPath,
    contract: value.contract
  }), /INSTALL_OBSERVATION_REQUEST_INVALID/u);
  assert.deepEqual(value.operations.filter(([kind]) => kind !== 'identity'), []);
});

test('observation receipt is preview input only and root reobservation rejects stale state', (t) => {
  const value = fixture(t);
  const receipt = value.stage1().receipt;
  const request = previewInstallationObservationRequest({
    clientUser: value.state.clientUser.name, identityReceipt: receipt,
    nodeArchive: value.archive, adapter: value.adapter, contract: value.contract
  });
  const observationReceipt = createInstallationObservationReceipt({
    request, observer: value.privilegedObserveFilesystemPath, contract: value.contract
  });
  const plan = previewInstallation({
    clientUser: value.state.clientUser.name, identityReceipt: receipt,
    nodeArchive: value.archive, adapter: value.adapter,
    observationReceipt, contract: value.contract
  });
  mkdirSync(value.contract.paths.stateRoot, { mode: 0o700 });
  value.setVirtualOwner(value.contract.paths.stateRoot, value.state.daemonUser.uid,
    value.state.daemonGroup.gid);
  value.operations.length = 0;
  assertStage2DriftRejected(value, plan, receipt);
});

test('existing hard-linked Node is rejected before Stage 2 approval', (t) => {
  const value = fixture(t);
  const receipt = value.stage1().receipt;
  const plan = value.stage2Plan(receipt);
  applyStageOnly({
    plan, approvedPlanDigest: plan.planDigest,
    clientUser: value.state.clientUser.name, nodeArchive: value.archive,
    adapter: value.adapter, contract: value.contract
  });
  linkSync(value.contract.paths.nodeBinary, path.join(value.root, 'node-hardlink'));
  value.operations.length = 0;
  assert.throws(() => value.stage2Plan(receipt), /INSTALL_FILESYSTEM_PRECONDITION_INVALID/u);
  assert.deepEqual(value.operations, []);
});

test('Node nlink drift after preview rejects before every Stage 2 mutation', (t) => {
  const value = fixture(t);
  const receipt = value.stage1().receipt;
  const first = value.stage2Plan(receipt);
  applyStageOnly({
    plan: first, approvedPlanDigest: first.planDigest,
    clientUser: value.state.clientUser.name, nodeArchive: value.archive,
    adapter: value.adapter, contract: value.contract
  });
  const plan = value.stage2Plan(receipt);
  linkSync(value.contract.paths.nodeBinary, path.join(value.root, 'node-hardlink'));
  value.operations.length = 0;
  assertStage2DriftRejected(value, plan, receipt);
});

test('daemon-reload is a separately bound Stage 2 mutation choice', (t) => {
  const value = fixture(t);
  const receipt = value.stage1().receipt;
  value.operations.length = 0;
  const plan = value.stage2Plan(receipt);
  assert.deepEqual(plan.daemonReload, { requested: false, operation: 'none' });
  assert.throws(() => applyStageOnly({
    plan,
    approvedPlanDigest: plan.planDigest,
    clientUser: value.state.clientUser.name,
    nodeArchive: value.archive,
    adapter: value.adapter,
    contract: value.contract,
    daemonReload: true
  }), /INSTALL_PLAN_PRECONDITION_CHANGED/u);
  assert.deepEqual(value.operations, []);
});

test('installer has no activation path and CLI separates the two approvals', () => {
  const tool = new URL('../tools/stage-hardened-installation.mjs', import.meta.url);
  const source = readFileSync(tool, 'utf8');
  assert.doesNotMatch(source, /systemctl['"], \[['"](?:start|restart|enable|preset)/u);
  assert.doesNotMatch(source, /enable-now|socket-activate|continuity-admit/u);
  assert.match(source, /systemctl['"], \[['"]daemon-reload['"]\]/u);
  assert.match(source, /PACKAGE_ROOT !== contract\.paths\.packageRoot/u);
  assert.match(source, /requireRootOwnedPath\(TOOL_PATH, 'file'\)/u);
  assert.match(source, /verifyCompanionIntegrity\(\{ packageRoot: PACKAGE_ROOT \}\)/u);
  const missingNode = spawnSync(process.execPath, [
    tool.pathname, '--preview-install', '--client-user', 'fixture-client',
    '--identity-receipt', '/does/not/matter'
  ], { encoding: 'utf8' });
  assert.notEqual(missingNode.status, 0);
  assert.match(missingNode.stderr, /INSTALL_ARGUMENTS_INVALID/u);
});
