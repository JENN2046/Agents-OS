import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  chmodSync,
  chownSync,
  existsSync,
  closeSync,
  fstatSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  openSync,
  readFileSync,
  readdirSync,
  realpathSync,
  renameSync,
  rmSync,
  unlinkSync,
  writeFileSync
} from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  renderDaemonIdentityPolicy,
  renderSystemdUnit
} from './render-systemd-unit.mjs';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const CONTRACT_PATH = resolve(
  PACKAGE_ROOT,
  'deployment/hardened-installation-contract.v1.json'
);
const require = createRequire(import.meta.url);
const { verifyCompanionIntegrity } = require('../companion/integrity');

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function canonicalJson(value) {
  const walk = (input) => {
    if (Array.isArray(input)) return input.map(walk);
    if (input !== null && typeof input === 'object') {
      return Object.fromEntries(
        Object.keys(input).sort().map((key) => [key, walk(input[key])])
      );
    }
    return input;
  };
  return JSON.stringify(walk(value));
}

function planDigest(plan) {
  return `sha256:${sha256(Buffer.from(canonicalJson(plan), 'utf8'))}`;
}

function exactKeys(value, keys) {
  return value !== null
    && typeof value === 'object'
    && !Array.isArray(value)
    && JSON.stringify(Object.keys(value).sort())
      === JSON.stringify([...keys].sort());
}

function safeAbsolute(value) {
  return typeof value === 'string'
    && value !== '/'
    && isAbsolute(value)
    && resolve(value) === value
    && !/[\0\r\n\t]/u.test(value);
}

function contains(parent, child) {
  const rel = relative(parent, child);
  return rel === '' || (rel !== '..' && !rel.startsWith(`..${sep}`));
}

function parseMode(value) {
  if (!/^[0-7]{4}$/u.test(value)) throw new Error('INSTALL_CONTRACT_INVALID');
  return Number.parseInt(value, 8);
}

export function loadInstallationContract(path = CONTRACT_PATH) {
  const contract = JSON.parse(readFileSync(path, 'utf8'));
  const { identities, nodeRuntime, ownership, package: pkg, paths, safety, systemd } = contract;
  if (contract.schemaVersion !== 'agents-os-resident.hardened-installation.v1'
    || contract.transactions?.stage1?.preview !== 'preview-identities'
    || contract.transactions?.stage1?.apply !== 'apply-identities'
    || contract.transactions?.stage1?.scope !== 'os-identities-only'
    || contract.transactions?.stage1?.receipt
      !== 'agents-os-resident.resolved-identity-receipt.v1'
    || contract.transactions?.stage2?.preview !== 'preview-install'
    || contract.transactions?.stage2?.apply !== 'apply-stage-only'
    || contract.transactions?.stage2?.requiresStage1Receipt !== true
    || contract.platform?.os !== 'linux'
    || contract.platform?.architecture !== 'x86_64'
    || identities?.daemonUser !== 'agents-os-resident'
    || identities?.daemonGroup !== 'agents-os-resident'
    || identities?.clientGroup !== 'agents-os-resident-clients'
    || identities?.allocation !== 'dynamic-system'
    || identities?.systemRangeSource !== '/etc/login.defs'
    || !exactKeys(identities?.systemRangeDefaults, ['uidMin', 'uidMax', 'gidMin', 'gidMax'])
    || identities.systemRangeDefaults.uidMin !== 100
    || identities.systemRangeDefaults.uidMax !== 999
    || identities.systemRangeDefaults.gidMin !== 100
    || identities.systemRangeDefaults.gidMax !== 999
    || identities?.groupAllocator !== '/usr/sbin/groupadd --system'
    || identities?.userAllocator !== '/usr/sbin/useradd --system'
    || identities?.daemonHome !== '/nonexistent'
    || identities?.daemonShell !== '/usr/sbin/nologin'
    || paths?.packageRoot !== '/opt/agents-os-resident'
    || paths?.configRoot !== '/etc/agents-os-resident'
    || paths?.stateRoot !== '/var/lib/agents-os-resident'
    || paths?.residentRoot !== `${paths.stateRoot}/agents-os-resident-local-owner-v1`
    || paths?.witnessRoot !== `${paths.stateRoot}/protected-witness`
    || paths?.memoryBodyRoot !== `${paths.stateRoot}/private-memory-bodies`
    || paths?.daemonIdentity !== `${paths.configRoot}/daemon-identity.json`
    || paths?.systemUnit !== '/etc/systemd/system/agents-os-resident.service'
    || paths?.nodeBinary !== `${paths.packageRoot}/runtime/node-v22.23.1-linux-x64/bin/node`
    || nodeRuntime?.version !== '22.23.1'
    || nodeRuntime?.versionOutput !== 'v22.23.1'
    || nodeRuntime?.distributionArchitecture !== 'linux-x64'
    || nodeRuntime?.archiveName !== 'node-v22.23.1-linux-x64.tar.xz'
    || nodeRuntime?.archiveMember !== 'node-v22.23.1-linux-x64/bin/node'
    || nodeRuntime?.officialUrl
      !== 'https://nodejs.org/dist/v22.23.1/node-v22.23.1-linux-x64.tar.xz'
    || nodeRuntime?.officialChecksumSource
      !== 'https://nodejs.org/dist/v22.23.1/SHASUMS256.txt'
    || !/^[0-9a-f]{64}$/u.test(nodeRuntime?.sha256)
    || JSON.stringify(nodeRuntime?.selectionOrder) !== JSON.stringify([
      'existing-exact-dedicated-runtime',
      'operator-supplied-official-archive'
    ])
    || nodeRuntime?.hostNodeReuse !== false
    || nodeRuntime?.networkDuringApply !== false
    || pkg?.inventoryManifest !== 'companion-integrity.json'
    || pkg?.inventoryMode !== 'manifest-exact-files-only'
    || systemd?.scope !== 'system'
    || systemd?.unitName !== 'agents-os-resident.service'
    || systemd?.runtimeGroup !== 'client'
    || systemd?.daemonReload !== 'explicit-only'
    || safety?.defaultOperation !== 'preview-identities'
    || safety?.applyOperation !== 'stage-only'
    || !Array.isArray(safety?.activationOperations)
    || safety.activationOperations.length !== 0
    || safety?.continuityInitialization !== false
    || safety?.witnessEnrollment !== false) {
    throw new Error('INSTALL_CONTRACT_INVALID');
  }
  for (const value of Object.values(paths)) {
    if (!safeAbsolute(value)) throw new Error('INSTALL_CONTRACT_INVALID');
  }
  const protectedRoots = [paths.residentRoot, paths.witnessRoot, paths.memoryBodyRoot];
  for (let left = 0; left < protectedRoots.length; left += 1) {
    for (let right = left + 1; right < protectedRoots.length; right += 1) {
      if (contains(protectedRoots[left], protectedRoots[right])
        || contains(protectedRoots[right], protectedRoots[left])) {
        throw new Error('INSTALL_CONTRACT_INVALID');
      }
    }
  }
  for (const profile of Object.values(ownership)) parseMode(profile.mode);
  return Object.freeze(contract);
}

