#!/usr/bin/env node

import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import EventEmitter from 'node:events';
import * as nodeFs from 'node:fs';
import {
  lstat,
  mkdir,
  readFile,
  readdir,
  realpath,
  rmdir,
  unlink,
  writeFile
} from 'node:fs/promises';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const SCRIPT_DIR = path.dirname(SCRIPT_PATH);
const WORKSPACE_ROOT = path.resolve(SCRIPT_DIR, '../..');
const PLAN_RELATIVE =
  'control-plane/registry/drafts/2026-07-25-agents-os-phase-5d-m0d-minimum-exact-host-smoke-plan-v0.3.json';
const PLAN_PATH = path.join(WORKSPACE_ROOT, PLAN_RELATIVE);
const TEST_RELATIVE =
  'execution/agents-os-phase5d-host-smoke/one-shot-host-smoke.test.mjs';
const TEST_PATH = path.join(WORKSPACE_ROOT, TEST_RELATIVE);
const PROC_SELF_STATUS_PATH = '/proc/self/status';
const MAX_WORKER_OUTPUT_BYTES = 4 * 1024 * 1024;
const TRANSPORT_REQUEST_NAME = '.agents-os-worker-request.json';
const TRANSPORT_OUTPUT_NAME = '.agents-os-worker-output.json';
const TRANSPORT_ERROR_NAME = '.agents-os-worker-error.txt';

const ROOT_KEYS = [
  'schema_version',
  'candidate_id',
  'status',
  'execution_authorized',
  'trust_root',
  'sealed_host',
  'isolation',
  'host_adapter',
  'inert_payload',
  'paths',
  'expected_observation',
  'forbidden'
];
const METHOD_SEQUENCE = [
  'PluginManager.loadPlugins',
  'InertPayload.initialize',
  'PluginManager.shutdownAllPlugins',
  'InertPayload.shutdown',
  'Harness.quarantineCleanup'
];
const REQUIRE_ALLOWLIST = [
  'fs',
  'events',
  'path',
  'child_process',
  'node-schedule',
  'dotenv',
  './FileFetcherServer.js',
  'express',
  'chokidar',
  './modules/captchaDecoder',
  './modules/toolApprovalManager',
  './modules/foldProtocol',
  './modules/toolResultPrivacyGuard',
  './modules/toolCallRecordStore',
  'EXACT_INERT_ENTRYPOINT'
];
const GIT_OPERATION_SEQUENCE = [
  'SEALED_COMMIT_EXISTS',
  'SEALED_TREE_RESOLVE',
  'PLUGIN_MANAGER_BLOB_RESOLVE',
  'PLUGIN_MANAGER_BLOB_READ'
];
const FILESYSTEM_READ_ALLOWLIST = [
  'Plugin',
  'Plugin/AGENTSOSResident/plugin-manifest.json',
  'Plugin/AGENTSOSResident/config.env',
  'preprocessor_order.json'
];
const FORBIDDEN = [
  'processToolCall',
  'native_or_NAPI_load',
  'database',
  'provider_or_network',
  'production_authentication',
  'private_Memory_or_state-private',
  'sensing_or_recording',
  'real_effect',
  'VCPToolBox_source_write',
  'canonical_worktree_write',
  'ordinary_plugin_population_read'
];
const OWNER_MARKER_BYTES = Buffer.from(
  '{"owner":"PHASE_5D_M0D_MINIMUM_EXACT_HOST_SMOKE_CANDIDATE_V0_3"}\n',
  'utf8'
);
const OUTER_OWNER_MARKER = '.agents-os-phase5d-sandbox-owner';
const OUTER_OWNER_MARKER_BYTES = Buffer.from(
  '{"owner":"PHASE_5D_M0D_MINIMUM_EXACT_HOST_SMOKE_CANDIDATE_V0_3_SANDBOX"}\n',
  'utf8'
);
const ISOLATED_PROFILES = [
  'SYNTHETIC_NORMAL',
  'SYNTHETIC_PROCESS_TOOL_CALL',
  'SYNTHETIC_UNKNOWN_REQUIRE',
  'SYNTHETIC_OUTSIDE_READ',
  'SYNTHETIC_BUFFER_ESCAPE',
  'SYNTHETIC_OUTER_FUNCTION_ESCAPE',
  'ACTUAL_SEALED_HOST'
];

class Blocked extends Error {
  constructor(code, detail = null) {
    super(code);
    this.name = 'Blocked';
    this.code = code;
    this.detail = detail;
  }
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

async function sha256File(filePath) {
  return sha256(await readFile(filePath));
}

async function requireRegularNoFollow(filePath, code) {
  let metadata;
  try {
    metadata = await lstat(filePath);
  } catch (error) {
    throw new Blocked(code, error.code ?? 'LSTAT_FAILED');
  }
  if (!metadata.isFile() || (await realpath(filePath)) !== path.resolve(filePath)) {
    throw new Blocked(code, 'NOT_REGULAR_NOFOLLOW');
  }
}

function openedFileIdentity(metadata) {
  return {
    dev: metadata.dev,
    ino: metadata.ino,
    mode: metadata.mode,
    nlink: metadata.nlink,
    size: metadata.size,
    mtimeNs: metadata.mtimeNs,
    ctimeNs: metadata.ctimeNs
  };
}

async function readOpenedRegularFile(
  handle,
  { code, minBytes = 0, maxBytes, exactBytes = null }
) {
  let before;
  try {
    before = await handle.stat({ bigint: true });
  } catch (error) {
    throw new Blocked(code, error?.code ?? 'FSTAT_FAILED');
  }
  if (
    !before.isFile() ||
    before.nlink !== 0n ||
    before.size < BigInt(minBytes) ||
    before.size > BigInt(maxBytes) ||
    (exactBytes !== null && before.size !== BigInt(exactBytes))
  ) {
    throw new Blocked(code, 'OPEN_FD_SHAPE_OR_SIZE');
  }
  const byteCount = Number(before.size);
  if (!Number.isSafeInteger(byteCount)) {
    throw new Blocked(code, 'OPEN_FD_SIZE_UNSAFE');
  }
  const bytes = Buffer.alloc(byteCount);
  let offset = 0;
  while (offset < byteCount) {
    let bytesRead;
    try {
      ({ bytesRead } = await handle.read(
        bytes,
        offset,
        byteCount - offset,
        offset
      ));
    } catch (error) {
      throw new Blocked(code, error?.code ?? 'OPEN_FD_READ_FAILED');
    }
    if (bytesRead <= 0) {
      throw new Blocked(code, 'OPEN_FD_SHORT_READ');
    }
    offset += bytesRead;
  }
  const eofProbe = Buffer.alloc(1);
  let trailingBytes;
  try {
    ({ bytesRead: trailingBytes } = await handle.read(
      eofProbe,
      0,
      1,
      byteCount
    ));
  } catch (error) {
    throw new Blocked(code, error?.code ?? 'OPEN_FD_EOF_READ_FAILED');
  }
  if (trailingBytes !== 0) {
    throw new Blocked(code, 'OPEN_FD_TRAILING_BYTES');
  }
  let after;
  try {
    after = await handle.stat({ bigint: true });
  } catch (error) {
    throw new Blocked(code, error?.code ?? 'FSTAT_FAILED');
  }
  try {
    assert.deepStrictEqual(openedFileIdentity(after), openedFileIdentity(before));
  } catch {
    throw new Blocked(code, 'OPEN_FD_CHANGED_DURING_READ');
  }
  return { bytes, metadata: after };
}

async function createUnlinkedRegularFile(root, relativeName, code) {
  const filePath = path.join(root, relativeName);
  let handle = null;
  try {
    handle = await nodeFs.promises.open(
      filePath,
      nodeFs.constants.O_RDWR |
        nodeFs.constants.O_CREAT |
        nodeFs.constants.O_EXCL |
        nodeFs.constants.O_NOFOLLOW,
      0o600
    );
    const metadata = await handle.stat({ bigint: true });
    if (
      !metadata.isFile() ||
      metadata.size !== 0n ||
      metadata.nlink !== 1n ||
      (metadata.mode & 0o777n) !== 0o600n
    ) {
      throw new Blocked(code, 'TRANSPORT_FD_INITIAL_SHAPE');
    }
    await unlink(filePath);
    const unlinked = await handle.stat({ bigint: true });
    if (!unlinked.isFile() || unlinked.size !== 0n || unlinked.nlink !== 0n) {
      throw new Blocked(code, 'TRANSPORT_FD_NOT_UNLINKED');
    }
    return { filePath, handle };
  } catch (error) {
    if (handle) {
      try {
        await handle.close();
      } catch {
        // The original fail-closed error remains authoritative.
      }
    }
    if (error instanceof Blocked) throw error;
    throw new Blocked(code, error?.code ?? error?.name);
  }
}

async function positionalWrite(handle, bytes, code) {
  let offset = 0;
  while (offset < bytes.length) {
    let bytesWritten;
    try {
      ({ bytesWritten } = await handle.write(
        bytes,
        offset,
        bytes.length - offset,
        offset
      ));
    } catch (error) {
      throw new Blocked(code, error?.code ?? 'OPEN_FD_WRITE_FAILED');
    }
    if (bytesWritten <= 0) {
      throw new Blocked(code, 'OPEN_FD_SHORT_WRITE');
    }
    offset += bytesWritten;
  }
  try {
    await handle.sync();
  } catch (error) {
    throw new Blocked(code, error?.code ?? 'OPEN_FD_SYNC_FAILED');
  }
  const metadata = await handle.stat({ bigint: true });
  if (metadata.size !== BigInt(bytes.length) || metadata.nlink !== 0n) {
    throw new Blocked(code, 'OPEN_FD_WRITE_SIZE');
  }
}

async function closeHandle(materialized) {
  if (!materialized?.handle) return 'NOT_CREATED';
  try {
    await materialized.handle.close();
    materialized.handle = null;
    return 'CLEAN';
  } catch {
    return 'RESIDUE_UNVERIFIED';
  }
}

function canonicalJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

async function readCanonicalJson(filePath, code) {
  await requireRegularNoFollow(filePath, code);
  let bytes;
  try {
    bytes = await readFile(filePath);
  } catch (error) {
    throw new Blocked(code, error.code ?? 'READ_FAILED');
  }
  const text = bytes.toString('utf8');
  let value;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Blocked(code, 'INVALID_JSON');
  }
  if (canonicalJson(value) !== text) {
    throw new Blocked(code, 'NONCANONICAL_OR_DUPLICATE_KEYS');
  }
  return { value, bytes };
}

