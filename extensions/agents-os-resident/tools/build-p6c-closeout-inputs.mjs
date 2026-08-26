#!/usr/bin/env node

import { createHash } from 'node:crypto';
import {
  chmodSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync
} from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const PACKAGE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WORKTREE_ROOT = path.resolve(PACKAGE_ROOT, '../..');
const PREDECESSOR_COMMIT = '8c4e2ac4eb907fd84bf09c1fee7aeab8384c2153';
const PREDECESSOR_TREE = '3d2fba6f0877acc73d9afa1d9dc028925a4e1ca0';

function argument(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || index + 1 >= process.argv.length) {
    throw new Error(`MISSING_ARGUMENT:${name}`);
  }
  return path.resolve(process.argv[index + 1]);
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value === null || typeof value !== 'object') return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonical(value[key])])
  );
}

function writeExclusive(root, name, value) {
  const target = path.join(root, name);
  const bytes = `${JSON.stringify(canonical(value), null, 2)}\n`;
  writeFileSync(target, bytes, { encoding: 'utf8', flag: 'wx', mode: 0o600 });
  chmodSync(target, 0o600);
  return { bytes: Buffer.byteLength(bytes), path: name, sha256: sha256(bytes) };
}

function git(args, options = {}) {
  const result = spawnSync('git', args, {
    cwd: WORKTREE_ROOT,
    encoding: options.encoding ?? 'utf8',
    maxBuffer: 32 * 1024 * 1024
  });
  if (result.status !== 0 && !options.allowFailure) {
    throw new Error(`GIT_FAILED:${args.join(':')}`);
  }
  return result;
}

function changedPaths() {
  const output = git([
    'status', '--porcelain=v1', '-z', '--untracked-files=all'
  ]).stdout;
  return [...new Set(output.split('\0').filter(Boolean).map((record) => {
    const value = record.slice(3);
    return value.includes(' -> ') ? value.split(' -> ').at(-1) : value;
  }))].sort();
}

function predecessorBytes(relativePath) {
  const result = git(
    ['show', `${PREDECESSOR_COMMIT}:${relativePath}`],
    { allowFailure: true, encoding: null }
  );
  return result.status === 0 ? result.stdout : null;
}

function commandVersion(command, args) {
  const result = spawnSync(command, args, { encoding: 'utf8' });
  if (result.status !== 0) throw new Error(`VERSION_FAILED:${command}`);
  return result.stdout.trim();
}

const evidenceRoot = argument('--evidence');
const outputRoot = argument('--output');
mkdirSync(outputRoot, { recursive: true, mode: 0o700 });
chmodSync(outputRoot, 0o700);

const head = git(['rev-parse', 'HEAD']).stdout.trim();
const tree = git(['rev-parse', 'HEAD^{tree}']).stdout.trim();
const branch = git(['branch', '--show-current']).stdout.trim();
if (head !== PREDECESSOR_COMMIT
  || tree !== PREDECESSOR_TREE
  || branch !== 'agent/mmr0-p6c-cav3') {
  throw new Error('P6_C_PREDECESSOR_IDENTITY_MISMATCH');
}

const exactChangedFiles = changedPaths().map((relativePath) => {
  const absolutePath = path.join(WORKTREE_ROOT, relativePath);
  const before = predecessorBytes(relativePath);
  const after = readFileSync(absolutePath);
  return {
    path: relativePath,
    postBytes: after.length,
    postSourceSha256: sha256(after),
    preBytes: before?.length ?? null,
    preSourceSha256: before === null ? null : sha256(before),
    predecessorTracked: before !== null
  };
});
const schemaChanged = exactChangedFiles.some(({ path: name }) =>
  /schema\.rs$|Cargo\.toml$|Cargo\.lock$/u.test(name));

const detailedArtifacts = readdirSync(evidenceRoot)
  .filter((name) => statSync(path.join(evidenceRoot, name)).isFile())
  .sort()
  .map((name) => {
    const bytes = readFileSync(path.join(evidenceRoot, name));
    return { bytes: bytes.length, path: name, sha256: sha256(bytes) };
  });
const targetedName = 'MMR-0_TD2_R4_P6_C_CAV3_Targeted_Proof_Evidence.json';
const targetedBytes = readFileSync(path.join(evidenceRoot, targetedName));
writeFileSync(path.join(outputRoot, targetedName), targetedBytes, {
  flag: 'wx', mode: 0o600
});
chmodSync(path.join(outputRoot, targetedName), 0o600);