function parseIntegrityManifest() {
  const verified = verifyCompanionIntegrity({ packageRoot: PACKAGE_ROOT });
  const manifest = JSON.parse(readFileSync(
    resolve(PACKAGE_ROOT, 'companion-integrity.json'),
    'utf8'
  ));
  if (manifest.buildId !== verified.buildId
    || manifest.packageVersion !== verified.packageVersion) {
    throw new Error('INSTALL_PACKAGE_PROJECTION_INVALID');
  }
  return manifest;
}

function validateNamedIdentityState(state, contract) {
  if (!exactKeys(state, ['daemonUser', 'daemonGroup', 'clientGroup'])) {
    throw new Error('IDENTITY_PRECONDITION_CONFLICT');
  }
  const { identities } = contract;
  if (state.daemonGroup !== null
    && (state.daemonGroup.name !== identities.daemonGroup
      || !Number.isSafeInteger(state.daemonGroup.gid)
      || state.daemonGroup.gid <= 0
      || state.daemonGroup.systemGroup !== true)) {
    throw new Error('IDENTITY_PRECONDITION_CONFLICT');
  }
  if (state.clientGroup !== null
    && (state.clientGroup.name !== identities.clientGroup
      || !Number.isSafeInteger(state.clientGroup.gid)
      || state.clientGroup.gid <= 0
      || state.clientGroup.systemGroup !== true)) {
    throw new Error('IDENTITY_PRECONDITION_CONFLICT');
  }
  if (state.daemonGroup !== null && state.clientGroup !== null
    && state.daemonGroup.gid === state.clientGroup.gid) {
    throw new Error('IDENTITY_PRECONDITION_CONFLICT');
  }
  if (state.daemonUser !== null) {
    if (state.daemonGroup === null
      || state.daemonUser.name !== identities.daemonUser
      || !Number.isSafeInteger(state.daemonUser.uid)
      || state.daemonUser.uid <= 0
      || state.daemonUser.gid !== state.daemonGroup.gid
      || state.daemonUser.systemAccount !== true
      || state.daemonUser.home !== identities.daemonHome
      || state.daemonUser.shell !== identities.daemonShell
      || !Array.isArray(state.daemonUser.supplementaryGids)
      || state.daemonUser.supplementaryGids.some((gid) => gid !== state.daemonUser.gid)) {
      throw new Error('IDENTITY_PRECONDITION_CONFLICT');
    }
  }
}

function validateInstallationIdentityState(state, contract, clientUser) {
  if (!exactKeys(state, ['daemonUser', 'daemonGroup', 'clientGroup', 'clientUser'])
    || state.clientUser === null
    || state.clientUser.name !== clientUser
    || !Number.isSafeInteger(state.clientUser.uid)
    || state.clientUser.uid <= 0
    || !Array.isArray(state.clientUser.groupNames)) {
    throw new Error('INSTALL_CLIENT_IDENTITY_INVALID');
  }
  validateNamedIdentityState({
    daemonUser: state.daemonUser,
    daemonGroup: state.daemonGroup,
    clientGroup: state.clientGroup
  }, contract);
  if (state.daemonUser === null || state.daemonGroup === null || state.clientGroup === null
    || state.daemonUser.uid === state.clientUser.uid) {
    throw new Error('INSTALL_IDENTITY_RECEIPT_INVALID');
  }
}

function namedIdentitySnapshot(state) {
  return Object.freeze({
    daemonUser: state.daemonUser === null ? { exists: false } : {
      exists: true,
      name: state.daemonUser.name,
      uid: state.daemonUser.uid,
      primaryGid: state.daemonUser.gid,
      home: state.daemonUser.home,
      shell: state.daemonUser.shell,
      systemAccount: state.daemonUser.systemAccount,
      supplementaryGids: [...state.daemonUser.supplementaryGids]
    },
    daemonGroup: state.daemonGroup === null ? { exists: false } : {
      exists: true,
      name: state.daemonGroup.name,
      gid: state.daemonGroup.gid,
      systemGroup: state.daemonGroup.systemGroup
    },
    clientGroup: state.clientGroup === null ? { exists: false } : {
      exists: true,
      name: state.clientGroup.name,
      gid: state.clientGroup.gid,
      systemGroup: state.clientGroup.systemGroup
    }
  });
}

function identityOperations(state, contract) {
  const { identities } = contract;
  const operations = [];
  if (state.daemonGroup === null) {
    operations.push({
      kind: 'create-daemon-group',
      executable: '/usr/sbin/groupadd',
      argv: ['--system', identities.daemonGroup]
    });
  }
  if (state.clientGroup === null) {
    operations.push({
      kind: 'create-client-group',
      executable: '/usr/sbin/groupadd',
      argv: ['--system', identities.clientGroup]
    });
  }
  if (state.daemonUser === null) {
    operations.push({
      kind: 'create-daemon-user',
      executable: '/usr/sbin/useradd',
      argv: [
        '--system', '--gid', identities.daemonGroup,
        '--home-dir', identities.daemonHome, '--no-create-home',
        '--shell', identities.daemonShell, identities.daemonUser
      ]
    });
  }
  return operations;
}

export function createIdentityPlan({ identityState, contract = loadInstallationContract() }) {
  validateNamedIdentityState(identityState, contract);
  const base = {
    schemaVersion: 'agents-os-resident.identity-allocation-plan.v1',
    operation: 'allocate-identities-only',
    contractIdentity: `sha256:${sha256(Buffer.from(canonicalJson(contract.identities), 'utf8'))}`,
    preconditions: namedIdentitySnapshot(identityState),
    intendedSemantics: {
      daemonUser: contract.identities.daemonUser,
      daemonGroup: contract.identities.daemonGroup,
      clientGroup: contract.identities.clientGroup,
      allocation: 'dynamic-system',
      daemonHome: contract.identities.daemonHome,
      daemonShell: contract.identities.daemonShell
    },
    operations: identityOperations(identityState, contract),
    forbiddenMutations: [
      'client-membership', 'package', 'node-runtime', 'config', 'state',
      'systemd', 'activation', 'continuity'
    ]
  };
  return Object.freeze({ ...base, planDigest: planDigest(base) });
}

function resolvedIdentityReceipt(state, identityPlan) {
  if (state.daemonUser === null || state.daemonGroup === null || state.clientGroup === null) {
    throw new Error('IDENTITY_ALLOCATION_INCOMPLETE');
  }
  const base = {
    schemaVersion: 'agents-os-resident.resolved-identity-receipt.v1',
    daemonUser: {
      name: state.daemonUser.name,
      uid: state.daemonUser.uid,
      primaryGid: state.daemonUser.gid
    },
    daemonGroup: { name: state.daemonGroup.name, gid: state.daemonGroup.gid },
    clientGroup: { name: state.clientGroup.name, gid: state.clientGroup.gid },
    sourceContractIdentity: identityPlan.contractIdentity,
    stage1PlanDigest: identityPlan.planDigest,
    continuityAuthority: false
  };
  return Object.freeze({ ...base, receiptDigest: planDigest(base) });
}