function exactKeys(value, expected, label) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new Blocked('BLOCKED_PLAN_SCHEMA', label);
  }
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (
    actual.length !== wanted.length ||
    actual.some((key, index) => key !== wanted[index])
  ) {
    throw new Blocked('BLOCKED_PLAN_SCHEMA', label);
  }
}

function exactValue(actual, expected, label) {
  try {
    assert.deepStrictEqual(actual, expected);
  } catch {
    throw new Blocked('BLOCKED_PLAN_VALUE', label);
  }
}

function safeWorkspaceRelative(relativePath, requiredPrefix) {
  return (
    typeof relativePath === 'string' &&
    relativePath.length > requiredPrefix.length &&
    relativePath.normalize('NFC') === relativePath &&
    relativePath.startsWith(requiredPrefix) &&
    !path.isAbsolute(relativePath) &&
    !relativePath.includes('\\') &&
    !relativePath.split('/').some((part) => part === '' || part === '.' || part === '..')
  );
}

function decodePayload(row, label) {
  exactKeys(row, ['relative_path', 'byte_count', 'sha256', 'base64'], label);
  if (
    typeof row.relative_path !== 'string' ||
    !Number.isSafeInteger(row.byte_count) ||
    row.byte_count <= 0 ||
    !/^[0-9a-f]{64}$/.test(row.sha256) ||
    typeof row.base64 !== 'string'
  ) {
    throw new Blocked('BLOCKED_PLAN_SCHEMA', label);
  }
  const bytes = Buffer.from(row.base64, 'base64');
  if (
    bytes.length !== row.byte_count ||
    sha256(bytes) !== row.sha256 ||
    bytes.toString('base64') !== row.base64
  ) {
    throw new Blocked('BLOCKED_PAYLOAD_BINDING', label);
  }
  return bytes;
}

export function validatePlanDocument(plan) {
  exactKeys(plan, ROOT_KEYS, 'root');
  exactValue(
    {
      schema_version: plan.schema_version,
      candidate_id: plan.candidate_id,
      status: plan.status,
      execution_authorized: plan.execution_authorized
    },
    {
      schema_version: 'agents-os.phase5d.minimum-exact-host-smoke-plan.v0.3',
      candidate_id: 'PHASE_5D_M0D_MINIMUM_EXACT_HOST_SMOKE_CANDIDATE_V0_3',
      status: 'CANDIDATE_FOR_INDEPENDENT_REVIEW',
      execution_authorized: false
    },
    'identity'
  );

  exactKeys(
    plan.trust_root,
    [
      'candidate_commit_binding',
      'gate_1_decision_relative_path',
      'gate_1_schema_version',
      'gate_1_consumption',
      'gate_2',
      'manifest_self_authorization'
    ],
    'trust_root'
  );
  exactValue(
    plan.trust_root,
    {
      candidate_commit_binding: 'JENN_GATE_1_DECISION',
      gate_1_decision_relative_path:
        'control-plane/registry/decisions/2026-07-25-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate1-decision-v0.3.json',
      gate_1_schema_version:
        'agents-os.phase5d.minimum-exact-host-smoke-gate1-decision.v0.3',
      gate_1_consumption: 'ONE_TIME',
      gate_2:
        'JENN_MAINLINE_MERGE_AFTER_SUCCESS_RECEIPT_AND_INDEPENDENT_CLOSEOUT',
      manifest_self_authorization: false
    },
    'trust_root'
  );

  exactKeys(
    plan.sealed_host,
    [
      'repository_root',
      'commit',
      'tree',
      'plugin_manager_path',
      'plugin_manager_blob_oid',
      'plugin_manager_sha256',
      'source_transport',
      'git_operation_sequence'
    ],
    'sealed_host'
  );
  exactValue(
    plan.sealed_host,
    {
      repository_root: '/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox',
      commit: '555b3b538f6eb736e530c2912de678c5941f9985',
      tree: 'fd82d403e79f36f749eb7f555b4736eae3eacdff',
      plugin_manager_path: 'Plugin.js',
      plugin_manager_blob_oid: '5fd77cea37c30ef432f23d9627d05aba862b9744',
      plugin_manager_sha256:
        'be15f76324b73400fe70052e6f07a0254b2a9c26393009ad1f026793fb36f5a2',
      source_transport: 'GIT_CAT_FILE_BLOB_TO_MEMORY_ONLY',
      git_operation_sequence: GIT_OPERATION_SEQUENCE
    },
    'sealed_host'
  );

  exactKeys(
    plan.isolation,
    [
      'security_boundary',
      'vm_role',
      'bwrap_path',
      'bwrap_sha256',
      'node_path',
      'node_sha256',
      'sandbox_runner_path',
      'sandbox_work_path',
      'network',
      'process_namespace',
      'harness_bwrap_invocation_count_per_smoke',
      'worker_stdio_transport',
      'network_seccomp',
      'filesystem_projection',
      'node_permission_flags',
      'environment',
      'vm_code_generation'
    ],
    'isolation'
  );
  exactValue(
    plan.isolation,
    {
      security_boundary:
        'BWRAP_NAMESPACES_PLUS_SECCOMP_NETWORK_DENY_PLUS_NODE_PERMISSION_MODEL',
      vm_role: 'ADAPTER_ONLY_NOT_SECURITY_BOUNDARY',
      bwrap_path: '/usr/bin/bwrap',
      bwrap_sha256:
        '52231e1caf55bcbc667b269f49c63599a6f7db4767ae6a039580d0ff853db712',
      node_path: '/home/jenn/.nvm/versions/node/v22.23.1/bin/node',
      node_sha256:
        '93956de2e59480474a7b46571da1651180b1a050cdf32641ebec4ce6e478e068',
      sandbox_runner_path: '/candidate/one-shot-host-smoke.mjs',
      sandbox_work_path: '/work',
      network: 'SHARED_NAMESPACE_WITH_ALL_NETWORK_SOCKET_SYSCALLS_DENIED',
      process_namespace: 'UNSHARED',
      harness_bwrap_invocation_count_per_smoke: 1,
      worker_stdio_transport:
        'UNLINKED_REGULAR_FILE_FDS_WITH_CANONICAL_REQUEST_RESPONSE',
      network_seccomp: {
        architecture: 'X86_64',
        action: 'ERRNO_EPERM',
        relative_path: '.agents-os-network-deny.bpf',
        byte_count: 176,
        sha256:
          '7a3c08b062d90d1f205bf458aedf4853f59350a6229a6182d5d0a0d77bd4b286',
        delegated_fd_binding:
          'OPEN_UNLINK_FSTAT_POSITIONAL_READ_SHA256_SAME_FD',
        filter_count_attestation:
          'WORKER_SECCOMP_FILTERS_EQUALS_PARENT_PLUS_ONE',
        base64:
          'IAAAAAQAAAAVAAATPgAAwCAAAAAAAAAANQAAAQAAAEAVAAAQ/////xUADgApAAAAFQANACoAAAAVAAwAKwAAABUACwAsAAAAFQAKAC0AAAAVAAkALgAAABUACAAvAAAAFQAHADAAAAAVAAYAMQAAABUABQAyAAAAFQAEADUAAAAVAAMAIAEAABUAAgArAQAAFQABADMBAAAGAAAAAAD/fwYAAAABAAUABgAAAAAAAAA=',
        denied_syscalls: [
          'socket',
          'socketpair',
          'connect',
          'bind',
          'listen',
          'accept',
          'accept4',
          'sendto',
          'sendmsg',
          'sendmmsg',
          'recvfrom',
          'recvmsg',
          'recvmmsg',
          'shutdown'
        ],
        worker_probe: 'AF_UNIX_NONEXISTENT_PATH_MUST_RETURN_EPERM',
        worker_probe_role: 'CORROBORATING_ONLY_NOT_CAUSAL_PROOF',
        packet_count: 0
      },
      filesystem_projection: [
        '/lib:READ_ONLY',
        '/lib64:READ_ONLY',
        '/node:READ_ONLY',
        '/candidate/one-shot-host-smoke.mjs:READ_ONLY',
        '/work:READ_WRITE_OWNED_QUARANTINE_ONLY',
        '/proc:PRIVATE',
        '/dev:PRIVATE',
        '/tmp:PRIVATE_TMPFS'
      ],
      node_permission_flags: [
        '--permission',
        '--allow-fs-read=/candidate',
        '--allow-fs-read=/work',
        '--allow-fs-read=/proc/self/status',
        '--allow-fs-write=/work'
      ],
      environment: {
        HOME: '/nonexistent',
        LC_ALL: 'C',
        PATH: '/usr/bin:/bin',
        PWD: '/work'
      },
      vm_code_generation: {
        strings: false,
        wasm: false
      }
    },
    'isolation'
  );

  exactKeys(
    plan.host_adapter,
    [
      'mode',
      'module_export',
      'plugin_population',
      'method_sequence',
      'require_allowlist',
      'filesystem_read_allowlist',
      'initialize_argument_projection',
      'initialize_expected_return',
      'shutdown_argument_count',
      'shutdown_expected_return'
    ],
    'host_adapter'
  );
  exactValue(plan.host_adapter.mode, 'SEALED_COMMONJS_IN_CONTROLLED_VM', 'mode');
  exactValue(plan.host_adapter.module_export, 'SINGLETON_PLUGIN_MANAGER', 'export');
  exactValue(plan.host_adapter.plugin_population, ['AGENTSOSResident'], 'population');
  exactValue(plan.host_adapter.method_sequence, METHOD_SEQUENCE, 'method_sequence');
  exactValue(plan.host_adapter.require_allowlist, REQUIRE_ALLOWLIST, 'require_allowlist');
  exactValue(
    plan.host_adapter.filesystem_read_allowlist,
    FILESYSTEM_READ_ALLOWLIST,
    'filesystem_read_allowlist'
  );
  exactValue(
    plan.host_adapter.initialize_argument_projection,
    {
      DebugMode: false,
      PORT: 'UNDEFINED',
      Key: 'UNDEFINED',
      PROJECT_BASE_PATH: null,
      dependency_keys: ['pluginManager', 'vcpLogFunctions']
    },
    'initialize_arguments'
  );
  exactValue(
    plan.host_adapter.initialize_expected_return,
    { initialized: false },
    'initialize_return'
  );
  exactValue(plan.host_adapter.shutdown_argument_count, 0, 'shutdown_arguments');
  exactValue(
    plan.host_adapter.shutdown_expected_return,
    { shutdown: true },
    'shutdown_return'
  );

  exactKeys(plan.inert_payload, ['plugin_directory', 'entrypoint', 'manifest'], 'payload');
  exactValue(
    plan.inert_payload.plugin_directory,
    'Plugin/AGENTSOSResident',
    'plugin_directory'
  );
  const entrypointBytes = decodePayload(plan.inert_payload.entrypoint, 'entrypoint');
  const manifestBytes = decodePayload(plan.inert_payload.manifest, 'manifest');
  exactValue(
    plan.inert_payload.entrypoint.relative_path,
    'Plugin/AGENTSOSResident/index.js',
    'entrypoint_path'
  );
  exactValue(
    plan.inert_payload.manifest.relative_path,
    'Plugin/AGENTSOSResident/plugin-manifest.json',
    'manifest_path'
  );
  let manifest;
  try {
    manifest = JSON.parse(manifestBytes.toString('utf8'));
  } catch {
    throw new Blocked('BLOCKED_PAYLOAD_MANIFEST', 'INVALID_JSON');
  }
  exactValue(
    {
      name: manifest.name,
      pluginType: manifest.pluginType,
      entryPoint: manifest.entryPoint,
      communication: manifest.communication,
      invocationCommands: manifest.capabilities?.invocationCommands
    },
    {
      name: 'AGENTSOSResident',
      pluginType: 'hybridservice',
      entryPoint: { script: 'index.js' },
      communication: { protocol: 'direct', timeout: 60000 },
      invocationCommands: []
    },
    'manifest_semantics'
  );

  exactKeys(
    plan.paths,
    [
      'actual_quarantine_root',
      'sandbox_inner_quarantine',
      'ownership_marker',
      'gate_1_claim_relative_path',
      'receipt_relative_path',
      'caller_selected_paths',
      'preexisting_root',
      'gate_1_claim_lifecycle'
    ],
    'paths'
  );
  exactValue(
    plan.paths,
    {
      actual_quarantine_root:
        '/tmp/agents-os-phase5d-minimum-host-smoke-v0.3-555b3b538f6e',
      sandbox_inner_quarantine: '/work/quarantine',
      ownership_marker: '.agents-os-phase5d-owner',
      gate_1_claim_relative_path:
        'control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate1-consumed-v0.3.json',
      receipt_relative_path:
        'control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3.json',
      caller_selected_paths: false,
      preexisting_root: 'BLOCKED',
      gate_1_claim_lifecycle: 'PERMANENT_ONCE_CREATED_NEVER_DELETED'
    },
    'paths'
  );

  exactKeys(
    plan.expected_observation,
    [
      'discovered_plugin_names',
      'initialize_return',
      'shutdown_return',
      'processToolCall_count',
      'native_addon_require_count',
      'child_process_spawn_count',
      'provider_or_network_count',
      'database_count',
      'private_memory_count',
      'canonical_root_modified',
      'owned_temporary_residue_count'
    ],
    'expected_observation'
  );
  exactValue(
    plan.expected_observation,
    {
      discovered_plugin_names: ['AGENTSOSResident'],
      initialize_return: { initialized: false },
      shutdown_return: { shutdown: true },
      processToolCall_count: 0,
      native_addon_require_count: 0,
      child_process_spawn_count: 0,
      provider_or_network_count: 0,
      database_count: 0,
      private_memory_count: 0,
      canonical_root_modified: false,
      owned_temporary_residue_count: 0
    },
    'expected_observation'
  );
  exactValue(plan.forbidden, FORBIDDEN, 'forbidden');

  return { entrypointBytes, manifestBytes };
}

