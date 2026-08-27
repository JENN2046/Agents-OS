import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  lstatSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
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
    sourceBundleSha256: 'ae719c7c228fd7dcce5156e3ce2c59e63f43778a6fa3cc5594d819b339fb65c0'
  }),
  VCPToolBox: Object.freeze({
    identityOrCommit: '028bb4747c148cddf7545421aeced5a261bba8b7',
    sourceBundleSha256: 'fd4fe5dfb2445c9ce9e4482182c00fba2a1edd4a771cafe9042d513b2f5a2434'
  })
});

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function repositoryIdentity(root) {
  try {
    return execFileSync('git', ['rev-parse', 'HEAD'], {
      cwd: root,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore']
    }).trim();
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
  if (actual.sourceBundle.sha256 !== expected.sourceBundleSha256) {
    throw new Error(`${label}_SOURCE_BUNDLE_MISMATCH`);
  }
  return actual;
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
  const canonicalWorkspace = resolve(workspaceRoot);
  const hostRoot = resolve(canonicalWorkspace, 'runtime/VCPToolBox');
  const chatRoot = resolve(canonicalWorkspace, 'runtime/VCPChat');
  if (resolve(declaredChatRoot) !== chatRoot) {
    throw new Error('VCPCHAT_CHECKED_ROOT_NOT_EXERCISED_ROOT');
  }
  const recovery = resolve(recoveryRoot);
  const recoveryStat = statSync(recovery);
  if (!recoveryStat.isDirectory()
    || recoveryStat.dev === statSync(PACKAGE_ROOT).dev) {
    throw new Error('RECOVERY_DOMAIN_NOT_INDEPENDENT');
  }
  const probe = mkdtempSync(resolve(recovery, 'resident-r2-preflight-'));
  try {
    writeFileSync(resolve(probe, 'write-probe'), 'R2_VALIDATION_PROBE\n', {
      flag: 'wx',
      mode: 0o600
    });
  } finally {
    rmSync(probe, { recursive: true, force: true });
  }
  const chat = enforceExpectedRepository('VCPCHAT', {
    identityOrCommit: repositoryIdentity(chatRoot),
    sourceBundle: sourceBundle(chatRoot, CHAT_FILES),
    selectedSourceStatus: selectedSourceStatus(chatRoot, CHAT_FILES)
  }, expected.VCPChat);
  const host = enforceExpectedRepository('VCPTOOLBOX', {
    identityOrCommit: repositoryIdentity(hostRoot),
    sourceBundle: sourceBundle(hostRoot, HOST_FILES),
    selectedSourceStatus: selectedSourceStatus(hostRoot, HOST_FILES)
  }, expected.VCPToolBox);
  return Object.freeze({
    result: 'R2_VALIDATION_PREREQUISITES_AVAILABLE',
    recoveryDomain: {
      independentDevice: true,
      provisioningCheck: 'OWNER_WRITABLE_TEMP_PROBE_PASS',
      requiredProperties: [
        'directory',
        'owner-writable',
        'device-distinct-from-candidate-worktree'
      ]
    },
    VCPChat: {
      ...chat,
      checkedRootMatchesExercisedRoot: true
    },
    VCPToolBox: host
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