function validateCompletedIdentityOperation(operation, state, contract) {
  if (operation.kind === 'create-daemon-group' && state.daemonGroup === null) {
    throw new Error('IDENTITY_ALLOCATION_INCOMPLETE');
  }
  if (operation.kind === 'create-client-group' && state.clientGroup === null) {
    throw new Error('IDENTITY_ALLOCATION_INCOMPLETE');
  }
  if (operation.kind === 'create-daemon-user' && state.daemonUser === null) {
    throw new Error('IDENTITY_ALLOCATION_INCOMPLETE');
  }
  validateNamedIdentityState(state, contract);
}

export function validateIdentityReceipt(receipt, contract = loadInstallationContract()) {
  if (!exactKeys(receipt, [
    'schemaVersion', 'daemonUser', 'daemonGroup', 'clientGroup',
    'sourceContractIdentity', 'stage1PlanDigest', 'continuityAuthority', 'receiptDigest'
  ])) throw new Error('INSTALL_IDENTITY_RECEIPT_INVALID');
  const { receiptDigest, ...base } = receipt;
  const contractIdentity = `sha256:${sha256(Buffer.from(canonicalJson(contract.identities), 'utf8'))}`;
  if (receipt.schemaVersion !== 'agents-os-resident.resolved-identity-receipt.v1'
    || receiptDigest !== planDigest(base)
    || receipt.sourceContractIdentity !== contractIdentity
    || !/^sha256:[0-9a-f]{64}$/u.test(receipt.stage1PlanDigest)
    || receipt.continuityAuthority !== false
    || receipt.daemonUser?.name !== contract.identities.daemonUser
    || receipt.daemonGroup?.name !== contract.identities.daemonGroup
    || receipt.clientGroup?.name !== contract.identities.clientGroup
    || !Number.isSafeInteger(receipt.daemonUser?.uid) || receipt.daemonUser.uid <= 0
    || !Number.isSafeInteger(receipt.daemonUser?.primaryGid)
    || receipt.daemonUser.primaryGid !== receipt.daemonGroup?.gid
    || !Number.isSafeInteger(receipt.clientGroup?.gid)
    || receipt.daemonGroup.gid === receipt.clientGroup.gid) {
    throw new Error('INSTALL_IDENTITY_RECEIPT_INVALID');
  }
  return receipt;
}

export function applyIdentityPlan({ plan, approvedPlanDigest, adapter, contract = loadInstallationContract() }) {
  const { planDigest: suppliedDigest, ...unsignedPlan } = plan;
  if (suppliedDigest !== approvedPlanDigest
    || suppliedDigest !== planDigest(unsignedPlan)
    || plan.operation !== 'allocate-identities-only') {
    throw new Error('IDENTITY_PLAN_NOT_APPROVED');
  }
  const current = adapter.inspectNamedIdentities(contract);
  validateNamedIdentityState(current, contract);
  if (canonicalJson(namedIdentitySnapshot(current)) !== canonicalJson(plan.preconditions)) {
    throw new Error('IDENTITY_PLAN_PRECONDITION_CHANGED');
  }
  if (createIdentityPlan({ identityState: current, contract }).planDigest !== suppliedDigest) {
    throw new Error('IDENTITY_PLAN_NOT_APPROVED');
  }
  const completedOperations = [];
  for (const operation of plan.operations) {
    try {
      adapter.applyIdentityOperation(operation);
      completedOperations.push(operation.kind);
      validateCompletedIdentityOperation(
        operation,
        adapter.inspectNamedIdentities(contract),
        contract
      );
    } catch {
      return Object.freeze({
        result: 'PARTIAL_IDENTITY_ALLOCATION',
        stage1PlanDigest: plan.planDigest,
        completedOperations: Object.freeze(completedOperations),
        automaticCleanupPerformed: false,
        continuityAuthority: false
      });
    }
  }
  const finalState = adapter.inspectNamedIdentities(contract);
  validateNamedIdentityState(finalState, contract);
  return Object.freeze({
    result: 'RESOLVED_IDENTITY_RECEIPT',
    receipt: resolvedIdentityReceipt(finalState, plan),
    completedOperations: Object.freeze(completedOperations)
  });
}

function descendantDirectories(root, leaf) {
  const output = [];
  let current = leaf;
  while (current !== root) {
    if (!contains(root, current) || current === dirname(current)) {
      throw new Error('INSTALL_PACKAGE_PROJECTION_INVALID');
    }
    output.push(current);
    current = dirname(current);
  }
  return output;
}

function packageFiles(contract, integrity) {
  const executable = contract.package.executableFiles;
  const entries = integrity.files.map((file) => ({
    source: file.path,
    destination: resolve(contract.paths.packageRoot, file.path),
    owner: 'root',
    group: 'root',
    mode: executable[file.path] ?? contract.package.regularFileMode,
    byteLength: file.byteLength,
    sha256: file.sha256,
    manifestBound: true
  }));
  const manifestBytes = readFileSync(resolve(PACKAGE_ROOT, 'companion-integrity.json'));
  entries.push({
    source: 'companion-integrity.json',
    destination: resolve(contract.paths.packageRoot, 'companion-integrity.json'),
    owner: 'root',
    group: 'root',
    mode: contract.package.regularFileMode,
    byteLength: manifestBytes.length,
    sha256: sha256(manifestBytes),
    manifestBound: 'build-id-envelope'
  });
  return entries;
}