export async function loadPlan() {
  const { value, bytes } = await readCanonicalJson(
    PLAN_PATH,
    'BLOCKED_PLAN_UNAVAILABLE'
  );
  const payload = validatePlanDocument(value);
  return { plan: value, planBytes: bytes, ...payload };
}

async function pathState(target) {
  try {
    return await lstat(target);
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
}

async function prepareQuarantine(root, plan, entrypointBytes, manifestBytes) {
  if (await pathState(root)) {
    throw new Blocked('BLOCKED_PREEXISTING_QUARANTINE_ROOT');
  }
  await mkdir(root, { mode: 0o700 });
  const markerPath = path.join(root, plan.paths.ownership_marker);
  await writeFile(markerPath, OWNER_MARKER_BYTES, { flag: 'wx', mode: 0o600 });
  const hostRoot = path.join(root, 'host');
  const pluginRoot = path.join(hostRoot, 'Plugin');
  const inertRoot = path.join(pluginRoot, 'AGENTSOSResident');
  await mkdir(hostRoot, { mode: 0o700 });
  await mkdir(pluginRoot, { mode: 0o700 });
  await mkdir(inertRoot, { mode: 0o700 });
  await writeFile(path.join(inertRoot, 'index.js'), entrypointBytes, {
    flag: 'wx',
    mode: 0o600
  });
  await writeFile(path.join(inertRoot, 'plugin-manifest.json'), manifestBytes, {
    flag: 'wx',
    mode: 0o600
  });
  return { root, markerPath, hostRoot, pluginRoot, inertRoot };
}

async function exactDirectoryNames(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  return entries
    .map((entry) => ({
      name: entry.name,
      type: entry.isDirectory()
        ? 'directory'
        : entry.isFile()
          ? 'file'
          : 'other'
    }))
    .sort((left, right) => left.name.localeCompare(right.name));
}

async function cleanupQuarantine(handle, plan) {
  if (!handle) return 'NOT_CREATED';
  try {
    if (!Buffer.from(await readFile(handle.markerPath)).equals(OWNER_MARKER_BYTES)) {
      return 'RESIDUE_UNVERIFIED';
    }
    exactValue(
      await exactDirectoryNames(handle.root),
      [
        { name: plan.paths.ownership_marker, type: 'file' },
        { name: 'host', type: 'directory' }
      ].sort((left, right) => left.name.localeCompare(right.name)),
      'root_inventory'
    );
    exactValue(
      await exactDirectoryNames(handle.hostRoot),
      [{ name: 'Plugin', type: 'directory' }],
      'host_inventory'
    );
    exactValue(
      await exactDirectoryNames(handle.pluginRoot),
      [{ name: 'AGENTSOSResident', type: 'directory' }],
      'plugin_inventory'
    );
    exactValue(
      await exactDirectoryNames(handle.inertRoot),
      [
        { name: 'index.js', type: 'file' },
        { name: 'plugin-manifest.json', type: 'file' }
      ],
      'inert_inventory'
    );
    await unlink(path.join(handle.inertRoot, 'plugin-manifest.json'));
    await unlink(path.join(handle.inertRoot, 'index.js'));
    await rmdir(handle.inertRoot);
    await rmdir(handle.pluginRoot);
    await rmdir(handle.hostRoot);
    await unlink(handle.markerPath);
    await rmdir(handle.root);
    return (await pathState(handle.root)) === null ? 'CLEAN' : 'RESIDUE_UNVERIFIED';
  } catch {
    return 'RESIDUE_UNVERIFIED';
  }
}

function inertConsole() {
  return Object.freeze({
    log() {},
    warn() {},
    error() {},
    info() {},
    debug() {}
  });
}

function evaluateInertEntrypoint(sourceBytes, filename, observations) {
  const module = { exports: {} };
  const blockedRequire = () => {
    observations.native_addon_require_count += 1;
    throw new Blocked('BLOCKED_NATIVE_OR_NAPI_REQUIRE');
  };
  const context = vm.createContext(
    {
      console: inertConsole()
    },
    {
      codeGeneration: { strings: false, wasm: false }
    }
  );
  const wrapper = new vm.Script(
    `(function (module, exports, require) {\n${sourceBytes.toString('utf8')}\n})`,
    { filename }
  ).runInContext(context, { timeout: 1000 });
  wrapper(module, module.exports, blockedRequire);
  const original = module.exports;
  if (
    original === null ||
    typeof original !== 'object' ||
    typeof original.initialize !== 'function' ||
    typeof original.shutdown !== 'function' ||
    typeof original.processToolCall !== 'function'
  ) {
    throw new Blocked('BLOCKED_INERT_ENTRYPOINT_SHAPE');
  }
  return Object.freeze({
    async initialize(config, dependencies) {
      observations.calls.push('InertPayload.initialize');
      observations.initialize_argument_projection = {
        DebugMode: config.DebugMode,
        PORT: config.PORT === undefined ? 'UNDEFINED' : config.PORT,
        Key: config.Key === undefined ? 'UNDEFINED' : config.Key,
        PROJECT_BASE_PATH: config.PROJECT_BASE_PATH,
        dependency_keys: Object.keys(dependencies).sort()
      };
      const value = await original.initialize(config, dependencies);
      observations.initialize_return = JSON.parse(JSON.stringify(value));
      return value;
    },
    async shutdown(...args) {
      observations.calls.push('InertPayload.shutdown');
      observations.shutdown_argument_count = args.length;
      const value = await original.shutdown(...args);
      observations.shutdown_return = JSON.parse(JSON.stringify(value));
      return value;
    },
    async processToolCall() {
      observations.processToolCall_count += 1;
      throw new Blocked('BLOCKED_PROCESS_TOOL_CALL');
    }
  });
}

function controlledHostRequire(
  hostRoot,
  entrypointPath,
  lifecycleModule,
  observations
) {
  function express() {
    return Object.freeze({});
  }
  express.Router = () => Object.freeze({});

  class ToolApprovalManager {
    getPrivacyProtectionConfig() {
      return { enabled: false };
    }
  }

  async function checkedPath(target) {
    if (typeof target !== 'string' && !Buffer.isBuffer(target)) {
      throw new Blocked('BLOCKED_HOST_FILESYSTEM_PATH_TYPE');
    }
    const resolved = path.resolve(String(target));
    const relative = path.relative(hostRoot, resolved).split(path.sep).join('/');
    if (
      relative.startsWith('../') ||
      path.isAbsolute(relative) ||
      !FILESYSTEM_READ_ALLOWLIST.includes(relative)
    ) {
      throw new Blocked('BLOCKED_HOST_FILESYSTEM_READ', relative);
    }
    observations.host_filesystem_read_attempts.push(relative);
    return resolved;
  }

  const confinedFs = Object.freeze({
    promises: Object.freeze({
      async readdir(target, options) {
        return nodeFs.promises.readdir(await checkedPath(target), options);
      },
      async readFile(target, options) {
        return nodeFs.promises.readFile(await checkedPath(target), options);
      }
    })
  });

  const table = new Map([
    ['fs', confinedFs],
    ['events', EventEmitter],
    ['path', path],
    [
      'child_process',
      Object.freeze({
        spawn() {
          observations.child_process_spawn_count += 1;
          throw new Blocked('BLOCKED_CHILD_PROCESS_SPAWN');
        }
      })
    ],
    [
      'node-schedule',
      Object.freeze({
        scheduleJob() {
          throw new Blocked('BLOCKED_SCHEDULED_JOB');
        }
      })
    ],
    ['dotenv', Object.freeze({ parse: () => ({}) })],
    ['./FileFetcherServer.js', Object.freeze({})],
    ['express', express],
    [
      'chokidar',
      Object.freeze({
        watch() {
          throw new Blocked('BLOCKED_FILE_WATCHER');
        }
      })
    ],
    ['./modules/captchaDecoder', Object.freeze({ getAuthCode: async () => null })],
    ['./modules/toolApprovalManager', ToolApprovalManager],
    [
      './modules/foldProtocol',
      Object.freeze({
        hasFoldMarkers: () => false,
        buildDynamicFoldObject: () => {
          throw new Blocked('BLOCKED_FOLD_RUNTIME');
        }
      })
    ],
    ['./modules/toolResultPrivacyGuard', Object.freeze({ sanitizeToolResult: (x) => x })],
    ['./modules/toolCallRecordStore', Object.freeze({})],
    [entrypointPath, lifecycleModule]
  ]);

  const controlledRequire = (specifier) => {
    if (!table.has(specifier)) {
      throw new Blocked('BLOCKED_UNDECLARED_HOST_REQUIRE', String(specifier));
    }
    observations.host_require_specifiers.push(
      specifier === entrypointPath ? 'EXACT_INERT_ENTRYPOINT' : specifier
    );
    return table.get(specifier);
  };
  controlledRequire.cache = Object.create(null);
  controlledRequire.resolve = (specifier) => {
    if (specifier === entrypointPath) return specifier;
    throw new Blocked('BLOCKED_UNDECLARED_HOST_REQUIRE_RESOLVE', String(specifier));
  };
  return controlledRequire;
}

function evaluateHostSource(sourceBytes, hostRoot, lifecycleModule, observations) {
  const module = { exports: {} };
  const entrypointPath = path.join(
    hostRoot,
    'Plugin',
    'AGENTSOSResident',
    'index.js'
  );
  const controlledRequire = controlledHostRequire(
    hostRoot,
    entrypointPath,
    lifecycleModule,
    observations
  );
  const safeProcess = Object.freeze({
    env: Object.freeze({ DebugMode: 'False' }),
    platform: 'linux',
    kill() {
      throw new Blocked('BLOCKED_PROCESS_SIGNAL');
    }
  });
  const context = vm.createContext(
    {
      clearTimeout,
      console: inertConsole(),
      process: safeProcess,
      setTimeout
    },
    {
      codeGeneration: { strings: false, wasm: false }
    }
  );
  const filename = path.join(hostRoot, 'Plugin.js');
  const wrapper = new vm.Script(
    `(function (exports, require, module, __filename, __dirname) {\n${sourceBytes.toString('utf8')}\n})`,
    { filename }
  ).runInContext(context, { timeout: 2000 });
  wrapper(module.exports, controlledRequire, module, filename, hostRoot);
  const host = module.exports;
  if (
    host === null ||
    typeof host !== 'object' ||
    typeof host.loadPlugins !== 'function' ||
    typeof host.shutdownAllPlugins !== 'function' ||
    typeof host.processToolCall !== 'function'
  ) {
    throw new Blocked('BLOCKED_HOST_EXPORT_SHAPE');
  }
  return host;
}

function blankObservations() {
  return {
    calls: [],
    host_require_specifiers: [],
    host_filesystem_read_attempts: [],
    discovered_plugin_names: [],
    initialize_argument_projection: null,
    initialize_return: null,
    shutdown_argument_count: null,
    shutdown_return: null,
    processToolCall_count: 0,
    native_addon_require_count: 0,
    child_process_spawn_count: 0,
    provider_or_network_count: 0,
    database_count: 0,
    private_memory_count: 0,
    canonical_root_modified: false
  };
}

async function executeSmoke({
  plan,
  entrypointBytes,
  manifestBytes,
  hostSourceBytes,
  quarantineRoot
}) {
  const observations = blankObservations();
  let handle = null;
  let failure = null;
  try {
    handle = await prepareQuarantine(
      quarantineRoot,
      plan,
      entrypointBytes,
      manifestBytes
    );
    const lifecycle = evaluateInertEntrypoint(
      entrypointBytes,
      path.join(handle.inertRoot, 'index.js'),
      observations
    );
    const host = evaluateHostSource(
      hostSourceBytes,
      handle.hostRoot,
      lifecycle,
      observations
    );
    observations.calls.push('PluginManager.loadPlugins');
    await host.loadPlugins();
    observations.discovered_plugin_names = [...host.plugins.keys()].sort();
    observations.calls.push('PluginManager.shutdownAllPlugins');
    await host.shutdownAllPlugins();
  } catch (error) {
    if (error instanceof Blocked) {
      failure = { code: error.code, detail: error.detail };
    } else if (error?.code === 'ERR_ACCESS_DENIED') {
      failure = {
        code: 'BLOCKED_OS_SANDBOX_ACCESS',
        detail: error.permission ?? error.name
      };
    } else if (
      error instanceof EvalError ||
      error instanceof ReferenceError ||
      error?.name === 'EvalError' ||
      error?.name === 'ReferenceError'
    ) {
      failure = {
        code: 'BLOCKED_VM_CONSTRUCTOR_ESCAPE',
        detail: error.name
      };
    } else {
      failure = { code: 'BLOCKED_UNEXPECTED_HOST_ERROR', detail: error.name };
    }
  }

  const cleanupStatus = await cleanupQuarantine(handle, plan);
  observations.calls.push('Harness.quarantineCleanup');
  if (cleanupStatus !== 'CLEAN' && cleanupStatus !== 'NOT_CREATED') {
    failure = { code: 'BLOCKED_CLEANUP_RESIDUE', detail: cleanupStatus };
  }

  if (!failure) {
    try {
      exactValue(observations.calls, METHOD_SEQUENCE, 'observed_method_sequence');
      exactValue(
        observations.discovered_plugin_names,
        plan.expected_observation.discovered_plugin_names,
        'discovered_plugin_names'
      );
      exactValue(
        observations.initialize_argument_projection,
        plan.host_adapter.initialize_argument_projection,
        'initialize_argument_projection'
      );
      exactValue(
        observations.initialize_return,
        plan.expected_observation.initialize_return,
        'initialize_return'
      );
      exactValue(
        observations.shutdown_argument_count,
        plan.host_adapter.shutdown_argument_count,
        'shutdown_argument_count'
      );
      exactValue(
        observations.shutdown_return,
        plan.expected_observation.shutdown_return,
        'shutdown_return'
      );
      for (const key of [
        'processToolCall_count',
        'native_addon_require_count',
        'child_process_spawn_count',
        'provider_or_network_count',
        'database_count',
        'private_memory_count',
        'canonical_root_modified'
      ]) {
        exactValue(observations[key], plan.expected_observation[key], key);
      }
    } catch (error) {
      failure = {
        code: error instanceof Blocked ? error.code : 'BLOCKED_OBSERVATION_MISMATCH',
        detail: error instanceof Blocked ? error.detail : error.name
      };
    }
  }

  return {
    schema_version: 'agents-os.phase5d.minimum-exact-host-smoke-result.v0.3',
    result: failure ? 'BLOCKED_CLEAN' : 'HOST_SMOKE_CANDIDATE_OBSERVED',
    failure,
    cleanup_status: cleanupStatus,
    owned_temporary_residue_count: (await pathState(quarantineRoot)) ? 1 : 0,
    observations
  };
}

function syntheticHostSource(variant = 'normal') {
  const optionalViolation =
    variant === 'unknownRequire' ? "require('undeclared-module');" : '';
  const constructorEscape =
    variant === 'bufferEscape'
      ? 'Buffer.constructor.constructor("return process")();'
      : variant === 'outerFunctionEscape'
        ? `setTimeout.constructor('return process')()
  .getBuiltinModule('fs')
  .readFileSync('/home/jenn/AGENTS_OS_Workspace/AGENTS.md');`
        : '';
  return Buffer.from(
    `'use strict';
const fs = require('fs').promises;
const EventEmitter = require('events');
const path = require('path');
${optionalViolation}
${constructorEscape}
class PluginManager extends EventEmitter {
  constructor() {
    super();
    this.plugins = new Map();
    this.serviceModules = new Map();
    this.projectBasePath = null;
  }
  getVCPLogFunctions() { return {}; }
  async loadPlugins() {
    ${variant === 'outsideRead' ? "await fs.readFile('/etc/passwd');" : ''}
    const pluginRoot = path.join(__dirname, 'Plugin');
    const names = await fs.readdir(pluginRoot);
    for (const name of names.sort()) {
      const basePath = path.join(pluginRoot, name);
      const manifest = JSON.parse(await fs.readFile(path.join(basePath, 'plugin-manifest.json'), 'utf8'));
      const plugin = require(path.join(basePath, manifest.entryPoint.script));
      manifest.basePath = basePath;
      manifest.pluginSpecificEnvConfig = {};
      this.plugins.set(manifest.name, manifest);
      this.serviceModules.set(manifest.name, { manifest, module: plugin });
      await plugin.initialize(
        { DebugMode: false, PORT: undefined, Key: undefined, PROJECT_BASE_PATH: null },
        { vcpLogFunctions: this.getVCPLogFunctions(), pluginManager: this }
      );
      ${variant === 'processToolCall' ? 'await plugin.processToolCall({});' : ''}
    }
  }
  async shutdownAllPlugins() {
    for (const value of this.serviceModules.values()) await value.module.shutdown();
  }
  async processToolCall() { throw new Error('forbidden'); }
}
module.exports = new PluginManager();
`,
    'utf8'
  );
}

async function prepareOuterSandbox(root) {
  if (await pathState(root)) {
    throw new Blocked('BLOCKED_PREEXISTING_QUARANTINE_ROOT');
  }
  await mkdir(root, { mode: 0o700 });
  try {
    await writeFile(path.join(root, OUTER_OWNER_MARKER), OUTER_OWNER_MARKER_BYTES, {
      flag: 'wx',
      mode: 0o600
    });
  } catch (error) {
    try {
      await rmdir(root);
    } catch {
      // The unexpected residue is intentionally preserved for inspection.
    }
    throw error;
  }
}

async function cleanupOuterSandbox(root) {
  try {
    const metadata = await lstat(root);
    if (!metadata.isDirectory() || (await realpath(root)) !== path.resolve(root)) {
      return 'RESIDUE_UNVERIFIED';
    }
    const markerPath = path.join(root, OUTER_OWNER_MARKER);
    if (
      !Buffer.from(await readFile(markerPath)).equals(OUTER_OWNER_MARKER_BYTES)
    ) {
      return 'RESIDUE_UNVERIFIED';
    }
    exactValue(
      await exactDirectoryNames(root),
      [{ name: OUTER_OWNER_MARKER, type: 'file' }],
      'outer_sandbox_inventory'
    );
    await unlink(markerPath);
    await rmdir(root);
    return (await pathState(root)) === null ? 'CLEAN' : 'RESIDUE_UNVERIFIED';
  } catch {
    return 'RESIDUE_UNVERIFIED';
  }
}

function networkSeccompBytes(plan) {
  const profile = plan.isolation.network_seccomp;
  const bytes = Buffer.from(profile.base64, 'base64');
  if (
    bytes.length !== profile.byte_count ||
    bytes.toString('base64') !== profile.base64 ||
    sha256(bytes) !== profile.sha256
  ) {
    throw new Blocked('BLOCKED_NETWORK_SECCOMP_BINDING');
  }
  return bytes;
}

export async function attestNetworkSeccompHandle(handle, plan) {
  const expectedBytes = networkSeccompBytes(plan);
  const { bytes, metadata } = await readOpenedRegularFile(handle, {
    code: 'BLOCKED_NETWORK_SECCOMP_FD_BINDING',
    maxBytes: plan.isolation.network_seccomp.byte_count,
    exactBytes: plan.isolation.network_seccomp.byte_count
  });
  if (
    (metadata.mode & 0o777n) !== 0o600n ||
    !bytes.equals(expectedBytes) ||
    sha256(bytes) !== plan.isolation.network_seccomp.sha256
  ) {
    throw new Blocked(
      'BLOCKED_NETWORK_SECCOMP_FD_BINDING',
      'DELEGATED_FD_CONTENT'
    );
  }
  return {
    byte_count: bytes.length,
    sha256: sha256(bytes),
    identity: openedFileIdentity(metadata)
  };
}

async function materializeNetworkSeccomp(root, plan) {
  const filePath = path.join(
    root,
    plan.isolation.network_seccomp.relative_path
  );
  const bytes = networkSeccompBytes(plan);
  await writeFile(filePath, bytes, { flag: 'wx', mode: 0o600 });
  const handle = await nodeFs.promises.open(
    filePath,
    nodeFs.constants.O_RDONLY | nodeFs.constants.O_NOFOLLOW
  );
  try {
    await unlink(filePath);
    const attestation = await attestNetworkSeccompHandle(handle, plan);
    return { filePath, handle, attestation };
  } catch (error) {
    try {
      await handle.close();
    } catch {
      // The original fail-closed error remains authoritative.
    }
    throw error;
  }
}

async function cleanupNetworkSeccomp(materialized) {
  if (!materialized) return 'NOT_CREATED';
  try {
    const closeStatus = await closeHandle(materialized);
    return closeStatus === 'CLEAN' &&
      (await pathState(materialized.filePath)) === null
      ? 'CLEAN'
      : 'RESIDUE_UNVERIFIED';
  } catch {
    return 'RESIDUE_UNVERIFIED';
  }
}

async function verifyIsolationExecutables(plan) {
  exactValue(process.arch, 'x64', 'network_seccomp_architecture');
  await requireRegularNoFollow(
    plan.isolation.bwrap_path,
    'BLOCKED_BWRAP_UNAVAILABLE'
  );
  await requireRegularNoFollow(
    plan.isolation.node_path,
    'BLOCKED_NODE_UNAVAILABLE'
  );
  exactValue(
    await sha256File(plan.isolation.bwrap_path),
    plan.isolation.bwrap_sha256,
    'bwrap_sha256'
  );
  exactValue(
    await sha256File(plan.isolation.node_path),
    plan.isolation.node_sha256,
    'node_sha256'
  );
}

function isolatedRequest(plan, profile, hostSourceBytes, ambientSeccomp) {
  if (!ISOLATED_PROFILES.includes(profile)) {
    throw new Blocked('BLOCKED_ISOLATED_PROFILE');
  }
  if (profile === 'ACTUAL_SEALED_HOST') {
    if (
      !Buffer.isBuffer(hostSourceBytes) ||
      sha256(hostSourceBytes) !== plan.sealed_host.plugin_manager_sha256
    ) {
      throw new Blocked('BLOCKED_ACTUAL_HOST_SOURCE_BINDING');
    }
  } else if (hostSourceBytes !== null) {
    throw new Blocked('BLOCKED_SYNTHETIC_SOURCE_INJECTION');
  }
  return {
    schema_version: 'agents-os.phase5d.minimum-exact-host-smoke-worker-request.v0.3',
    request_nonce: randomUUID(),
    profile,
    plan,
    host_source_base64:
      profile === 'ACTUAL_SEALED_HOST' ? hostSourceBytes.toString('base64') : null,
    ambient_seccomp_mode: ambientSeccomp.mode,
    ambient_seccomp_filter_count: ambientSeccomp.filter_count
  };
}

async function readCanonicalStdin() {
  const chunks = [];
  let byteCount = 0;
  for await (const chunk of process.stdin) {
    byteCount += chunk.length;
    if (byteCount > 2 * 1024 * 1024) {
      throw new Blocked('BLOCKED_WORKER_REQUEST_TOO_LARGE');
    }
    chunks.push(chunk);
  }
  const bytes = Buffer.concat(chunks);
  const text = bytes.toString('utf8');
  let value;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Blocked('BLOCKED_WORKER_REQUEST_JSON');
  }
  if (canonicalJson(value) !== text) {
    throw new Blocked('BLOCKED_WORKER_REQUEST_NONCANONICAL');
  }
  return { value, bytes };
}

