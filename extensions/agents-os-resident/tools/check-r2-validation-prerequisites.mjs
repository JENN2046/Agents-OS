import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  closeSync,
  fsyncSync,
  lstatSync,
  mkdtempSync,
  openSync,
  readFileSync,
  realpathSync,
  rmSync,
  writeFileSync
} from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const RECONCILIATION_FREEZE =
  '/home/jenn/文档/ChatGPT/agents-os-resident/VCPToolBox_Selected_Source_Canonical_Baseline_R1.yaml';
const RECONCILIATION_FREEZE_SHA256 =
  'ff2702214dc630aef213103d0b6cb9982130c1a6f869ded3a9a2e2a30f29d44c';
const HOST_FILES = Object.freeze([
  'Plugin.js',
  'modules/chatCompletionHandler.js',
  'modules/handlers/nonStreamHandler.js',
  'modules/handlers/streamHandler.js',
  'modules/vcpLoop/toolExecutor.js',
  'modules/vcpLoop/residentPresentation.js'
]);
const CHAT_FILES = Object.freeze([
  'modules/messageRenderer.js',
  'modules/renderer/streamManager.js',
  'modules/renderer/residentEphemeralPresentation.mjs',
  'modules/ipc/chatHandlers.js',
  'modules/vcpClient.js',
  'renderer.js',
  'styles/messageRenderer.css',
  'node_modules/jsdom/package.json'
]);
export const EXPECTED_R2_PREREQUISITES = Object.freeze({
  VCPChat: Object.freeze({
    identityOrCommit: 'f743b88b631fae761d68275abd2b131fa92f59ef',
    treeOid: 'd7a2ebb9afd3fcb2efb26302ee7176271aa33213',
    sourceBundleSha256: 'ae719c7c228fd7dcce5156e3ce2c59e63f43778a6fa3cc5594d819b339fb65c0'
  }),
  VCPToolBox: Object.freeze({
    identityOrCommit: '08a2164b38a8fc01d385998c3d71c4a434c3af9c',
    treeOid: 'dcea4f0f6fc6d43eee992153d19e7cf18308245e',
    sourceBundleSha256: 'fd4fe5dfb2445c9ce9e4482182c00fba2a1edd4a771cafe9042d513b2f5a2434'
  })
});

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function repositoryIdentity(root) {
  try {
    const identityOrCommit = execFileSync('git', ['rev-parse', 'HEAD'], {
      cwd: realpathSync(root),
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore']
    }).trim();
    const treeOid = execFileSync('git', ['rev-parse', 'HEAD^{tree}'], {
      cwd: realpathSync(root),
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore']
    }).trim();
    return Object.freeze({ identityOrCommit, treeOid });
  } catch {
    throw new Error('GIT_IDENTITY_UNAVAILABLE');
  }
}

function sourceBundle(root, paths) {
  const rows = paths.map((relativePath) => {
    const absolute = resolve(root, relativePath);
    const stat = lstatSync(absolute);
    if (!stat.isFile() || stat.isSymbolicLink()) {
      throw new Error(`SOURCE_INVALID:${relativePath}`);
    }
    const bytes = readFileSync(absolute);
    return { byteLength: bytes.length, path: relativePath, sha256: sha256(bytes) };
  });
  return {
    files: rows,
    sha256: sha256(Buffer.from(JSON.stringify(rows), 'utf8'))
  };
}

function selectedSourceStatus(root, paths) {
  try {
    const porcelain = execFileSync('git', ['status', '--porcelain', '--', ...paths], {
      cwd: root,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore']
    });
    return Object.freeze({
      dirtyPolicy: 'HASH_BIND_EXACT_EXERCISED_BYTES',
      statusSha256: sha256(Buffer.from(porcelain, 'utf8')),
      worktreeClean: porcelain.length === 0
    });
  } catch {
    throw new Error('GIT_STATUS_UNAVAILABLE');
  }
}

export function enforceExpectedRepository(label, actual, expected) {
  if (actual.identityOrCommit !== expected.identityOrCommit) {
    throw new Error(`${label}_COMMIT_MISMATCH`);
  }
  if (actual.treeOid !== expected.treeOid) {
    throw new Error(`${label}_TREE_MISMATCH`);
  }
  if (actual.sourceBundle.sha256 !== expected.sourceBundleSha256) {
    throw new Error(`${label}_SOURCE_BUNDLE_MISMATCH`);
  }
  if (actual.selectedSourceStatus?.worktreeClean !== true) {
    throw new Error(`${label}_SELECTED_SOURCE_DIRTY`);
  }
  return actual;
}

function runCanonicalRecoveryQualifier(arguments_, input) {
  let output;
  try {
    output = execFileSync('cargo', [
      'run', '--quiet', '--bin', 'p4a-recovery-qualifier', '--', ...arguments_
    ], {
      cwd: PACKAGE_ROOT,
      encoding: 'utf8',
      input,
      maxBuffer: 16 * 1024 * 1024,
      stdio: ['pipe', 'pipe', 'pipe']
    });
  } catch {
    throw new Error('CANONICAL_RECOVERY_QUALIFIER_FAILED');
  }
  try {
    return Object.freeze(JSON.parse(output));
  } catch {
    throw new Error('CANONICAL_RECOVERY_QUALIFIER_OUTPUT_INVALID');
  }
}

export function qualifyRecoveryDomain(liveRoot, recoveryRoot) {
  return runCanonicalRecoveryQualifier([
    '--live', realpathSync(liveRoot),
    '--recovery', realpathSync(recoveryRoot)
  ]);
}