export function createInstallationPlan({
  clientUser,
  identityState,
  identityReceipt,
  nodeArtifact,
  filesystemPreconditions,
  daemonReload = false,
  contract = loadInstallationContract()
}) {
  if (!/^[a-z_][a-z0-9_-]*[$]?$/u.test(clientUser)) {
    throw new Error('INSTALL_CLIENT_IDENTITY_INVALID');
  }
  validateInstallationIdentityState(identityState, contract, clientUser);
  validateIdentityReceipt(identityReceipt, contract);
  if (identityState.daemonUser.uid !== identityReceipt.daemonUser.uid
    || identityState.daemonGroup.gid !== identityReceipt.daemonGroup.gid
    || identityState.clientGroup.gid !== identityReceipt.clientGroup.gid
    || !Array.isArray(filesystemPreconditions)
    || nodeArtifact?.archiveSha256 !== contract.nodeRuntime.sha256
    || nodeArtifact?.validatedVersion !== contract.nodeRuntime.versionOutput) {
    throw new Error('INSTALL_PLAN_PRECONDITION_CHANGED');
  }
  const integrity = parseIntegrityManifest();
  const { identities, paths } = contract;
  const daemonUid = identityState.daemonUser.uid;
  const daemonGid = identityState.daemonGroup.gid;
  const clientGid = identityState.clientGroup.gid;
  const files = packageFiles(contract, integrity);
  const packageDirectories = [...new Set(files.flatMap((file) =>
    descendantDirectories(paths.packageRoot, dirname(file.destination))))]
    .filter((path) => path !== paths.packageRoot)
    .sort((left, right) => left.length - right.length || left.localeCompare(right));
  if (!packageDirectories.includes(dirname(paths.nodeBinary))) {
    packageDirectories.push(...descendantDirectories(
      paths.packageRoot,
      dirname(paths.nodeBinary)
    ).filter((path) => !packageDirectories.includes(path)));
    packageDirectories.sort((left, right) => left.length - right.length || left.localeCompare(right));
  }
  const basePlan = {
    schemaVersion: 'agents-os-resident.hardened-installation-plan.v1',
    operation: 'stage-only',
    identities: {
      users: [{
        name: identities.daemonUser,
        operation: 'require-receipt-exact',
        uidPolicy: 'resolved-by-stage1',
        resolvedUid: daemonUid,
        primaryGroup: identities.daemonGroup,
        home: identities.daemonHome,
        shell: identities.daemonShell
      }],
      groups: [
        {
          name: identities.daemonGroup,
          operation: 'require-receipt-exact',
          gidPolicy: 'resolved-by-stage1',
          resolvedGid: daemonGid
        },
        {
          name: identities.clientGroup,
          operation: 'require-receipt-exact',
          gidPolicy: 'resolved-by-stage1',
          resolvedGid: clientGid
        }
      ],
      memberships: [{
        user: clientUser,
        group: identities.clientGroup,
        operation: identityState.clientUser.groupNames.includes(identities.clientGroup)
          ? 'reuse-compatible' : 'append-exact-group'
      }]
    },
    runtime: {
      acquisitionSource: contract.nodeRuntime.officialUrl,
      archiveName: contract.nodeRuntime.archiveName,
      archiveSha256: contract.nodeRuntime.sha256,
      version: contract.nodeRuntime.version,
      architecture: contract.nodeRuntime.distributionArchitecture,
      installPath: paths.nodeBinary,
      networkDuringApply: false
    },
    identityReceipt,
    identitySnapshot: {
      daemonUid,
      daemonGid,
      clientGid,
      clientUid: identityState.clientUser.uid,
      observed: {
        named: namedIdentitySnapshot({
          daemonUser: identityState.daemonUser,
          daemonGroup: identityState.daemonGroup,
          clientGroup: identityState.clientGroup
        }),
        clientUser: {
          name: identityState.clientUser.name,
          uid: identityState.clientUser.uid,
          groupNames: [...identityState.clientUser.groupNames].sort()
        }
      }
    },
    nodeArtifact,
    filesystemPreconditions,
    directories: [
      { path: paths.packageRoot, owner: 'root', group: 'root', mode: '0755' },
      ...packageDirectories.map((path) => ({ path, owner: 'root', group: 'root', mode: '0755' })),
      { path: paths.configRoot, owner: 'root', group: 'root', mode: '0755' },
      { path: paths.stateRoot, owner: 'daemon', group: 'daemon', mode: '0700' },
      { path: paths.residentRoot, owner: 'daemon', group: 'daemon', mode: '0700', provisioner: 'prepare-roots' },
      { path: paths.witnessRoot, owner: 'daemon', group: 'daemon', mode: '0700', provisioner: 'prepare-roots' },
      { path: paths.memoryBodyRoot, owner: 'daemon', group: 'daemon', mode: '0700', provisioner: 'prepare-roots' }
    ],
    files: [
      ...files,
      {
        source: contract.nodeRuntime.officialUrl,
        destination: paths.nodeBinary,
        owner: 'root', group: 'root', mode: '0755',
        sha256: contract.nodeRuntime.sha256,
        binding: 'official-archive-member-after-archive-sha256-verification'
      },
      {
        source: 'generated:daemon-identity-policy', destination: paths.daemonIdentity,
        owner: 'root', group: 'root', mode: '0644'
      },
      {
        source: 'generated:systemd-renderer', destination: paths.systemUnit,
        owner: 'root', group: 'root', mode: '0644'
      }
    ],
    units: [{
      name: contract.systemd.unitName,
      source: 'generated:systemd-renderer',
      destination: paths.systemUnit,
      scope: 'system',
      start: false,
      enable: false,
      restart: false,
      preset: false
    }],
    daemonReload: {
      requested: daemonReload,
      operation: daemonReload ? 'systemctl-daemon-reload' : 'none'
    },
    continuity: {
      initialize: false,
      witnessEnrollment: false,
      canonicalWriter: false,
      generationEvent: false
    },
    package: {
      buildId: integrity.buildId,
      packageVersion: integrity.packageVersion,
      inventoryManifest: contract.package.inventoryManifest,
      validatedProjectionOnly: true
    }
  };
  return Object.freeze({ ...basePlan, planDigest: planDigest(basePlan) });
}

export function verifyNodeArchive(archivePath, contract = loadInstallationContract()) {
  const canonicalPath = resolve(archivePath);
  if (!safeAbsolute(canonicalPath)) throw new Error('INSTALL_NODE_ARCHIVE_INVALID');
  const stat = lstatSync(canonicalPath);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.nlink !== 1
    || realpathSync.native(canonicalPath) !== canonicalPath) {
    throw new Error('INSTALL_NODE_ARCHIVE_INVALID');
  }
  const bytes = readFileSync(canonicalPath);
  if (sha256(bytes) !== contract.nodeRuntime.sha256) {
    throw new Error('INSTALL_NODE_INTEGRITY_FAILED');
  }
  const extracted = spawnSync('/usr/bin/tar', [
    '-xJOf', '-', contract.nodeRuntime.archiveMember
  ], { encoding: null, input: bytes, maxBuffer: 256 * 1024 * 1024 });
  if (extracted.status !== 0 || !Buffer.isBuffer(extracted.stdout)
    || extracted.stdout.length === 0) {
    throw new Error('INSTALL_NODE_ARCHIVE_INVALID');
  }
  return extracted.stdout;
}