function validateWorkerRequest(request) {
  exactKeys(
    request,
    [
      'schema_version',
      'request_nonce',
      'profile',
      'plan',
      'host_source_base64',
      'ambient_seccomp_mode',
      'ambient_seccomp_filter_count'
    ],
    'worker_request'
  );
  exactValue(
    request.schema_version,
    'agents-os.phase5d.minimum-exact-host-smoke-worker-request.v0.3',
    'worker_schema'
  );
  if (
    typeof request.request_nonce !== 'string' ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(
      request.request_nonce
    ) ||
    ![0, 2].includes(request.ambient_seccomp_mode) ||
    !Number.isSafeInteger(request.ambient_seccomp_filter_count) ||
    request.ambient_seccomp_filter_count < 0
  ) {
    throw new Blocked('BLOCKED_WORKER_REQUEST_ATTESTATION');
  }
  validatePlanDocument(request.plan);
  if (!ISOLATED_PROFILES.includes(request.profile)) {
    throw new Blocked('BLOCKED_ISOLATED_PROFILE');
  }
  if (request.profile === 'ACTUAL_SEALED_HOST') {
    if (typeof request.host_source_base64 !== 'string') {
      throw new Blocked('BLOCKED_ACTUAL_HOST_SOURCE_BINDING');
    }
    const bytes = Buffer.from(request.host_source_base64, 'base64');
    if (
      bytes.toString('base64') !== request.host_source_base64 ||
      sha256(bytes) !== request.plan.sealed_host.plugin_manager_sha256
    ) {
      throw new Blocked('BLOCKED_ACTUAL_HOST_SOURCE_BINDING');
    }
    return bytes;
  }
  if (request.host_source_base64 !== null) {
    throw new Blocked('BLOCKED_SYNTHETIC_SOURCE_INJECTION');
  }
  const variants = {
    SYNTHETIC_NORMAL: 'normal',
    SYNTHETIC_PROCESS_TOOL_CALL: 'processToolCall',
    SYNTHETIC_UNKNOWN_REQUIRE: 'unknownRequire',
    SYNTHETIC_OUTSIDE_READ: 'outsideRead',
    SYNTHETIC_BUFFER_ESCAPE: 'bufferEscape',
    SYNTHETIC_OUTER_FUNCTION_ESCAPE: 'outerFunctionEscape'
  };
  return syntheticHostSource(variants[request.profile]);
}

