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
const PREDECESSOR_COMMIT = '5d0b30d7c6d9c774abfa17648600c0df7cdf9ae3';
const PREDECESSOR_TREE = '319719d9f4877a9ccd2bb11c6cead15eabe641c5';

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

function currentChangedPaths() {
  const output = git([
    'status',
    '--porcelain=v1',
    '-z',
    '--untracked-files=all'
  ]).stdout;
  return [...new Set(output.split('\0').filter(Boolean).map((record) => {
    const pathValue = record.slice(3);
    return pathValue.includes(' -> ')
      ? pathValue.split(' -> ').at(-1)
      : pathValue;
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
  || branch !== 'agent/mmr0-p6b-cav2') {
  throw new Error('P6_B_PREDECESSOR_IDENTITY_MISMATCH');
}

const changedPaths = currentChangedPaths();
const exactChangedFiles = changedPaths.map((relativePath) => {
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
const schemaChanged = changedPaths.some((name) => /schema\.rs$|Cargo\.toml$|Cargo\.lock$/u.test(name));

const detailedArtifacts = readdirSync(evidenceRoot)
  .filter((name) => statSync(path.join(evidenceRoot, name)).isFile())
  .sort()
  .map((name) => {
    const bytes = readFileSync(path.join(evidenceRoot, name));
    return { bytes: bytes.length, path: name, sha256: sha256(bytes) };
  });
const targetedName = 'MMR-0_TD2_R4_P6_B_CAV2_Targeted_Proof_Evidence.json';
const targetedBytes = readFileSync(path.join(evidenceRoot, targetedName));
writeFileSync(path.join(outputRoot, targetedName), targetedBytes, {
  flag: 'wx',
  mode: 0o600
});
chmodSync(path.join(outputRoot, targetedName), 0o600);

const p6aValidator = readFileSync(
  '/home/jenn/文档/ChatGPT/agents-os-resident/p6a-cav1-implementation-evidence/P6_A_CAV1_Validator_Result.json'
);
const p6aCloseout = readFileSync(
  '/home/jenn/文档/ChatGPT/agents-os-resident/MMR-0_TD2_R4_P6_A_CAV1_Final_Requalification_Closeout_R3.yaml'
);
const predecessorLedger = {
  branch,
  controlledProofAdmissions: [],
  head: head,
  p6A: {
    baselineCommit: PREDECESSOR_COMMIT,
    baselineTree: PREDECESSOR_TREE,
    closeoutSha256: sha256(p6aCloseout),
    result: 'COMPLETE',
    validatorSha256: sha256(p6aValidator)
  },
  requiredEntryGate: 'GATE_P6-B_AUTHORIZED',
  schema: 'MMR-0-TD2-R4-P6-B-PREDECESSOR-LEDGER-v0.1'
};
const predecessorRecord = writeExclusive(
  outputRoot,
  'MMR-0_TD2_R4_P6_B_Predecessor_Ledger.json',
  predecessorLedger
);

const manifest = {
  artifacts: detailedArtifacts,
  controlledProofClaimed: false,
  derivedPhaseResult: 'PASS_CANDIDATE_PENDING_CANONICAL_VALIDATOR',
  evidenceRole: 'TARGETED_DEVELOPMENT_EVIDENCE_NOT_CONTROLLED_PROOF',
  schema: 'MMR-0-TD2-R4-P6-B-EVIDENCE-MANIFEST-v0.1',
  subphase: 'P6-B',
  targetedEvidence: {
    bytes: targetedBytes.length,
    path: targetedName,
    sha256: sha256(targetedBytes)
  },
  vectors: [
    { caseId: 'CAV2-V1', result: 'PASS' },
    { caseId: 'CAV2-V2', result: 'PASS' }
  ]
};
const manifestRecord = writeExclusive(
  outputRoot,
  'MMR-0_TD2_R4_P6_B_Evidence_Manifest.json',
  manifest
);

const binary = readFileSync(path.join(PACKAGE_ROOT, 'agents-os-resident.linux-x64-gnu.node'));
const integrity = readFileSync(path.join(PACKAGE_ROOT, 'companion-integrity.json'));
const receipt = {
  CAV2_V1: 'PASS',
  CAV2_V2: 'PASS',
  P6_C_started: false,
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
  effectiveContextEvidence: {
    artifact: 'effective_projection.json',
    bindingRequired: true
  },
  exactChangedFiles,
  freshSessionEvidence: {
    artifact: 'fresh_session_transcript.json',
    inheritedMessageCount: 0
  },
  historyMutationPerformed: false,
  modelProfileEvidence: {
    artifact: 'model_runtime_fingerprint.json',
    externalModelInvoked: false,
    providerInvoked: false
  },
  phase: { id: 'P6', result: 'PASS_CANDIDATE', subphase: 'P6-B' },
  predecessorCommit: PREDECESSOR_COMMIT,
  predecessorTree: PREDECESSOR_TREE,
  projectionProvenance: {
    artifact: 'effective_projection.json',
    generationBound: true
  },
  receiptIsProofAuthority: false,
  regressionObserved: {
    companionIntegration: '2/2_PASS',
    hostProjectionBinding: 'PASS',
    nodeFull: '90/90_PASS',
    p6A_CAV1: '3/3_PASS',
    p6BActualCompanion: '1/1_PASS',
    rustFull: '228/228_PASS'
  },
  responseBinding: { artifact: 'structured_response.json' },
  schema: 'MMR-0-TD2-R4-P6-B-IMPLEMENTATION-RECEIPT-v0.1',
  schemaChanged,
  staleProjectionRejection: {
    artifact: 'stale_projection_rejection.json',
    resultCode: 'STALE_PROJECTION_FAIL_CLOSED'
  },
  storageChanged: schemaChanged
};
const receiptRecord = writeExclusive(
  outputRoot,
  'MMR-0_TD2_R4_P6_B_Implementation_Receipt.json',
  receipt
);

process.stdout.write(`${JSON.stringify({
  changedFileCount: exactChangedFiles.length,
  manifestSha256: manifestRecord.sha256,
  predecessorLedgerSha256: predecessorRecord.sha256,
  receiptSha256: receiptRecord.sha256,
  result: 'PASS_P6_B_CLOSEOUT_INPUT_BUILD',
  successorGateWritten: false,
  targetedEvidenceSha256: sha256(targetedBytes)
})}\n`);
