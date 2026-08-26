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

export function checkR2ValidationPrerequisites(environment = process.env) {
  const workspaceRoot = environment.AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT;
  const recoveryRoot = environment.MMR_P4A_RECOVERY_DOMAIN;
  if (typeof workspaceRoot !== 'string' || workspaceRoot.length === 0) {
    throw new Error('WORKSPACE_ROOT_UNDECLARED');
  }
  if (typeof recoveryRoot !== 'string' || recoveryRoot.length === 0) {
    throw new Error('RECOVERY_DOMAIN_UNDECLARED');
  }
  const canonicalWorkspace = resolve(workspaceRoot);
  const hostRoot = resolve(canonicalWorkspace, 'runtime/VCPToolBox');
  const chatRoot = resolve(canonicalWorkspace, 'runtime/VCPChat');
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
      identityOrCommit: repositoryIdentity(chatRoot),
      sourceBundle: sourceBundle(chatRoot, CHAT_FILES)
    },
    VCPToolBox: {
      identityOrCommit: repositoryIdentity(hostRoot),
      sourceBundle: sourceBundle(hostRoot, HOST_FILES)
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