async function readSeccompStatus(code) {
  let text;
  try {
    text = await readFile(PROC_SELF_STATUS_PATH, 'utf8');
  } catch (error) {
    throw new Blocked(code, error?.code ?? 'PROC_STATUS_READ_FAILED');
  }
  const modeMatches = [...text.matchAll(/^Seccomp:\s+([0-9]+)$/gm)];
  const filterMatches = [...text.matchAll(/^Seccomp_filters:\s+([0-9]+)$/gm)];
  if (modeMatches.length !== 1 || filterMatches.length !== 1) {
    throw new Blocked(code, 'PROC_STATUS_FIELDS');
  }
  const mode = Number(modeMatches[0][1]);
  const filterCount = Number(filterMatches[0][1]);
  if (
    !Number.isSafeInteger(mode) ||
    ![0, 2].includes(mode) ||
    !Number.isSafeInteger(filterCount) ||
    filterCount < 0 ||
    (mode === 0 && filterCount !== 0)
  ) {
    throw new Blocked(code, 'PROC_STATUS_VALUES');
  }
  return { mode, filter_count: filterCount };
}

async function assertIsolatedWorkerBoundary(plan) {
  exactValue(process.arch, 'x64', 'worker_architecture');
  exactValue(SCRIPT_PATH, plan.isolation.sandbox_runner_path, 'worker_script_path');
  exactValue(WORKSPACE_ROOT, '/', 'worker_workspace_root');
  await requireRegularNoFollow(
    SCRIPT_PATH,
    'BLOCKED_WORKER_SCRIPT_UNAVAILABLE'
  );
  exactValue(
    {
      HOME: process.env.HOME,
      LC_ALL: process.env.LC_ALL,
      PATH: process.env.PATH,
      PWD: process.env.PWD
    },
    plan.isolation.environment,
    'worker_environment'
  );
  exactValue(
    Object.keys(process.env).sort(),
    Object.keys(plan.isolation.environment).sort(),
    'worker_environment_keys'
  );
  if (
    !process.permission ||
    process.permission.has('child_process') ||
    process.permission.has('worker_threads') ||
    process.permission.has('addons') ||
    process.permission.has(
      'fs.read',
      '/home/jenn/AGENTS_OS_Workspace/AGENTS.md'
    ) ||
    !process.permission.has('fs.read', '/candidate') ||
    !process.permission.has('fs.read', '/work') ||
    !process.permission.has('fs.read', PROC_SELF_STATUS_PATH) ||
    !process.permission.has('fs.write', '/work')
  ) {
    throw new Blocked('BLOCKED_WORKER_PERMISSION_BOUNDARY');
  }
  return await readSeccompStatus('BLOCKED_WORKER_SECCOMP_ATTESTATION');
}