export function qualifyRecoveryFixtureIdentity(fixtureIdentity) {
  return runCanonicalRecoveryQualifier(
    ['--classify-json'],
    `${JSON.stringify(fixtureIdentity)}\n`
  );
}

function verifyRecoveryWriteAndSync(recovery) {
  const probe = mkdtempSync(resolve(recovery, 'resident-r2-preflight-'));
  try {
    const file = resolve(probe, 'write-probe');
    writeFileSync(file, 'R2_VALIDATION_PROBE\n', {
      flag: 'wx',
      mode: 0o600
    });
    const fileDescriptor = openSync(file, 'r');
    try {
      fsyncSync(fileDescriptor);
    } finally {
      closeSync(fileDescriptor);
    }
    const directoryDescriptor = openSync(probe, 'r');
    try {
      fsyncSync(directoryDescriptor);
    } finally {
      closeSync(directoryDescriptor);
    }
  } finally {
    rmSync(probe, { recursive: true, force: true });
  }
}

export function checkR2ValidationPrerequisites(
  environment = process.env,
  expected = EXPECTED_R2_PREREQUISITES
) {
  const workspaceRoot = environment.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT;
  const declaredChatRoot = environment.AGENTS_OS_RESIDENT_VCPCHAT_ROOT;
  const recoveryRoot = environment.MMR_P4A_RECOVERY_DOMAIN;
  if (typeof workspaceRoot !== 'string' || workspaceRoot.length === 0) {
    throw new Error('WORKSPACE_ROOT_UNDECLARED');
  }
  if (typeof recoveryRoot !== 'string' || recoveryRoot.length === 0) {
    throw new Error('RECOVERY_DOMAIN_UNDECLARED');
  }
  if (typeof declaredChatRoot !== 'string' || declaredChatRoot.length === 0) {
    throw new Error('VCPCHAT_ROOT_UNDECLARED');
  }
  const declaredWorkspace = resolve(workspaceRoot);
  const declaredExercisedChatRoot = resolve(
    declaredWorkspace,
    'runtime/VCPChat'
  );
  if (resolve(declaredChatRoot) !== declaredExercisedChatRoot) {
    throw new Error('VCPCHAT_CHECKED_ROOT_NOT_EXERCISED_ROOT');
  }
  if (sha256(readFileSync(RECONCILIATION_FREEZE))
    !== RECONCILIATION_FREEZE_SHA256) {
    throw new Error('VCPTOOLBOX_BASELINE_FREEZE_MISMATCH');
  }
  const recovery = realpathSync(resolve(recoveryRoot));
  const recoveryQualification = qualifyRecoveryDomain(PACKAGE_ROOT, recovery);
  if (!recoveryQualification.admitted) {
    throw new Error('RECOVERY_DOMAIN_NOT_INDEPENDENT_OR_DURABLE');
  }
  verifyRecoveryWriteAndSync(recovery);
  const canonicalWorkspace = realpathSync(declaredWorkspace);
  const hostRoot = realpathSync(resolve(canonicalWorkspace, 'runtime/VCPToolBox'));
  const chatRoot = realpathSync(resolve(canonicalWorkspace, 'runtime/VCPChat'));
  if (realpathSync(resolve(declaredChatRoot)) !== chatRoot) {
    throw new Error('VCPCHAT_CHECKED_ROOT_NOT_EXERCISED_ROOT');
  }
  const chatIdentity = repositoryIdentity(chatRoot);
  const chat = enforceExpectedRepository('VCPCHAT', {
    ...chatIdentity,
    sourceBundle: sourceBundle(chatRoot, CHAT_FILES),
    selectedSourceStatus: selectedSourceStatus(chatRoot, CHAT_FILES)
  }, expected.VCPChat);
  const hostIdentity = repositoryIdentity(hostRoot);
  const host = enforceExpectedRepository('VCPTOOLBOX', {
    ...hostIdentity,
    sourceBundle: sourceBundle(hostRoot, HOST_FILES),
    selectedSourceStatus: selectedSourceStatus(hostRoot, HOST_FILES)
  }, expected.VCPToolBox);
  return Object.freeze({
    result: 'R2_VALIDATION_PREREQUISITES_AVAILABLE',
    resolvedExecutionRoots: {
      validationWorkspaceRoot: canonicalWorkspace,
      VCPChatRoot: chatRoot,
      recoveryDomain: recovery,
      matchFrozenEnvironment: true
    },
    recoveryDomain: {
      ...recoveryQualification,
      provisioningCheck: 'OWNER_WRITABLE_FSYNC_PROBE_PASS',
      requiredProperties: [
        'durable-nonvolatile-filesystem',
        'persistence-marker',
        'owner-writable',
        'device-distinct-from-candidate-worktree',
        'mount-distinct-from-candidate-worktree',
        'underlying-failure-domain-distinct-from-candidate-worktree'
      ]
    },
    VCPChat: {
      ...chat,
      checkedRootMatchesExercisedRoot: true
    },
    VCPToolBox: {
      ...host,
      baselineFreezeSha256: RECONCILIATION_FREEZE_SHA256,
      checkedRootMatchesExercisedRoot: true
    }
  });
}

function main(argv) {
  if (argv.length !== 1 || argv[0] !== '--check') {
    throw new Error('ARGUMENTS_INVALID');
  }
  process.stdout.write(`${JSON.stringify(checkR2ValidationPrerequisites())}\n`);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(
      `R2_VALIDATION_PREREQUISITE_MISSING:${error.message}\n`
    );
    process.exit(2);
  }
}