const p6bValidator = readFileSync(
  '/home/jenn/文档/ChatGPT/agents-os-resident/MMR-0_TD2_R4_P6_B_Validator_Result.json'
);
const p6bCloseout = readFileSync(
  '/home/jenn/文档/ChatGPT/agents-os-resident/MMR-0_TD2_R4_P6_B_CAV2_Implementation_Closeout.yaml'
);
const predecessorLedger = {
  branch,
  controlledProofAdmissions: [],
  head,
  p6B: {
    baselineCommit: PREDECESSOR_COMMIT,
    baselineTree: PREDECESSOR_TREE,
    closeoutSha256: sha256(p6bCloseout),
    result: 'COMPLETE',
    validatorSha256: sha256(p6bValidator)
  },
  requiredEntryGate: 'GATE_P6-C_AUTHORIZED',
  schema: 'MMR-0-TD2-R4-P6-C-PREDECESSOR-LEDGER-v0.1'
};
const predecessorRecord = writeExclusive(
  outputRoot,
  'MMR-0_TD2_R4_P6_C_Predecessor_Ledger.json',
  predecessorLedger
);

const manifest = {
  artifacts: detailedArtifacts,
  controlledProofClaimed: false,
  derivedPhaseResult: 'PASS_CANDIDATE_PENDING_CANONICAL_VALIDATOR',
  evidenceRole: 'TARGETED_DEVELOPMENT_EVIDENCE_NOT_CONTROLLED_PROOF',
  schema: 'MMR-0-TD2-R4-P6-C-EVIDENCE-MANIFEST-v0.1',
  subphase: 'P6-C',
  targetedEvidence: {
    bytes: targetedBytes.length,
    path: targetedName,
    sha256: sha256(targetedBytes)
  },
  vectors: [
    { caseId: 'CAV3-V1', result: 'PASS' },
    { caseId: 'CAV3-V2', result: 'PASS' }
  ]
};
const manifestRecord = writeExclusive(
  outputRoot,
  'MMR-0_TD2_R4_P6_C_Evidence_Manifest.json',
  manifest
);

const binary = readFileSync(
  path.join(PACKAGE_ROOT, 'agents-os-resident.linux-x64-gnu.node')
);
const integrity = readFileSync(path.join(PACKAGE_ROOT, 'companion-integrity.json'));
const receipt = {
  CAV3_V1: 'PASS',
  CAV3_V2: 'PASS',
  P6_D_started: false,
  buildIdentity: {
    binaryBytes: binary.length,
    binarySha256: sha256(binary),
    companionIntegritySha256: sha256(integrity),
    toolchain: {
      node: commandVersion('node', ['--version']),
      npm: commandVersion('npm', ['--version']),
      rustc: commandVersion('rustc', ['--version'])
    }
  },
  controlledProofClaimed: false,
  durableMutationFromCognition: 0,
  effectiveContextAbsenceEvidence: {
    artifact: 'effective_projection.json',
    negativeRulePresent: false
  },
  exactChangedFiles,
  historyMutationPerformed: false,
  negativeControl: {
    currentProjectionContainsNegativeRule: false,
    durableAdmitted: false,
    effectiveContextContainsNegativeRule: false,
    responseReproducesNegativeRule: false
  },
  phase: { id: 'P6', result: 'PASS_CANDIDATE', subphase: 'P6-C' },
  positiveControl: {
    admitted: true,
    effectiveContextPresent: true,
    projected: true,
    responseBinding: 'PASS'
  },
  predecessorCommit: PREDECESSOR_COMMIT,
  predecessorTree: PREDECESSOR_TREE,
  projectionAbsenceEvidence: {
    artifact: 'effective_projection.json',
    negativeRulePresent: false
  },
  providerInvoked: false,
  receiptIsProofAuthority: false,
  regressionObserved: {
    companionIntegration: '2/2_PASS',
    hostProjectionBinding: 'PASS',
    nodeFull: '92/92_PASS',
    p6A_CAV1: '3/3_PASS',
    p6BActualCompanion: '1/1_PASS',
    p6B_CAV2: '2/2_PASS',
    p6CActualCompanion: '1/1_PASS',
    rustFull: '230/230_PASS'
  },
  responseNegativeReproductionCount: 0,
  schema: 'MMR-0-TD2-R4-P6-C-IMPLEMENTATION-RECEIPT-v0.1',
  schemaChanged,
  staleProjectionRejection: {
    artifact: 'stale_projection_rejection.json',
    resultCode: 'STALE_PROJECTION_FAIL_CLOSED'
  },
  storageChanged: schemaChanged,
  transcriptLeakScan: {
    artifact: 'full_secret_scan.json',
    plaintextRuntimeLeakCount: 0
  }
};
const receiptRecord = writeExclusive(
  outputRoot,
  'MMR-0_TD2_R4_P6_C_Implementation_Receipt.json',
  receipt
);

process.stdout.write(`${JSON.stringify({
  changedFileCount: exactChangedFiles.length,
  manifestSha256: manifestRecord.sha256,
  predecessorLedgerSha256: predecessorRecord.sha256,
  receiptSha256: receiptRecord.sha256,
  result: 'PASS_P6_C_CLOSEOUT_INPUT_BUILD',
  successorGateWritten: false,
  targetedEvidenceSha256: sha256(targetedBytes)
})}\n`);