async function verifyNetworkSeccomp(plan) {
  const probePath = path.join(
    plan.isolation.sandbox_work_path,
    '.agents-os-network-probe-must-not-exist.sock'
  );
  if (await pathState(probePath)) {
    throw new Blocked('BLOCKED_NETWORK_SECCOMP_PROBE_PATH');
  }
  return await new Promise((resolve, reject) => {
    let socket;
    const timeout = setTimeout(() => {
      socket?.destroy();
      reject(new Blocked('BLOCKED_NETWORK_SECCOMP_PROBE_TIMEOUT'));
    }, 1000);
    const finish = (callback) => {
      clearTimeout(timeout);
      callback();
    };
    try {
      socket = net.createConnection({ path: probePath });
    } catch (error) {
      finish(() => {
        if (error?.code === 'EPERM') {
          resolve({
            attempted_socket_syscalls: 1,
            denied_socket_syscalls: 1,
            denial_code: 'EPERM',
            packet_count: 0
          });
        } else {
          reject(
            new Blocked(
              'BLOCKED_NETWORK_SECCOMP_PROBE_RESULT',
              error?.code ?? error?.name
            )
          );
        }
      });
      return;
    }
    socket.once('connect', () => {
      socket.destroy();
      finish(() =>
        reject(new Blocked('BLOCKED_NETWORK_SECCOMP_FILTER_MISSING'))
      );
    });
    socket.once('error', (error) => {
      finish(() => {
        if (error?.code === 'EPERM') {
          resolve({
            attempted_socket_syscalls: 1,
            denied_socket_syscalls: 1,
            denial_code: 'EPERM',
            packet_count: 0
          });
        } else {
          reject(
            new Blocked(
              'BLOCKED_NETWORK_SECCOMP_PROBE_RESULT',
              error?.code ?? error?.name
            )
          );
        }
      });
    });
  });
}

async function runIsolatedWorker() {
  const { value: request, bytes: requestBytes } = await readCanonicalStdin();
  const hostSourceBytes = validateWorkerRequest(request);
  const workerSeccomp = await assertIsolatedWorkerBoundary(request.plan);
  exactValue(workerSeccomp.mode, 2, 'worker_seccomp_mode');
  exactValue(
    workerSeccomp.filter_count,
    request.ambient_seccomp_filter_count + 1,
    'worker_seccomp_filter_count'
  );
  const networkSeccompProbe = await verifyNetworkSeccomp(request.plan);
  const { entrypointBytes, manifestBytes } = validatePlanDocument(request.plan);
  const smoke = await executeSmoke({
    plan: request.plan,
    entrypointBytes,
    manifestBytes,
    hostSourceBytes,
    quarantineRoot: request.plan.paths.sandbox_inner_quarantine
  });
  return {
    ...smoke,
    mode: 'BWRAP_NAMESPACES_SECCOMP_NODE_PERMISSION_WORKER',
    profile: request.profile,
    network_seccomp_probe: networkSeccompProbe,
    worker_attestation: {
      request_nonce: request.request_nonce,
      request_sha256: sha256(requestBytes),
      ambient_seccomp_mode: request.ambient_seccomp_mode,
      ambient_seccomp_filter_count: request.ambient_seccomp_filter_count,
      worker_seccomp_mode: workerSeccomp.mode,
      worker_seccomp_filter_count: workerSeccomp.filter_count
    },
    actual_Host_smoke_executed: request.profile === 'ACTUAL_SEALED_HOST'
  };
}

async function cleanupWorkerTransport(transport) {
  if (!transport) return 'NOT_CREATED';
  const statuses = [];
  for (const entry of [transport.request, transport.output, transport.error]) {
    statuses.push(await closeHandle(entry));
  }
  return statuses.every((status) => status === 'CLEAN')
    ? 'CLEAN'
    : 'RESIDUE_UNVERIFIED';
}

async function createWorkerTransport(root, requestBytes) {
  let transport = null;
  try {
    transport = {
      request: await createUnlinkedRegularFile(
        root,
        TRANSPORT_REQUEST_NAME,
        'BLOCKED_OS_SANDBOX_TRANSPORT'
      ),
      output: null,
      error: null
    };
    await positionalWrite(
      transport.request.handle,
      requestBytes,
      'BLOCKED_OS_SANDBOX_TRANSPORT'
    );
    const requestAttestation = await readOpenedRegularFile(
      transport.request.handle,
      {
        code: 'BLOCKED_OS_SANDBOX_TRANSPORT',
        maxBytes: 2 * 1024 * 1024,
        exactBytes: requestBytes.length
      }
    );
    if (!requestAttestation.bytes.equals(requestBytes)) {
      throw new Blocked(
        'BLOCKED_OS_SANDBOX_TRANSPORT',
        'REQUEST_FD_CONTENT'
      );
    }
    transport.output = await createUnlinkedRegularFile(
      root,
      TRANSPORT_OUTPUT_NAME,
      'BLOCKED_OS_SANDBOX_TRANSPORT'
    );
    transport.error = await createUnlinkedRegularFile(
      root,
      TRANSPORT_ERROR_NAME,
      'BLOCKED_OS_SANDBOX_TRANSPORT'
    );
    return transport;
  } catch (error) {
    await cleanupWorkerTransport(transport);
    throw error;
  }
}

export async function readCanonicalWorkerOutputHandle(handle) {
  const { bytes } = await readOpenedRegularFile(handle, {
    code: 'BLOCKED_OS_SANDBOX_OUTPUT',
    minBytes: 1,
    maxBytes: MAX_WORKER_OUTPUT_BYTES
  });
  const text = bytes.toString('utf8');
  let value;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Blocked('BLOCKED_OS_SANDBOX_OUTPUT', 'INVALID_JSON');
  }
  if (
    !Buffer.from(canonicalJson(value), 'utf8').equals(bytes) ||
    !Buffer.from(text, 'utf8').equals(bytes)
  ) {
    throw new Blocked('BLOCKED_OS_SANDBOX_OUTPUT', 'NONCANONICAL_OUTPUT');
  }
  return { value, bytes };
}

function validateWorkerResult(
  parsed,
  completedStatus,
  { profile, request, requestBytes, ambientSeccomp }
) {
  exactKeys(
    parsed,
    [
      'schema_version',
      'result',
      'failure',
      'cleanup_status',
      'owned_temporary_residue_count',
      'observations',
      'mode',
      'profile',
      'network_seccomp_probe',
      'worker_attestation',
      'actual_Host_smoke_executed'
    ],
    'worker_result'
  );
  exactValue(
    {
      schema_version: parsed.schema_version,
      mode: parsed.mode,
      profile: parsed.profile,
      actual_Host_smoke_executed: parsed.actual_Host_smoke_executed
    },
    {
      schema_version: 'agents-os.phase5d.minimum-exact-host-smoke-result.v0.3',
      mode: 'BWRAP_NAMESPACES_SECCOMP_NODE_PERMISSION_WORKER',
      profile,
      actual_Host_smoke_executed: profile === 'ACTUAL_SEALED_HOST'
    },
    'worker_result_identity'
  );
  const expectedStatus =
    parsed.result === 'HOST_SMOKE_CANDIDATE_OBSERVED'
      ? 0
      : parsed.result === 'BLOCKED_CLEAN'
        ? 1
        : null;
  if (expectedStatus === null || completedStatus !== expectedStatus) {
    throw new Blocked(
      'BLOCKED_OS_SANDBOX_OUTPUT',
      'WORKER_STATUS_RESULT_MISMATCH'
    );
  }
  if (expectedStatus === 0 && parsed.failure !== null) {
    throw new Blocked('BLOCKED_OS_SANDBOX_OUTPUT', 'SUCCESS_WITH_FAILURE');
  }
  if (expectedStatus === 1) {
    exactKeys(parsed.failure, ['code', 'detail'], 'worker_failure');
  }
  exactValue(
    parsed.worker_attestation,
    {
      request_nonce: request.request_nonce,
      request_sha256: sha256(requestBytes),
      ambient_seccomp_mode: ambientSeccomp.mode,
      ambient_seccomp_filter_count: ambientSeccomp.filter_count,
      worker_seccomp_mode: 2,
      worker_seccomp_filter_count: ambientSeccomp.filter_count + 1
    },
    'worker_attestation'
  );
  exactValue(
    parsed.network_seccomp_probe,
    {
      attempted_socket_syscalls: 1,
      denied_socket_syscalls: 1,
      denial_code: 'EPERM',
      packet_count: 0
    },
    'network_seccomp_probe'
  );
}

export function validateSpawnCompletion(completed) {
  if (
    completed?.error ||
    ![0, 1].includes(completed?.status) ||
    completed?.signal !== null
  ) {
    throw new Blocked('BLOCKED_OS_SANDBOX_EXECUTION', {
      error_code: completed?.error?.code ?? null,
      status: completed?.status ?? null,
      signal: completed?.signal ?? null
    });
  }
}