export function verifyNodeBytes(bytes, expectedVersion) {
  const root = mkdtempSync(join(tmpdir(), 'agents-os-resident-node-check-'));
  const binary = resolve(root, 'node');
  try {
    writeFileSync(binary, bytes, { flag: 'wx', mode: 0o700 });
    chmodSync(binary, 0o700);
    const result = spawnSync(binary, ['--version'], { encoding: 'utf8' });
    if (result.status !== 0 || result.stdout.trim() !== expectedVersion) {
      throw new Error('INSTALL_NODE_VERSION_INVALID');
    }
    return result.stdout.trim();
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

export function validateNodeArtifact(archivePath, contract = loadInstallationContract()) {
  const canonicalPath = realpathSync.native(resolve(archivePath));
  const archive = readFileSync(canonicalPath);
  const executable = verifyNodeArchive(canonicalPath, contract);
  const validatedVersion = verifyNodeBytes(executable, contract.nodeRuntime.versionOutput);
  return Object.freeze({
    identity: Object.freeze({
      requiredVersion: contract.nodeRuntime.version,
      architecture: contract.nodeRuntime.distributionArchitecture,
      officialSource: contract.nodeRuntime.officialUrl,
      archivePath: canonicalPath,
      archiveSha256: sha256(archive),
      expectedOfficialSha256: contract.nodeRuntime.sha256,
      archiveSize: archive.length,
      validatedVersion,
      stagedExecutableSha256: sha256(executable),
      stagedExecutableSize: executable.length
    }),
    executable
  });
}

function observedType(stat) {
  if (stat.isSymbolicLink()) return 'symlink';
  if (stat.isDirectory()) return 'directory';
  if (stat.isFile()) return 'regular-file';
  if (stat.isSocket()) return 'socket';
  if (stat.isFIFO()) return 'fifo';
  return 'other';
}

export function observeFilesystemPath(path) {
  const before = lstatSync(path, { throwIfNoEntry: false });
  if (before === undefined) {
    return Object.freeze({
      exists: false, type: null, symlink: false, canonicalPath: null,
      uid: null, gid: null, mode: null, size: null, sha256: null,
      device: null, inode: null
    });
  }
  const type = observedType(before);
  let fileSha = null;
  let size = null;
  if (type === 'regular-file') {
    const descriptor = openSync(path, 0);
    try {
      const opened = fstatSync(descriptor);
      if (opened.dev !== before.dev || opened.ino !== before.ino
        || !opened.isFile() || opened.isSymbolicLink()) {
        throw new Error('INSTALL_FILESYSTEM_OBSERVATION_UNSTABLE');
      }
      const bytes = readFileSync(descriptor);
      const after = lstatSync(path);
      if (after.dev !== opened.dev || after.ino !== opened.ino
        || after.size !== opened.size) {
        throw new Error('INSTALL_FILESYSTEM_OBSERVATION_UNSTABLE');
      }
      fileSha = sha256(bytes);
      size = bytes.length;
    } finally {
      closeSync(descriptor);
    }
  }
  return Object.freeze({
    exists: true,
    type,
    symlink: before.isSymbolicLink(),
    canonicalPath: before.isSymbolicLink() ? null : realpathSync.native(path),
    uid: before.uid,
    gid: before.gid,
    mode: (before.mode & 0o7777).toString(8).padStart(4, '0'),
    size,
    sha256: fileSha,
    device: String(before.dev),
    inode: String(before.ino)
  });
}

function filesystemSpecs(plan, contract) {
  const specs = new Map();
  const add = (spec) => specs.set(spec.path, spec);
  for (const directory of plan.directories) {
    add({
      path: directory.path,
      kind: 'directory',
      uid: directory.owner === 'root' ? 0 : plan.identitySnapshot.daemonUid,
      gid: directory.group === 'root' ? 0 : plan.identitySnapshot.daemonGid,
      mode: directory.mode
    });
  }
  for (const file of plan.files) {
    add({
      path: file.destination,
      kind: file.source === contract.nodeRuntime.officialUrl
        ? 'node' : file.source.startsWith('generated:') ? 'control-file' : 'package-file',
      uid: 0,
      gid: 0,
      mode: file.mode,
      desiredSha256: file.sha256 ?? null
    });
  }
  for (const path of [
    dirname(contract.paths.packageRoot),
    dirname(contract.paths.configRoot),
    dirname(contract.paths.stateRoot),
    dirname(contract.paths.systemUnit)
  ]) {
    if (!specs.has(path)) add({ path, kind: 'dependency-directory' });
  }
  return [...specs.values()].sort((left, right) => left.path.localeCompare(right.path));
}

function expectedOperation(spec, observed) {
  if (spec.kind === 'dependency-directory') return 'require-compatible';
  if (!observed.exists) return spec.kind === 'directory' ? 'create' : 'install';
  if (spec.kind === 'directory') return 'reuse-compatible';
  if (spec.kind === 'package-file') return 'replace-validated-projection';
  return 'reuse-exact';
}

export function observeFilesystemPreconditions(
  plan,
  contract = loadInstallationContract(),
  observer = observeFilesystemPath
) {
  return Object.freeze(filesystemSpecs(plan, contract).map((spec) => {
    const observed = observer(spec.path);
    return Object.freeze({
      path: spec.path,
      expectedOperation: expectedOperation(spec, observed),
      expectedKind: spec.kind,
      observed
    });
  }));
}

function validateFilesystemPreconditions(plan, contract) {
  const specs = new Map(filesystemSpecs(plan, contract).map((spec) => [spec.path, spec]));
  if (plan.filesystemPreconditions.length !== specs.size) {
    throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
  }
  for (const entry of plan.filesystemPreconditions) {
    const spec = specs.get(entry.path);
    const observed = entry.observed;
    if (spec === undefined || entry.expectedKind !== spec.kind
      || entry.expectedOperation !== expectedOperation(spec, observed)) {
      throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
    }
    if (!observed.exists) {
      if (spec.kind === 'dependency-directory') {
        throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
      }
      continue;
    }
    if (observed.symlink || observed.canonicalPath !== entry.path) {
      throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
    }
    if (spec.kind === 'dependency-directory') {
      if (observed.type !== 'directory' || observed.uid !== 0
        || (Number.parseInt(observed.mode, 8) & 0o022) !== 0) {
        throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
      }
      continue;
    }
    if (spec.kind === 'directory') {
      if (observed.type !== 'directory' || observed.uid !== spec.uid
        || observed.gid !== spec.gid || observed.mode !== spec.mode) {
        throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
      }
      continue;
    }
    if (observed.type !== 'regular-file' || observed.uid !== spec.uid
      || observed.gid !== spec.gid || observed.mode !== spec.mode) {
      throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
    }
    if (spec.kind === 'node'
      && observed.sha256 !== plan.nodeArtifact.stagedExecutableSha256) {
      throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
    }
  }
  const packageObservation = plan.filesystemPreconditions.find(
    (entry) => entry.path === contract.paths.packageRoot
  );
  if (packageObservation?.observed.exists) assertExactPackageSurface(plan, contract);

  const existingControls = plan.filesystemPreconditions.filter(
    (entry) => entry.expectedKind === 'control-file' && entry.observed.exists
  );
  if (existingControls.length > 0) {
    const protectedReady = [
      contract.paths.residentRoot,
      contract.paths.witnessRoot,
      contract.paths.memoryBodyRoot
    ].every((path) => plan.filesystemPreconditions.find((entry) => entry.path === path)?.observed.exists);
    if (!protectedReady) throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
    const config = {
      activationRoot: contract.paths.residentRoot,
      buildId: plan.package.buildId,
      clientUid: plan.identitySnapshot.clientUid,
      daemonUid: plan.identitySnapshot.daemonUid,
      memoryBodyRoot: contract.paths.memoryBodyRoot,
      nodeBinary: contract.paths.nodeBinary,
      pluginRoot: contract.paths.packageRoot,
      socketGid: plan.identitySnapshot.clientGid,
      witnessRoot: contract.paths.witnessRoot
    };
    const desired = new Map([
      [contract.paths.daemonIdentity, Buffer.from(`${JSON.stringify(renderDaemonIdentityPolicy(config), null, 2)}\n`)],
      [contract.paths.systemUnit, Buffer.from(renderSystemdUnit(config))]
    ]);
    for (const entry of existingControls) {
      if (entry.observed.sha256 !== sha256(desired.get(entry.path))) {
        throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
      }
    }
  }
}

function identityStateMatchesReceipt(state, receipt) {
  return state.daemonUser.uid === receipt.daemonUser.uid
    && state.daemonUser.gid === receipt.daemonUser.primaryGid
    && state.daemonGroup.gid === receipt.daemonGroup.gid
    && state.clientGroup.gid === receipt.clientGroup.gid;
}

function previewInstallationBundle({
  clientUser,
  identityReceipt,
  nodeArchive,
  adapter,
  daemonReload = false,
  contract = loadInstallationContract()
}) {
  validateIdentityReceipt(identityReceipt, contract);
  const identityState = adapter.inspectInstallationIdentities(clientUser, contract);
  validateInstallationIdentityState(identityState, contract, clientUser);
  if (!identityStateMatchesReceipt(identityState, identityReceipt)) {
    throw new Error('INSTALL_PLAN_PRECONDITION_CHANGED');
  }
  const node = validateNodeArtifact(nodeArchive, contract);
  const draft = createInstallationPlan({
    clientUser,
    identityState,
    identityReceipt,
    nodeArtifact: node.identity,
    filesystemPreconditions: [],
    daemonReload,
    contract
  });
  const filesystemPreconditions = observeFilesystemPreconditions(
    draft,
    contract,
    adapter.observeFilesystemPath ?? observeFilesystemPath
  );
  const plan = createInstallationPlan({
    clientUser,
    identityState,
    identityReceipt,
    nodeArtifact: node.identity,
    filesystemPreconditions,
    daemonReload,
    contract
  });
  validateFilesystemPreconditions(plan, contract);
  return Object.freeze({ plan, nodeBytes: node.executable });
}

export function previewInstallation(options) {
  return previewInstallationBundle(options).plan;
}

function validatedSourceBytes(file) {
  const bytes = readFileSync(resolve(PACKAGE_ROOT, file.source));
  if (bytes.length !== file.byteLength || sha256(bytes) !== file.sha256) {
    throw new Error('INSTALL_PACKAGE_PROJECTION_INVALID');
  }
  return bytes;
}

function assertExactPackageSurface(plan, contract) {
  const expectedDirectories = new Set(plan.directories
    .map((entry) => entry.path)
    .filter((path) => contains(contract.paths.packageRoot, path)));
  expectedDirectories.add(contract.paths.packageRoot);
  const expectedFiles = new Set(plan.files
    .map((entry) => entry.destination)
    .filter((path) => contains(contract.paths.packageRoot, path)));
  const visit = (directory) => {
    for (const name of readdirSync(directory)) {
      const candidate = resolve(directory, name);
      const stat = lstatSync(candidate);
      if (stat.isSymbolicLink()) throw new Error('INSTALL_PACKAGE_SURFACE_CONFLICT');
      if (stat.isDirectory()) {
        if (!expectedDirectories.has(candidate)) {
          throw new Error('INSTALL_PACKAGE_SURFACE_CONFLICT');
        }
        visit(candidate);
      } else if (!stat.isFile() || !expectedFiles.has(candidate)) {
        throw new Error('INSTALL_PACKAGE_SURFACE_CONFLICT');
      }
    }
  };
  visit(contract.paths.packageRoot);
}

function validateResolvedIdentityState(state, contract, clientUser) {
  validateInstallationIdentityState(state, contract, clientUser);
  if (state.daemonUser === null || state.daemonGroup === null || state.clientGroup === null
    || state.daemonUser.uid === state.clientUser.uid
    || state.daemonGroup.gid === state.clientGroup.gid
    || !state.clientUser.groupNames.includes(contract.identities.clientGroup)) {
    throw new Error('H_EXISTING_DAEMON_IDENTITY_CONFLICT');
  }
  return Object.freeze({
    daemonUid: state.daemonUser.uid,
    daemonGid: state.daemonGroup.gid,
    clientUid: state.clientUser.uid,
    clientGid: state.clientGroup.gid
  });
}

function assertFilesystemPreconditionStillMatches(plan, destination, adapter) {
  const approved = plan.filesystemPreconditions.find((entry) => entry.path === destination);
  if (approved === undefined) throw new Error('INSTALL_FILESYSTEM_PRECONDITION_INVALID');
  const observer = adapter.observeFilesystemPath ?? observeFilesystemPath;
  if (canonicalJson(observer(destination)) !== canonicalJson(approved.observed)) {
    throw new Error('INSTALL_PLAN_PRECONDITION_CHANGED');
  }
}

export function applyStageOnly({
  plan,
  approvedPlanDigest,
  clientUser,
  nodeArchive,
  adapter,
  contract = loadInstallationContract(),
  daemonReload = false
}) {
  const { planDigest: suppliedDigest, ...unsignedPlan } = plan;
  if (suppliedDigest !== planDigest(unsignedPlan)
    || suppliedDigest !== approvedPlanDigest
    || plan.operation !== 'stage-only'
    || plan.units.some((unit) => unit.start || unit.enable || unit.restart || unit.preset)) {
    throw new Error('INSTALL_PLAN_NOT_APPROVED');
  }
  let current;
  try {
    current = previewInstallationBundle({
      clientUser,
      identityReceipt: plan.identityReceipt,
      nodeArchive,
      adapter,
      daemonReload,
      contract
    });
  } catch {
    throw new Error('INSTALL_PLAN_PRECONDITION_CHANGED');
  }
  if (current.plan.planDigest !== approvedPlanDigest) {
    throw new Error('INSTALL_PLAN_PRECONDITION_CHANGED');
  }
  const nodeBytes = current.nodeBytes;
  adapter.ensureMembership(plan.identities.memberships[0]);
  const state = adapter.inspectInstallationIdentities(clientUser, contract);
  const ids = validateResolvedIdentityState(state, contract, clientUser);

  for (const directory of plan.directories.filter((entry) => entry.provisioner === undefined)) {
    assertFilesystemPreconditionStillMatches(plan, directory.path, adapter);
    const uid = directory.owner === 'root' ? 0 : ids.daemonUid;
    const gid = directory.group === 'root' ? 0 : ids.daemonGid;
    adapter.ensureDirectory(directory.path, parseMode(directory.mode), uid, gid);
  }
  assertExactPackageSurface(plan, contract);
  for (const file of plan.files.filter((entry) => entry.manifestBound)) {
    assertFilesystemPreconditionStillMatches(plan, file.destination, adapter);
    adapter.installFile(
      file.destination,
      validatedSourceBytes(file),
      parseMode(file.mode),
      0,
      0
    );
  }
  assertFilesystemPreconditionStillMatches(plan, contract.paths.nodeBinary, adapter);
  adapter.installNode(contract.paths.nodeBinary, nodeBytes, 0o755, 0, 0);
  adapter.verifyNodeVersion(contract.paths.nodeBinary, contract.nodeRuntime.versionOutput);
  for (const destination of [
    contract.paths.residentRoot,
    contract.paths.witnessRoot,
    contract.paths.memoryBodyRoot
  ]) {
    assertFilesystemPreconditionStillMatches(plan, destination, adapter);
  }
  adapter.prepareRoots({
    daemonUser: contract.identities.daemonUser,
    nodeBinary: contract.paths.nodeBinary,
    packageRoot: contract.paths.packageRoot,
    buildId: plan.package.buildId,
    residentRoot: contract.paths.residentRoot,
    witnessRoot: contract.paths.witnessRoot,
    memoryBodyRoot: contract.paths.memoryBodyRoot
  });

  const renderConfig = {
    activationRoot: contract.paths.residentRoot,
    buildId: plan.package.buildId,
    clientUid: ids.clientUid,
    daemonUid: ids.daemonUid,
    memoryBodyRoot: contract.paths.memoryBodyRoot,
    nodeBinary: contract.paths.nodeBinary,
    pluginRoot: contract.paths.packageRoot,
    socketGid: ids.clientGid,
    witnessRoot: contract.paths.witnessRoot
  };
  const identity = Buffer.from(
    `${JSON.stringify(renderDaemonIdentityPolicy(renderConfig), null, 2)}\n`,
    'utf8'
  );
  const unit = Buffer.from(renderSystemdUnit(renderConfig), 'utf8');
  assertFilesystemPreconditionStillMatches(plan, contract.paths.daemonIdentity, adapter);
  adapter.installControlFile(contract.paths.daemonIdentity, identity, 0o644, 0, 0);
  assertFilesystemPreconditionStillMatches(plan, contract.paths.systemUnit, adapter);
  adapter.installControlFile(contract.paths.systemUnit, unit, 0o644, 0, 0);
  if (daemonReload) adapter.daemonReload();
  return Object.freeze({
    result: 'AGENTS_OS_RESIDENT_HARDENED_STAGE_ONLY_APPLIED',
    planDigest: approvedPlanDigest,
    buildId: plan.package.buildId,
    identities: ids,
    daemonReloadPerformed: daemonReload,
    serviceStarted: false,
    serviceEnabled: false,
    continuityInitialized: false
  });
}

function command(path, args, { allowMissing = false, encoding = 'utf8' } = {}) {
  const result = spawnSync(path, args, { encoding });
  if (allowMissing && result.status === 2) return null;
  if (result.status !== 0) throw new Error('INSTALL_HOST_COMMAND_FAILED');
  return result.stdout;
}

function parsePasswd(line) {
  if (line === null) return null;
  const fields = line.trimEnd().split(':');
  if (fields.length !== 7) throw new Error('INSTALL_HOST_IDENTITY_INVALID');
  return {
    name: fields[0], uid: Number(fields[2]), gid: Number(fields[3]),
    home: fields[5], shell: fields[6]
  };
}

function parseGroup(line) {
  if (line === null) return null;
  const fields = line.trimEnd().split(':');
  if (fields.length !== 4) throw new Error('INSTALL_HOST_IDENTITY_INVALID');
  return { name: fields[0], gid: Number(fields[2]), members: fields[3] ? fields[3].split(',') : [] };
}

function systemIdentityRanges(contract) {
  const defaults = contract.identities.systemRangeDefaults;
  const values = new Map([
    ['SYS_UID_MIN', defaults.uidMin], ['SYS_UID_MAX', defaults.uidMax],
    ['SYS_GID_MIN', defaults.gidMin], ['SYS_GID_MAX', defaults.gidMax]
  ]);
  for (const line of readFileSync('/etc/login.defs', 'utf8').split('\n')) {
    const match = line.match(/^\s*(SYS_UID_MIN|SYS_UID_MAX|SYS_GID_MIN|SYS_GID_MAX)\s+([0-9]+)\s*(?:#.*)?$/u);
    if (match) values.set(match[1], Number(match[2]));
  }
  for (const key of ['SYS_UID_MIN', 'SYS_UID_MAX', 'SYS_GID_MIN', 'SYS_GID_MAX']) {
    if (!Number.isSafeInteger(values.get(key))) {
      throw new Error('INSTALL_HOST_IDENTITY_INVALID');
    }
  }
  return values;
}

function inspectHostNamedIdentities(contract) {
  const ranges = systemIdentityRanges(contract);
  const user = (name) => parsePasswd(command('/usr/bin/getent', ['passwd', name], { allowMissing: true }));
  const group = (name) => parseGroup(command('/usr/bin/getent', ['group', name], { allowMissing: true }));
  const daemon = user(contract.identities.daemonUser);
  const daemonGroup = group(contract.identities.daemonGroup);
  const clientGroup = group(contract.identities.clientGroup);
  if (daemon !== null) {
    daemon.systemAccount = daemon.uid >= ranges.get('SYS_UID_MIN')
      && daemon.uid <= ranges.get('SYS_UID_MAX');
    daemon.supplementaryGids = command('/usr/bin/id', ['-G', daemon.name])
      .trim().split(/\s+/u).filter(Boolean).map(Number);
  }
  for (const candidate of [daemonGroup, clientGroup]) {
    if (candidate !== null) {
      candidate.systemGroup = candidate.gid >= ranges.get('SYS_GID_MIN')
        && candidate.gid <= ranges.get('SYS_GID_MAX');
    }
  }
  return {
    daemonUser: daemon,
    daemonGroup,
    clientGroup
  };
}

function inspectHostInstallationIdentities(clientUser, contract) {
  const named = inspectHostNamedIdentities(contract);
  const client = parsePasswd(command('/usr/bin/getent', ['passwd', clientUser], {
    allowMissing: true
  }));
  if (client !== null) {
    client.groupNames = command('/usr/bin/id', ['-nG', client.name])
      .trim().split(/\s+/u).filter(Boolean);
  }
  return { ...named, clientUser: client };
}

function validateSafeParent(path) {
  const parent = dirname(path);
  const stat = lstatSync(parent);
  if (!stat.isDirectory() || stat.isSymbolicLink() || realpathSync.native(parent) !== parent
    || stat.uid !== 0 || (stat.mode & 0o022) !== 0) {
    throw new Error('INSTALL_PATH_PARENT_UNSAFE');
  }
}

function atomicInstall(path, bytes, mode, uid, gid) {
  validateSafeParent(path);
  if (existsSync(path)) {
    const existing = lstatSync(path);
    if (!existing.isFile() || existing.isSymbolicLink()
      || existing.uid !== uid || existing.gid !== gid
      || (existing.mode & 0o7777) !== mode) {
      throw new Error('INSTALL_DESTINATION_CONFLICT');
    }
  }
  const temporary = `${path}.stage-${process.pid}`;
  writeFileSync(temporary, bytes, { flag: 'wx', mode });
  try {
    chmodSync(temporary, mode);
    chownSync(temporary, uid, gid);
    renameSync(temporary, path);
  } finally {
    if (existsSync(temporary)) unlinkSync(temporary);
  }
}

export function createHostAdapter({ requireRoot = false } = {}) {
  if (requireRoot && process.geteuid() !== 0) throw new Error('INSTALL_ROOT_REQUIRED');
  return Object.freeze({
    inspectNamedIdentities: inspectHostNamedIdentities,
    inspectInstallationIdentities: inspectHostInstallationIdentities,
    applyIdentityOperation(operation) {
      if (!['create-daemon-group', 'create-client-group', 'create-daemon-user']
        .includes(operation.kind)
        || !['/usr/sbin/groupadd', '/usr/sbin/useradd'].includes(operation.executable)
        || !Array.isArray(operation.argv)) {
        throw new Error('IDENTITY_OPERATION_INVALID');
      }
      command(operation.executable, operation.argv);
    },
    ensureMembership(membership) {
      if (membership.operation === 'append-exact-group') {
        command('/usr/sbin/usermod', [
          '--append', '--groups', membership.group, membership.user
        ]);
      }
    },
    ensureDirectory(path, mode, uid, gid) {
      if (!existsSync(path)) {
        validateSafeParent(path);
        mkdirSync(path, { mode });
        chmodSync(path, mode);
        chownSync(path, uid, gid);
      } else {
        const stat = lstatSync(path);
        if (!stat.isDirectory() || stat.isSymbolicLink()
          || realpathSync.native(path) !== path
          || stat.uid !== uid || stat.gid !== gid
          || (stat.mode & 0o7777) !== mode) {
          throw new Error('INSTALL_DESTINATION_CONFLICT');
        }
      }
    },
    installFile: atomicInstall,
    installNode(path, bytes, mode, uid, gid) {
      if (existsSync(path)) {
        const stat = lstatSync(path);
        if (!stat.isFile() || stat.isSymbolicLink() || stat.nlink !== 1
          || stat.uid !== uid || stat.gid !== gid
          || (stat.mode & 0o7777) !== mode
          || !readFileSync(path).equals(bytes)) {
          throw new Error('INSTALL_NODE_RUNTIME_CONFLICT');
        }
        return;
      }
      atomicInstall(path, bytes, mode, uid, gid);
    },
    installControlFile(path, bytes, mode, uid, gid) {
      if (existsSync(path)) {
        const stat = lstatSync(path);
        if (!stat.isFile() || stat.isSymbolicLink()
          || stat.uid !== uid || stat.gid !== gid
          || (stat.mode & 0o7777) !== mode
          || !readFileSync(path).equals(bytes)) {
          throw new Error('INSTALL_CONTROL_FILE_CONFLICT');
        }
        return;
      }
      atomicInstall(path, bytes, mode, uid, gid);
    },
    verifyNodeVersion(path, expected) {
      const output = command(path, ['--version']).trim();
      if (output !== expected) throw new Error('INSTALL_NODE_VERSION_INVALID');
    },
    prepareRoots(config) {
      command('/usr/sbin/runuser', [
        '--user', config.daemonUser, '--', config.nodeBinary,
        resolve(config.packageRoot, 'companion/resident-daemon.js'),
        '--operation', 'prepare-roots',
        '--root', config.residentRoot,
        '--witness-root', config.witnessRoot,
        '--memory-body-root', config.memoryBodyRoot,
        '--expected-build-id', config.buildId
      ]);
    },
    daemonReload() {
      command('/usr/bin/systemctl', ['daemon-reload']);
    }
  });
}

function parseArgs(argv) {
  const parsed = { daemonReload: false };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if ([
      '--preview-identities', '--apply-identities',
      '--preview-install', '--apply-stage-only'
    ].includes(key)) {
      if (parsed.operation !== undefined) throw new Error('INSTALL_ARGUMENTS_INVALID');
      parsed.operation = key.slice(2);
    } else if (key === '--daemon-reload') {
      parsed.daemonReload = true;
    } else if ([
      '--client-user', '--node-archive', '--identity-receipt',
      '--approved-plan-digest'
    ].includes(key)) {
      if (parsed[key] !== undefined || index + 1 >= argv.length) {
        throw new Error('INSTALL_ARGUMENTS_INVALID');
      }
      parsed[key] = argv[index + 1];
      index += 1;
    } else {
      throw new Error('INSTALL_ARGUMENTS_INVALID');
    }
  }
  const identityOperation = ['preview-identities', 'apply-identities'].includes(parsed.operation);
  const installOperation = ['preview-install', 'apply-stage-only'].includes(parsed.operation);
  if (parsed.operation === undefined
    || (identityOperation && (parsed['--client-user'] !== undefined
      || parsed['--node-archive'] !== undefined || parsed['--identity-receipt'] !== undefined))
    || (installOperation && (parsed['--client-user'] === undefined
      || parsed['--node-archive'] === undefined || parsed['--identity-receipt'] === undefined))
    || (parsed.daemonReload
      && !['preview-install', 'apply-stage-only'].includes(parsed.operation))
    || (parsed.operation.startsWith('apply-')
      && parsed['--approved-plan-digest'] === undefined)
    || (parsed.operation.startsWith('preview-')
      && parsed['--approved-plan-digest'] !== undefined)) {
    throw new Error('INSTALL_ARGUMENTS_INVALID');
  }
  return parsed;
}

function readIdentityReceipt(path, contract) {
  const canonicalPath = resolve(path);
  const stat = lstatSync(canonicalPath);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.nlink !== 1
    || realpathSync.native(canonicalPath) !== canonicalPath || stat.size > 8192) {
    throw new Error('INSTALL_IDENTITY_RECEIPT_INVALID');
  }
  return validateIdentityReceipt(JSON.parse(readFileSync(canonicalPath, 'utf8')), contract);
}

function main(argv) {
  const args = parseArgs(argv);
  const contract = loadInstallationContract();
  const applying = args.operation.startsWith('apply-');
  const adapter = createHostAdapter({ requireRoot: applying });
  if (args.operation === 'preview-identities') {
    const plan = createIdentityPlan({
      identityState: adapter.inspectNamedIdentities(contract), contract
    });
    process.stdout.write(`${JSON.stringify(plan, null, 2)}\n`);
    return;
  }
  if (args.operation === 'apply-identities') {
    const plan = createIdentityPlan({
      identityState: adapter.inspectNamedIdentities(contract), contract
    });
    if (plan.planDigest !== args['--approved-plan-digest']) {
      throw new Error('IDENTITY_PLAN_PRECONDITION_CHANGED');
    }
    const result = applyIdentityPlan({
      plan, approvedPlanDigest: args['--approved-plan-digest'], adapter, contract
    });
    process.stdout.write(`${JSON.stringify(
      result.result === 'RESOLVED_IDENTITY_RECEIPT' ? result.receipt : result,
      null,
      2
    )}\n`);
    return;
  }
  const clientUser = args['--client-user'];
  const identityReceipt = readIdentityReceipt(args['--identity-receipt'], contract);
  const plan = previewInstallation({
    clientUser,
    identityReceipt,
    nodeArchive: resolve(args['--node-archive']),
    adapter,
    daemonReload: args.daemonReload,
    contract
  });
  if (args.operation === 'preview-install') {
    process.stdout.write(`${JSON.stringify(plan, null, 2)}\n`);
    return;
  }
  if (plan.planDigest !== args['--approved-plan-digest']) {
    throw new Error('INSTALL_PLAN_PRECONDITION_CHANGED');
  }
  const result = applyStageOnly({
    plan, approvedPlanDigest: args['--approved-plan-digest'], clientUser,
    nodeArchive: resolve(args['--node-archive']), adapter, contract,
    daemonReload: args.daemonReload
  });
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`${error?.message ?? 'HARDENED_STAGE_INSTALL_FAILED'}\n`);
    process.exit(1);
  }
}