async function runIsolatedSmoke(plan, profile, hostSourceBytes, outerRoot) {
  await verifyIsolationExecutables(plan);
  await prepareOuterSandbox(outerRoot);
  let networkSeccomp = null;
  let transport = null;
  let completed;
  let parsed;
  try {
    const ambientSeccomp = await readSeccompStatus(
      'BLOCKED_AMBIENT_SECCOMP_ATTESTATION'
    );
    networkSeccomp = await materializeNetworkSeccomp(outerRoot, plan);
    const request = isolatedRequest(
      plan,
      profile,
      hostSourceBytes,
      ambientSeccomp
    );
    const requestBytes = Buffer.from(canonicalJson(request), 'utf8');
    transport = await createWorkerTransport(outerRoot, requestBytes);
    const args = [
      '--unshare-all',
      '--share-net',
      '--die-with-parent',
      '--new-session',
      '--clearenv',
      '--setenv',
      'HOME',
      plan.isolation.environment.HOME,
      '--setenv',
      'LC_ALL',
      plan.isolation.environment.LC_ALL,
      '--setenv',
      'PATH',
      plan.isolation.environment.PATH,
      '--ro-bind',
      '/lib',
      '/lib',
      '--ro-bind',
      '/lib64',
      '/lib64',
      '--ro-bind',
      plan.isolation.node_path,
      '/node',
      '--dir',
      '/candidate',
      '--ro-bind',
      SCRIPT_PATH,
      plan.isolation.sandbox_runner_path,
      '--bind',
      outerRoot,
      plan.isolation.sandbox_work_path,
      '--proc',
      '/proc',
      '--dev',
      '/dev',
      '--tmpfs',
      '/tmp',
      '--seccomp',
      '3',
      '--chdir',
      plan.isolation.sandbox_work_path,
      '/node',
      ...plan.isolation.node_permission_flags,
      plan.isolation.sandbox_runner_path,
      '--isolated-worker'
    ];
    const preSpawnSeccompAttestation = await attestNetworkSeccompHandle(
      networkSeccomp.handle,
      plan
    );
    exactValue(
      preSpawnSeccompAttestation,
      networkSeccomp.attestation,
      'network_seccomp_fd_pre_spawn_stability'
    );
    completed = spawnSync(plan.isolation.bwrap_path, args, {
      cwd: WORKSPACE_ROOT,
      env: {
        HOME: '/nonexistent',
        LC_ALL: 'C',
        PATH: '/usr/bin:/bin'
      },
      stdio: [
        transport.request.handle.fd,
        transport.output.handle.fd,
        transport.error.handle.fd,
        networkSeccomp.handle.fd
      ]
    });
    validateSpawnCompletion(completed);
    await readOpenedRegularFile(transport.error.handle, {
      code: 'BLOCKED_OS_SANDBOX_EXECUTION',
      maxBytes: 0,
      exactBytes: 0
    });
    ({ value: parsed } = await readCanonicalWorkerOutputHandle(
      transport.output.handle
    ));
    validateWorkerResult(parsed, completed.status, {
      profile,
      request,
      requestBytes,
      ambientSeccomp
    });
    const postSpawnSeccompAttestation = await attestNetworkSeccompHandle(
      networkSeccomp.handle,
      plan
    );
    exactValue(
      postSpawnSeccompAttestation,
      preSpawnSeccompAttestation,
      'network_seccomp_fd_stability'
    );
    parsed.network_seccomp_attestation = {
      delegated_fd_byte_count: preSpawnSeccompAttestation.byte_count,
      delegated_fd_sha256: preSpawnSeccompAttestation.sha256,
      ambient_seccomp_mode: ambientSeccomp.mode,
      ambient_seccomp_filter_count: ambientSeccomp.filter_count,
      worker_seccomp_mode: parsed.worker_attestation.worker_seccomp_mode,
      worker_seccomp_filter_count:
        parsed.worker_attestation.worker_seccomp_filter_count,
      filter_count_increment:
        parsed.worker_attestation.worker_seccomp_filter_count -
        ambientSeccomp.filter_count,
      probe_role: plan.isolation.network_seccomp.worker_probe_role
    };
  } finally {
    const transportCleanup = await cleanupWorkerTransport(transport);
    const seccompCleanup = await cleanupNetworkSeccomp(networkSeccomp);
    const outerCleanup = await cleanupOuterSandbox(outerRoot);
    if (
      !['CLEAN', 'NOT_CREATED'].includes(transportCleanup) ||
      !['CLEAN', 'NOT_CREATED'].includes(seccompCleanup) ||
      outerCleanup !== 'CLEAN'
    ) {
      throw new Blocked('BLOCKED_OUTER_SANDBOX_RESIDUE', {
        transport_cleanup: transportCleanup,
        seccomp_cleanup: seccompCleanup,
        outer_cleanup: outerCleanup
      });
    }
  }
  return {
    ...parsed,
    outer_sandbox_cleanup_status: 'CLEAN',
    owned_temporary_residue_count: 0,
    harness_bwrap_invocation_count: 1,
    sandbox_network: 'SECCOMP_ALL_NETWORK_SOCKET_SYSCALLS_DENIED',
    spawn_wrapper_error_code: null,
    OS_security_boundary: plan.isolation.security_boundary,
    vm_security_boundary: false
  };
}

export async function runSyntheticDryRun(variant = 'normal') {
  const { plan } = await loadPlan();
  const profileMap = {
    normal: 'SYNTHETIC_NORMAL',
    processToolCall: 'SYNTHETIC_PROCESS_TOOL_CALL',
    unknownRequire: 'SYNTHETIC_UNKNOWN_REQUIRE',
    outsideRead: 'SYNTHETIC_OUTSIDE_READ',
    bufferEscape: 'SYNTHETIC_BUFFER_ESCAPE',
    outerFunctionEscape: 'SYNTHETIC_OUTER_FUNCTION_ESCAPE'
  };
  if (!Object.hasOwn(profileMap, variant)) {
    throw new Blocked('BLOCKED_SYNTHETIC_VARIANT');
  }
  const outerRoot = path.join(
    '/tmp',
    `agents-os-phase5d-minimum-host-smoke-dry-${process.pid}-${randomUUID()}`
  );
  const result = await runIsolatedSmoke(
    plan,
    profileMap[variant],
    null,
    outerRoot
  );
  return {
    ...result,
    mode: 'HERMETIC_DRY_RUN',
    VCPToolBox_Git_command_count: 0,
    Host_source: 'SYNTHETIC_TEST_ONLY',
    actual_Host_smoke_executed: false
  };
}

function gitEnvironment() {
  return {
    PATH: process.env.PATH ?? '/usr/bin:/bin',
    HOME: '/nonexistent',
    LC_ALL: 'C',
    GIT_CONFIG_NOSYSTEM: '1',
    GIT_NO_REPLACE_OBJECTS: '1',
    GIT_OPTIONAL_LOCKS: '0'
  };
}

function gitRead(args, encoding = 'utf8') {
  const completed = spawnSync('git', args, {
    cwd: WORKSPACE_ROOT,
    env: gitEnvironment(),
    encoding,
    input: null,
    maxBuffer: 4 * 1024 * 1024,
    stdio: ['ignore', 'pipe', 'ignore']
  });
  if (completed.error || completed.status !== 0) {
    throw new Blocked('BLOCKED_SEALED_GIT_OBJECT_UNAVAILABLE');
  }
  return completed.stdout;
}

function readSealedHostSource(plan) {
  const gitDir = path.join(plan.sealed_host.repository_root, '.git');
  const commandIds = [];
  const empty = gitRead([
    `--git-dir=${gitDir}`,
    'cat-file',
    '-e',
    `${plan.sealed_host.commit}^{commit}`
  ]);
  commandIds.push('SEALED_COMMIT_EXISTS');
  if (empty !== '') throw new Blocked('BLOCKED_SEALED_COMMIT_OUTPUT');

  const tree = gitRead([
    `--git-dir=${gitDir}`,
    'rev-parse',
    `${plan.sealed_host.commit}^{tree}`
  ]).trim();
  commandIds.push('SEALED_TREE_RESOLVE');
  exactValue(tree, plan.sealed_host.tree, 'sealed_tree');

  const blob = gitRead([
    `--git-dir=${gitDir}`,
    'rev-parse',
    `${plan.sealed_host.commit}:${plan.sealed_host.plugin_manager_path}`
  ]).trim();
  commandIds.push('PLUGIN_MANAGER_BLOB_RESOLVE');
  exactValue(blob, plan.sealed_host.plugin_manager_blob_oid, 'plugin_manager_blob');

  const bytes = gitRead(
    [
      `--git-dir=${gitDir}`,
      'cat-file',
      'blob',
      plan.sealed_host.plugin_manager_blob_oid
    ],
    null
  );
  commandIds.push('PLUGIN_MANAGER_BLOB_READ');
  exactValue(commandIds, GIT_OPERATION_SEQUENCE, 'git_operation_sequence');
  exactValue(sha256(bytes), plan.sealed_host.plugin_manager_sha256, 'host_source_sha256');
  return { bytes, commandIds };
}

export function validateGateDecision(decision, plan) {
  exactKeys(
    decision,
    [
      'schema_version',
      'decision_id',
      'owner',
      'candidate_commit',
      'plan_sha256',
      'runner_sha256',
      'tests_sha256',
      'independent_review_relative_path',
      'independent_review_sha256',
      'independent_review_result',
      'quarantine_root',
      'gate_1_claim_relative_path',
      'receipt_relative_path',
      'sealed_host_commit',
      'sealed_host_tree',
      'sealed_host_blob_oid',
      'allowed_method_sequence',
      'actual_host_smoke_authorized',
      'authorized_once'
    ],
    'gate_1_decision'
  );
  exactValue(
    {
      schema_version: decision.schema_version,
      owner: decision.owner,
      independent_review_result: decision.independent_review_result,
      quarantine_root: decision.quarantine_root,
      gate_1_claim_relative_path: decision.gate_1_claim_relative_path,
      receipt_relative_path: decision.receipt_relative_path,
      sealed_host_commit: decision.sealed_host_commit,
      sealed_host_tree: decision.sealed_host_tree,
      sealed_host_blob_oid: decision.sealed_host_blob_oid,
      allowed_method_sequence: decision.allowed_method_sequence,
      actual_host_smoke_authorized: decision.actual_host_smoke_authorized,
      authorized_once: decision.authorized_once
    },
    {
      schema_version: plan.trust_root.gate_1_schema_version,
      owner: 'Jenn',
      independent_review_result: 'PASS_NO_BLOCKER',
      quarantine_root: plan.paths.actual_quarantine_root,
      gate_1_claim_relative_path: plan.paths.gate_1_claim_relative_path,
      receipt_relative_path: plan.paths.receipt_relative_path,
      sealed_host_commit: plan.sealed_host.commit,
      sealed_host_tree: plan.sealed_host.tree,
      sealed_host_blob_oid: plan.sealed_host.plugin_manager_blob_oid,
      allowed_method_sequence: METHOD_SEQUENCE,
      actual_host_smoke_authorized: true,
      authorized_once: true
    },
    'gate_1_binding'
  );
  if (
    typeof decision.decision_id !== 'string' ||
    !decision.decision_id.startsWith('JENN_') ||
    !/^[0-9a-f]{40}$/.test(decision.candidate_commit) ||
    !/^[0-9a-f]{64}$/.test(decision.plan_sha256) ||
    !/^[0-9a-f]{64}$/.test(decision.runner_sha256) ||
    !/^[0-9a-f]{64}$/.test(decision.tests_sha256) ||
    !safeWorkspaceRelative(
      decision.independent_review_relative_path,
      'control-plane/registry/reviews/'
    ) ||
    !/^[0-9a-f]{64}$/.test(decision.independent_review_sha256)
  ) {
    throw new Blocked('BLOCKED_GATE_1_SCHEMA');
  }
}

async function requireGateDecision(plan, planBytes) {
  const decisionPath = path.join(
    WORKSPACE_ROOT,
    plan.trust_root.gate_1_decision_relative_path
  );
  const { value: decision, bytes: decisionBytes } = await readCanonicalJson(
    decisionPath,
    'BLOCKED_MISSING_GATE_1_DECISION'
  );
  validateGateDecision(decision, plan);

  const artifactHashes = {
    plan_sha256: sha256(planBytes),
    runner_sha256: await sha256File(SCRIPT_PATH),
    tests_sha256: await sha256File(TEST_PATH)
  };
  exactValue(
    {
      plan_sha256: decision.plan_sha256,
      runner_sha256: decision.runner_sha256,
      tests_sha256: decision.tests_sha256
    },
    artifactHashes,
    'gate_1_artifact_hashes'
  );

  const reviewPath = path.join(
    WORKSPACE_ROOT,
    decision.independent_review_relative_path
  );
  await requireRegularNoFollow(
    reviewPath,
    'BLOCKED_INDEPENDENT_REVIEW_UNAVAILABLE'
  );
  exactValue(
    await sha256File(reviewPath),
    decision.independent_review_sha256,
    'independent_review_sha256'
  );
  const candidateCommit = gitRead(['-C', WORKSPACE_ROOT, 'rev-parse', 'HEAD']).trim();
  exactValue(candidateCommit, decision.candidate_commit, 'candidate_commit');

  const claimPath = path.join(
    WORKSPACE_ROOT,
    plan.paths.gate_1_claim_relative_path
  );
  if (await pathState(claimPath)) {
    throw new Blocked('BLOCKED_GATE_1_ALREADY_CONSUMED');
  }
  const receiptPath = path.join(WORKSPACE_ROOT, plan.paths.receipt_relative_path);
  if (await pathState(receiptPath)) {
    throw new Blocked('BLOCKED_GATE_1_ALREADY_CONSUMED');
  }
  if (await pathState(plan.paths.actual_quarantine_root)) {
    throw new Blocked('BLOCKED_PREEXISTING_QUARANTINE_ROOT');
  }
  return {
    decision,
    decision_sha256: sha256(decisionBytes),
    candidateCommit,
    artifactHashes,
    claimPath,
    receiptPath
  };
}

export async function createExclusiveClaim({
  claimPath,
  allowedDirectory,
  bytes
}) {
  if (
    typeof claimPath !== 'string' ||
    typeof allowedDirectory !== 'string' ||
    !Buffer.isBuffer(bytes) ||
    bytes.length === 0
  ) {
    throw new Blocked('BLOCKED_CLAIM_SCHEMA');
  }
  const directoryMetadata = await lstat(allowedDirectory);
  const canonicalDirectory = await realpath(allowedDirectory);
  if (
    !directoryMetadata.isDirectory() ||
    canonicalDirectory !== path.resolve(allowedDirectory) ||
    path.dirname(path.resolve(claimPath)) !== canonicalDirectory
  ) {
    throw new Blocked('BLOCKED_CLAIM_PATH');
  }
  let handle;
  let directoryHandle;
  try {
    handle = await nodeFs.promises.open(
      claimPath,
      nodeFs.constants.O_WRONLY |
        nodeFs.constants.O_CREAT |
        nodeFs.constants.O_EXCL |
        nodeFs.constants.O_NOFOLLOW,
      0o600
    );
    await handle.writeFile(bytes);
    await handle.sync();
    await handle.close();
    handle = null;
    directoryHandle = await nodeFs.promises.open(
      allowedDirectory,
      nodeFs.constants.O_RDONLY |
        nodeFs.constants.O_DIRECTORY |
        nodeFs.constants.O_NOFOLLOW
    );
    await directoryHandle.sync();
  } catch (error) {
    throw new Blocked(
      error?.code === 'EEXIST'
        ? 'BLOCKED_GATE_1_ALREADY_CONSUMED'
        : 'BLOCKED_GATE_1_CLAIM_WRITE',
      error?.code ?? error?.name
    );
  } finally {
    if (handle) {
      await handle.close();
    }
    if (directoryHandle) {
      await directoryHandle.close();
    }
  }
}

async function consumeGateOnce(gate, plan) {
  const claim = {
    schema_version:
      'agents-os.phase5d.minimum-exact-host-smoke-gate1-claim.v0.3',
    decision_sha256: gate.decision_sha256,
    candidate_commit: gate.candidateCommit,
    state: 'CONSUMED_PENDING',
    retry_authorized: false,
    terminal_receipt_relative_path: plan.paths.receipt_relative_path
  };
  const receiptsDirectory = path.dirname(gate.claimPath);
  await createExclusiveClaim({
    claimPath: gate.claimPath,
    allowedDirectory: receiptsDirectory,
    bytes: Buffer.from(canonicalJson(claim), 'utf8')
  });
  return claim;
}

async function writeReceipt(gate, plan, smoke, hostGitCommandIds) {
  const receipt = {
    schema_version: 'agents-os.phase5d.minimum-exact-host-smoke-receipt.v0.3',
    decision_sha256: gate.decision_sha256,
    candidate_commit: gate.candidateCommit,
    artifact_hashes: gate.artifactHashes,
    sealed_host: {
      commit: plan.sealed_host.commit,
      tree: plan.sealed_host.tree,
      plugin_manager_blob_oid: plan.sealed_host.plugin_manager_blob_oid,
      plugin_manager_sha256: plan.sealed_host.plugin_manager_sha256
    },
    VCPToolBox_Git_command_ids: hostGitCommandIds,
    result: smoke.result,
    failure: smoke.failure,
    cleanup_status: smoke.cleanup_status,
    owned_temporary_residue_count: smoke.owned_temporary_residue_count,
    observations: smoke.observations,
    isolation_observation: {
      security_boundary: smoke.OS_security_boundary ?? null,
      vm_security_boundary: smoke.vm_security_boundary ?? null,
      sandbox_network: smoke.sandbox_network ?? 'NOT_STARTED',
      harness_bwrap_invocation_count:
        smoke.harness_bwrap_invocation_count ?? 0,
      network_seccomp_probe: smoke.network_seccomp_probe ?? null,
      spawn_wrapper_error_code: smoke.spawn_wrapper_error_code ?? null
    },
    gate_1_claim_relative_path: plan.paths.gate_1_claim_relative_path,
    Gate_1_consumed: true,
    Gate_2_mainline_merge_authorized: false
  };
  await writeFile(gate.receiptPath, canonicalJson(receipt), {
    flag: 'wx',
    mode: 0o600
  });
  return receipt;
}

async function runActual() {
  const { plan, planBytes } = await loadPlan();
  const gate = await requireGateDecision(plan, planBytes);
  await consumeGateOnce(gate, plan);
  await verifyIsolationExecutables(plan);
  let commandIds = [];
  let smoke;
  try {
    const source = readSealedHostSource(plan);
    commandIds = source.commandIds;
    smoke = await runIsolatedSmoke(
      plan,
      'ACTUAL_SEALED_HOST',
      source.bytes,
      plan.paths.actual_quarantine_root
    );
  } catch (error) {
    const residue = (await pathState(plan.paths.actual_quarantine_root)) ? 1 : 0;
    smoke = {
      schema_version: 'agents-os.phase5d.minimum-exact-host-smoke-result.v0.3',
      result: 'BLOCKED_CLEAN',
      failure: {
        code: error instanceof Blocked ? error.code : 'BLOCKED_UNEXPECTED',
        detail: error instanceof Blocked ? error.detail : error.name
      },
      cleanup_status: residue === 0 ? 'CLEAN' : 'RESIDUE_UNVERIFIED',
      owned_temporary_residue_count: residue,
      observations: blankObservations(),
      actual_Host_smoke_executed: false
    };
  }
  const receipt = await writeReceipt(gate, plan, smoke, commandIds);
  return {
    result: receipt.result,
    cleanup_status: receipt.cleanup_status,
    receipt_relative_path: plan.paths.receipt_relative_path,
    Gate_1_consumed: true,
    Gate_2_mainline_merge_authorized: false
  };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 1 && args[0] === '--isolated-worker') {
    try {
      const result = await runIsolatedWorker();
      process.stdout.write(canonicalJson(result));
      return result.result === 'HOST_SMOKE_CANDIDATE_OBSERVED' ? 0 : 1;
    } catch (error) {
      process.stdout.write(
        canonicalJson({
          result: 'BLOCKED',
          failure: {
            code: error instanceof Blocked ? error.code : 'BLOCKED_UNEXPECTED',
            detail: error instanceof Blocked ? error.detail : error.name
          },
          actual_Host_smoke_executed: false
        })
      );
      return 1;
    }
  }
  if (args.length !== 1 || !['--dry-run', '--actual'].includes(args[0])) {
    process.stdout.write(
      `${canonicalJson({
        result: 'BLOCKED_USAGE',
        allowed_modes: ['--dry-run', '--actual']
      })}`
    );
    return 2;
  }
  try {
    const result =
      args[0] === '--dry-run' ? await runSyntheticDryRun() : await runActual();
    process.stdout.write(canonicalJson(result));
    return result.result === 'HOST_SMOKE_CANDIDATE_OBSERVED' ? 0 : 1;
  } catch (error) {
    const blocked = {
      result: 'BLOCKED',
      failure: {
        code: error instanceof Blocked ? error.code : 'BLOCKED_UNEXPECTED',
        detail: error instanceof Blocked ? error.detail : error.name
      },
      actual_Host_smoke_executed: false
    };
    process.stdout.write(canonicalJson(blocked));
    return 1;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === SCRIPT_PATH) {
  process.exitCode = await main();
}
