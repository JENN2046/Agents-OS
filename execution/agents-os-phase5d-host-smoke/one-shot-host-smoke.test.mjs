#!/usr/bin/env node

import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { constants as fsConstants } from 'node:fs';
import {
  chmod,
  lstat,
  mkdtemp,
  open,
  readFile,
  rmdir,
  unlink,
  writeFile
} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  attestNetworkSeccompHandle,
  createExclusiveClaim,
  loadPlan,
  readCanonicalWorkerOutputHandle,
  runSyntheticDryRun,
  validateGateDecision,
  validatePlanDocument,
  validateSpawnCompletion
} from './one-shot-host-smoke.mjs';

const TEST_PATH = fileURLToPath(import.meta.url);
const RUNNER_URL = new URL('./one-shot-host-smoke.mjs', import.meta.url).href;
const WORKSPACE_ROOT = path.resolve(path.dirname(TEST_PATH), '../..');
const PLAN = path.join(
  WORKSPACE_ROOT,
  'control-plane/registry/drafts/2026-07-25-agents-os-phase-5d-m0d-minimum-exact-host-smoke-plan-v0.3.json'
);
const ACTUAL_ROOT =
  '/tmp/agents-os-phase5d-minimum-host-smoke-v0.3-555b3b538f6e';
const CLAIM = path.join(
  WORKSPACE_ROOT,
  'control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate1-consumed-v0.3.json'
);
const RECEIPT = path.join(
  WORKSPACE_ROOT,
  'control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3.json'
);

async function absent(target) {
  try {
    await lstat(target);
    return false;
  } catch (error) {
    if (error.code === 'ENOENT') return true;
    throw error;
  }
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

async function openUnlinkedFixture(root, name, bytes, flags = fsConstants.O_RDWR) {
  const filePath = path.join(root, name);
  await writeFile(filePath, bytes, { flag: 'wx', mode: 0o600 });
  const handle = await open(filePath, flags | fsConstants.O_NOFOLLOW);
  await unlink(filePath);
  return handle;
}

function expectBlocked(label, mutate) {
  const candidate = structuredClone(plan);
  mutate(candidate);
  assert.throws(
    () => validatePlanDocument(candidate),
    (error) => error?.name === 'Blocked',
    label
  );
}

const planText = await readFile(PLAN, 'utf8');
const plan = JSON.parse(planText);
assert.equal(`${JSON.stringify(plan, null, 2)}\n`, planText);
validatePlanDocument(plan);
const sealedSeccompBytes = Buffer.from(
  plan.isolation.network_seccomp.base64,
  'base64'
);
assert.equal(sealedSeccompBytes.length, 176);
assert.equal(sha256(sealedSeccompBytes), plan.isolation.network_seccomp.sha256);
const seccompInstructions = [];
for (let offset = 0; offset < sealedSeccompBytes.length; offset += 8) {
  seccompInstructions.push({
    code: sealedSeccompBytes.readUInt16LE(offset),
    jt: sealedSeccompBytes.readUInt8(offset + 2),
    jf: sealedSeccompBytes.readUInt8(offset + 3),
    k: sealedSeccompBytes.readUInt32LE(offset + 4)
  });
}
assert.equal(seccompInstructions.length, 22);
assert.deepEqual(
  seccompInstructions.slice(5, 19).map((instruction) => instruction.k),
  [41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 53, 288, 299, 307]
);
assert.deepEqual(plan.isolation.network_seccomp.denied_syscalls, [
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
]);
assert.deepEqual(
  seccompInstructions.slice(19).map((instruction) => [
    instruction.code,
    instruction.k
  ]),
  [
    [0x06, 0x7fff0000],
    [0x06, 0x00050001],
    [0x06, 0x00000000]
  ]
);

expectBlocked('unknown root field', (item) => {
  item.extra = false;
});
expectBlocked('execution authority elevation', (item) => {
  item.execution_authorized = true;
});
expectBlocked('network seccomp boundary weakening', (item) => {
  item.isolation.network = 'SHARED';
});
expectBlocked('changed network seccomp BPF', (item) => {
  item.isolation.network_seccomp.base64 =
    `A${item.isolation.network_seccomp.base64.slice(1)}`;
});
expectBlocked('deleted network seccomp profile', (item) => {
  delete item.isolation.network_seccomp;
});
expectBlocked('ordinary replacement network seccomp profile', (item) => {
  item.isolation.network_seccomp = {};
});
expectBlocked('changed network seccomp architecture', (item) => {
  item.isolation.network_seccomp.architecture = 'AARCH64';
});
expectBlocked('changed network seccomp action', (item) => {
  item.isolation.network_seccomp.action = 'KILL_PROCESS';
});
expectBlocked('coherent allow-all seccomp replacement', (item) => {
  const allowAll = Buffer.from([0x06, 0, 0, 0, 0, 0, 0xff, 0x7f]);
  item.isolation.network_seccomp.action = 'ALLOW';
  item.isolation.network_seccomp.byte_count = allowAll.length;
  item.isolation.network_seccomp.sha256 = sha256(allowAll);
  item.isolation.network_seccomp.base64 = allowAll.toString('base64');
  item.isolation.network_seccomp.denied_syscalls = [];
});
expectBlocked('coherent seccomp syscall drop', (item) => {
  const weakened = Buffer.from(item.isolation.network_seccomp.base64, 'base64');
  let changed = false;
  for (let offset = 0; offset < weakened.length; offset += 8) {
    if (
      weakened.readUInt16LE(offset) === 0x15 &&
      weakened.readUInt32LE(offset + 4) === 48
    ) {
      weakened.writeUInt32LE(39, offset + 4);
      changed = true;
      break;
    }
  }
  assert.equal(changed, true);
  item.isolation.network_seccomp.sha256 = sha256(weakened);
  item.isolation.network_seccomp.base64 = weakened.toString('base64');
  item.isolation.network_seccomp.denied_syscalls =
    item.isolation.network_seccomp.denied_syscalls.filter(
      (name) => name !== 'shutdown'
    );
});
expectBlocked('changed network seccomp worker probe', (item) => {
  item.isolation.network_seccomp.worker_probe = 'EPERM_ONLY';
});
expectBlocked('promoted network seccomp probe to causal proof', (item) => {
  item.isolation.network_seccomp.worker_probe_role = 'CAUSAL_PROOF';
});
expectBlocked('changed network seccomp packet invariant', (item) => {
  item.isolation.network_seccomp.packet_count = 1;
});
expectBlocked('weakened delegated FD binding', (item) => {
  item.isolation.network_seccomp.delegated_fd_binding =
    'PATHNAME_HASH_BEFORE_OPEN';
});
expectBlocked('removed filter count attestation', (item) => {
  item.isolation.network_seccomp.filter_count_attestation = 'NONE';
});
expectBlocked('changed worker stdio transport', (item) => {
  item.isolation.worker_stdio_transport = 'PIPE';
});
expectBlocked('changed sealed Host blob', (item) => {
  item.sealed_host.plugin_manager_blob_oid = 'a'.repeat(40);
});
expectBlocked('extra Host method', (item) => {
  item.host_adapter.method_sequence.push('PluginManager.processToolCall');
});
expectBlocked('reordered Host requires', (item) => {
  item.host_adapter.require_allowlist.reverse();
});
expectBlocked('caller-selected root', (item) => {
  item.paths.caller_selected_paths = true;
});
expectBlocked('payload mutation', (item) => {
  item.inert_payload.entrypoint.base64 =
    `A${item.inert_payload.entrypoint.base64.slice(1)}`;
});
expectBlocked('enabled effect count', (item) => {
  item.expected_observation.processToolCall_count = 1;
});

const dryRun = await runSyntheticDryRun();
assert.equal(dryRun.result, 'HOST_SMOKE_CANDIDATE_OBSERVED');
assert.equal(dryRun.cleanup_status, 'CLEAN');
assert.equal(dryRun.owned_temporary_residue_count, 0);
assert.equal(dryRun.VCPToolBox_Git_command_count, 0);
assert.equal(dryRun.actual_Host_smoke_executed, false);
assert.equal(
  dryRun.OS_security_boundary,
  'BWRAP_NAMESPACES_PLUS_SECCOMP_NETWORK_DENY_PLUS_NODE_PERMISSION_MODEL'
);
assert.equal(dryRun.vm_security_boundary, false);
assert.equal(dryRun.outer_sandbox_cleanup_status, 'CLEAN');
assert.equal(dryRun.harness_bwrap_invocation_count, 1);
assert.equal(
  dryRun.sandbox_network,
  'SECCOMP_ALL_NETWORK_SOCKET_SYSCALLS_DENIED'
);
assert.deepEqual(dryRun.network_seccomp_probe, {
  attempted_socket_syscalls: 1,
  denied_socket_syscalls: 1,
  denial_code: 'EPERM',
  packet_count: 0
});
assert.equal(dryRun.spawn_wrapper_error_code, null);
assert.deepEqual(dryRun.network_seccomp_attestation, {
  delegated_fd_byte_count: plan.isolation.network_seccomp.byte_count,
  delegated_fd_sha256: plan.isolation.network_seccomp.sha256,
  ambient_seccomp_mode: dryRun.worker_attestation.ambient_seccomp_mode,
  ambient_seccomp_filter_count:
    dryRun.worker_attestation.ambient_seccomp_filter_count,
  worker_seccomp_mode: 2,
  worker_seccomp_filter_count:
    dryRun.worker_attestation.ambient_seccomp_filter_count + 1,
  filter_count_increment: 1,
  probe_role: 'CORROBORATING_ONLY_NOT_CAUSAL_PROOF'
});
assert.match(
  dryRun.worker_attestation.request_nonce,
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
);
assert.match(dryRun.worker_attestation.request_sha256, /^[0-9a-f]{64}$/);
assert.deepEqual(dryRun.observations.calls, plan.host_adapter.method_sequence);
assert.deepEqual(
  dryRun.observations.discovered_plugin_names,
  ['AGENTSOSResident']
);
assert.deepEqual(dryRun.observations.initialize_return, { initialized: false });
assert.deepEqual(dryRun.observations.shutdown_return, { shutdown: true });
assert.equal(dryRun.observations.processToolCall_count, 0);
assert.equal(dryRun.observations.native_addon_require_count, 0);
assert.equal(dryRun.observations.child_process_spawn_count, 0);

for (const completion of [
  {
    error: Object.assign(new Error('ambient wrapper rejection'), {
      code: 'EPERM'
    }),
    status: 1,
    signal: null
  },
  {
    error: Object.assign(new Error('missing executable'), { code: 'ENOENT' }),
    status: null,
    signal: null
  },
  { error: null, status: 2, signal: null },
  { error: null, status: null, signal: 'SIGKILL' }
]) {
  assert.throws(
    () => validateSpawnCompletion(completion),
    (error) => error?.code === 'BLOCKED_OS_SANDBOX_EXECUTION'
  );
}
validateSpawnCompletion({ error: null, status: 0, signal: null });
validateSpawnCompletion({ error: null, status: 1, signal: null });

const fdFixtureRoot = await mkdtemp(
  path.join(os.tmpdir(), 'agents-os-phase5d-seccomp-fd-test-')
);
const expectedSeccompBytes = Buffer.from(
  plan.isolation.network_seccomp.base64,
  'base64'
);
const goodSeccompHandle = await openUnlinkedFixture(
  fdFixtureRoot,
  'good.bpf',
  expectedSeccompBytes,
  fsConstants.O_RDONLY
);
const firstGoodAttestation = await attestNetworkSeccompHandle(
  goodSeccompHandle,
  plan
);
const secondGoodAttestation = await attestNetworkSeccompHandle(
  goodSeccompHandle,
  plan
);
assert.deepEqual(secondGoodAttestation, firstGoodAttestation);
await goodSeccompHandle.close();

const weakenedSeccompBytes = Buffer.from(expectedSeccompBytes);
weakenedSeccompBytes[weakenedSeccompBytes.length - 1] ^= 0x01;
const restoredPath = path.join(fdFixtureRoot, 'delegated-weak.bpf');
const weakenedDelegatedHandle = await openUnlinkedFixture(
  fdFixtureRoot,
  'delegated-weak.bpf',
  weakenedSeccompBytes,
  fsConstants.O_RDONLY
);
await writeFile(restoredPath, expectedSeccompBytes, {
  flag: 'wx',
  mode: 0o600
});
await assert.rejects(
  attestNetworkSeccompHandle(weakenedDelegatedHandle, plan),
  (error) => error?.code === 'BLOCKED_NETWORK_SECCOMP_FD_BINDING'
);
await weakenedDelegatedHandle.close();
await unlink(restoredPath);

const modifiedAfterHashHandle = await openUnlinkedFixture(
  fdFixtureRoot,
  'modified-after-hash.bpf',
  expectedSeccompBytes
);
await attestNetworkSeccompHandle(modifiedAfterHashHandle, plan);
await modifiedAfterHashHandle.write(
  Buffer.from([expectedSeccompBytes[0] ^ 0x01]),
  0,
  1,
  0
);
await modifiedAfterHashHandle.sync();
await assert.rejects(
  attestNetworkSeccompHandle(modifiedAfterHashHandle, plan),
  (error) => error?.code === 'BLOCKED_NETWORK_SECCOMP_FD_BINDING'
);
await modifiedAfterHashHandle.close();

for (const [name, bytes] of [
  ['truncated.bpf', expectedSeccompBytes.subarray(0, -1)],
  ['trailing.bpf', Buffer.concat([expectedSeccompBytes, Buffer.from([0])])]
]) {
  const handle = await openUnlinkedFixture(
    fdFixtureRoot,
    name,
    bytes,
    fsConstants.O_RDONLY
  );
  await assert.rejects(
    attestNetworkSeccompHandle(handle, plan),
    (error) => error?.code === 'BLOCKED_NETWORK_SECCOMP_FD_BINDING'
  );
  await handle.close();
}

const canonicalOutput = Buffer.from(
  `${JSON.stringify({ fixture: 'canonical' }, null, 2)}\n`,
  'utf8'
);
const canonicalOutputHandle = await openUnlinkedFixture(
  fdFixtureRoot,
  'canonical-output.json',
  canonicalOutput
);
assert.deepEqual(
  (await readCanonicalWorkerOutputHandle(canonicalOutputHandle)).value,
  { fixture: 'canonical' }
);
await canonicalOutputHandle.close();

const invalidOutputs = [
  ['empty-output.json', Buffer.alloc(0)],
  ['invalid-json.json', Buffer.from('{', 'utf8')],
  ['noncanonical.json', Buffer.from('{"fixture":true}\n', 'utf8')],
  ['duplicate-key.json', Buffer.from('{"a":1,"a":2}\n', 'utf8')],
  ['double-newline.json', Buffer.from('{\n  "a": 1\n}\n\n', 'utf8')],
  ['trailing-junk.json', Buffer.from('{\n  "a": 1\n}\nX', 'utf8')],
  ['invalid-utf8.json', Buffer.from([0xff])],
  ['oversize.json', Buffer.alloc(4 * 1024 * 1024 + 1, 0x20)]
];
for (const [name, bytes] of invalidOutputs) {
  const handle = await openUnlinkedFixture(fdFixtureRoot, name, bytes);
  await assert.rejects(
    readCanonicalWorkerOutputHandle(handle),
    (error) => error?.code === 'BLOCKED_OS_SANDBOX_OUTPUT'
  );
  await handle.close();
}
await rmdir(fdFixtureRoot);

const processToolCall = await runSyntheticDryRun('processToolCall');
assert.equal(processToolCall.result, 'BLOCKED_CLEAN');
assert.equal(processToolCall.failure.code, 'BLOCKED_PROCESS_TOOL_CALL');
assert.equal(processToolCall.cleanup_status, 'CLEAN');
assert.equal(processToolCall.owned_temporary_residue_count, 0);
assert.equal(processToolCall.observations.processToolCall_count, 1);

const unknownRequire = await runSyntheticDryRun('unknownRequire');
assert.equal(unknownRequire.result, 'BLOCKED_CLEAN');
assert.equal(unknownRequire.failure.code, 'BLOCKED_UNDECLARED_HOST_REQUIRE');
assert.equal(unknownRequire.cleanup_status, 'CLEAN');
assert.equal(unknownRequire.owned_temporary_residue_count, 0);

const outsideRead = await runSyntheticDryRun('outsideRead');
assert.equal(outsideRead.result, 'BLOCKED_CLEAN');
assert.equal(outsideRead.failure.code, 'BLOCKED_HOST_FILESYSTEM_READ');
assert.equal(outsideRead.cleanup_status, 'CLEAN');
assert.equal(outsideRead.owned_temporary_residue_count, 0);

const bufferEscape = await runSyntheticDryRun('bufferEscape');
assert.equal(bufferEscape.result, 'BLOCKED_CLEAN');
assert.equal(bufferEscape.failure.code, 'BLOCKED_VM_CONSTRUCTOR_ESCAPE');
assert.equal(bufferEscape.cleanup_status, 'CLEAN');
assert.equal(bufferEscape.owned_temporary_residue_count, 0);

const outerFunctionEscape = await runSyntheticDryRun('outerFunctionEscape');
assert.equal(outerFunctionEscape.result, 'BLOCKED_CLEAN');
assert.equal(outerFunctionEscape.failure.code, 'BLOCKED_OS_SANDBOX_ACCESS');
assert.equal(outerFunctionEscape.cleanup_status, 'CLEAN');
assert.equal(outerFunctionEscape.owned_temporary_residue_count, 0);

assert.equal(await absent(ACTUAL_ROOT), true);
assert.equal(await absent(CLAIM), true);
assert.equal(await absent(RECEIPT), true);

const loaded = await loadPlan();
assert.deepEqual(loaded.plan, plan);

const pureGateDecision = {
  schema_version: plan.trust_root.gate_1_schema_version,
  decision_id: 'JENN_PHASE_5D_M0D_MINIMUM_HOST_SMOKE_GATE_1_V0_3',
  owner: 'Jenn',
  candidate_commit: 'a'.repeat(40),
  plan_sha256: 'b'.repeat(64),
  runner_sha256: 'c'.repeat(64),
  tests_sha256: 'd'.repeat(64),
  independent_review_relative_path:
    'control-plane/registry/reviews/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3-independent-review.yaml',
  independent_review_sha256: 'e'.repeat(64),
  independent_review_result: 'PASS_NO_BLOCKER',
  quarantine_root: plan.paths.actual_quarantine_root,
  gate_1_claim_relative_path: plan.paths.gate_1_claim_relative_path,
  receipt_relative_path: plan.paths.receipt_relative_path,
  sealed_host_commit: plan.sealed_host.commit,
  sealed_host_tree: plan.sealed_host.tree,
  sealed_host_blob_oid: plan.sealed_host.plugin_manager_blob_oid,
  allowed_method_sequence: plan.host_adapter.method_sequence,
  actual_host_smoke_authorized: true,
  authorized_once: true
};
validateGateDecision(pureGateDecision, plan);
assert.throws(
  () =>
    validateGateDecision(
      { ...pureGateDecision, gate_1_claim_relative_path: 'wrong' },
      plan
    ),
  (error) => error?.name === 'Blocked'
);

const claimFixtureRoot = await mkdtemp(
  path.join(os.tmpdir(), 'agents-os-phase5d-gate-claim-test-')
);
const claimFixturePath = path.join(claimFixtureRoot, 'claim.json');
const claimBytes = Buffer.from('{"state":"CONSUMED_PENDING"}\n', 'utf8');
const claimChildSource = [
  `const { createExclusiveClaim } = await import(${JSON.stringify(RUNNER_URL)});`,
  'try {',
  `  await createExclusiveClaim({ claimPath: ${JSON.stringify(claimFixturePath)}, allowedDirectory: ${JSON.stringify(claimFixtureRoot)}, bytes: Buffer.from(${JSON.stringify(claimBytes.toString('base64'))}, 'base64') });`,
  '  process.exitCode = 0;',
  '} catch (error) {',
  "  process.exitCode = error?.code === 'BLOCKED_GATE_1_ALREADY_CONSUMED' ? 31 : 99;",
  '}'
].join('\n');
const claimProcessResults = await Promise.all(
  Array.from(
    { length: 32 },
    () =>
      new Promise((resolve, reject) => {
        const child = spawn(
          process.execPath,
          ['--input-type=module', '--eval', claimChildSource],
          {
            stdio: 'ignore',
            timeout: 10000,
            killSignal: 'SIGKILL'
          }
        );
        child.once('error', reject);
        child.once('exit', (code, signal) => resolve({ code, signal }));
      })
  )
);
assert.equal(
  claimProcessResults.filter(
    (item) => item.code === 0 && item.signal === null
  ).length,
  1
);
assert.equal(
  claimProcessResults.filter(
    (item) => item.code === 31 && item.signal === null
  ).length,
  31
);
assert.deepEqual(await readFile(claimFixturePath), claimBytes);
assert.equal((await lstat(claimFixturePath)).mode & 0o777, 0o600);
assert.equal(await absent(path.join(claimFixtureRoot, 'receipt.json')), true);
await assert.rejects(
  createExclusiveClaim({
    claimPath: claimFixturePath,
    allowedDirectory: claimFixtureRoot,
    bytes: claimBytes
  }),
  (error) => error?.code === 'BLOCKED_GATE_1_ALREADY_CONSUMED'
);
await unlink(claimFixturePath);
await rmdir(claimFixtureRoot);

const sigkillFixtureRoot = await mkdtemp(
  path.join(os.tmpdir(), 'agents-os-phase5d-gate-claim-sigkill-test-')
);
const sigkillClaimPath = path.join(sigkillFixtureRoot, 'claim.json');
const sigkillReceiptPath = path.join(sigkillFixtureRoot, 'receipt.json');
const sigkillChildSource = [
  `const { createExclusiveClaim } = await import(${JSON.stringify(RUNNER_URL)});`,
  `await createExclusiveClaim({ claimPath: ${JSON.stringify(sigkillClaimPath)}, allowedDirectory: ${JSON.stringify(sigkillFixtureRoot)}, bytes: Buffer.from(${JSON.stringify(claimBytes.toString('base64'))}, 'base64') });`,
  "process.kill(process.pid, 'SIGKILL');"
].join('\n');
const sigkillResult = spawnSync(
  process.execPath,
  ['--input-type=module', '--eval', sigkillChildSource],
  {
    stdio: 'ignore',
    timeout: 10000,
    killSignal: 'SIGKILL'
  }
);
assert.equal(sigkillResult.error, undefined);
assert.equal(sigkillResult.status, null);
assert.equal(sigkillResult.signal, 'SIGKILL');
assert.deepEqual(await readFile(sigkillClaimPath), claimBytes);
assert.equal((await lstat(sigkillClaimPath)).mode & 0o777, 0o600);
assert.equal(await absent(sigkillReceiptPath), true);
await assert.rejects(
  createExclusiveClaim({
    claimPath: sigkillClaimPath,
    allowedDirectory: sigkillFixtureRoot,
    bytes: claimBytes
  }),
  (error) => error?.code === 'BLOCKED_GATE_1_ALREADY_CONSUMED'
);
await unlink(sigkillClaimPath);
await rmdir(sigkillFixtureRoot);

const receiptFailureFixtureRoot = await mkdtemp(
  path.join(os.tmpdir(), 'agents-os-phase5d-gate-receipt-eacces-test-')
);
const receiptFailureClaimPath = path.join(
  receiptFailureFixtureRoot,
  'claim.json'
);
const deniedReceiptPath = path.join(receiptFailureFixtureRoot, 'receipt.json');
await createExclusiveClaim({
  claimPath: receiptFailureClaimPath,
  allowedDirectory: receiptFailureFixtureRoot,
  bytes: claimBytes
});
let receiptWriteError = null;
await chmod(receiptFailureFixtureRoot, 0o500);
try {
  await writeFile(deniedReceiptPath, '{"result":"unexpected"}\n', {
    flag: 'wx',
    mode: 0o600
  });
} catch (error) {
  receiptWriteError = error?.code ?? error?.name;
} finally {
  await chmod(receiptFailureFixtureRoot, 0o700);
}
assert.equal(receiptWriteError, 'EACCES');
assert.deepEqual(await readFile(receiptFailureClaimPath), claimBytes);
assert.equal(await absent(deniedReceiptPath), true);
await assert.rejects(
  createExclusiveClaim({
    claimPath: receiptFailureClaimPath,
    allowedDirectory: receiptFailureFixtureRoot,
    bytes: claimBytes
  }),
  (error) => error?.code === 'BLOCKED_GATE_1_ALREADY_CONSUMED'
);
await unlink(receiptFailureClaimPath);
await rmdir(receiptFailureFixtureRoot);

process.stdout.write(
  `${JSON.stringify({
    result: 'PASS',
    positive_dry_runs: 1,
    plan_negative_cases: 22,
    seccomp_focused_plan_negative_cases: 14,
    runtime_negative_cases: 5,
    constructor_escape_cases: 2,
    delegated_seccomp_fd_positive_cases: 2,
    delegated_seccomp_fd_negative_cases: 4,
    canonical_output_positive_cases: 1,
    canonical_output_negative_cases: invalidOutputs.length,
    spawn_completion_positive_cases: 2,
    spawn_completion_negative_cases: 4,
    network_seccomp_bytes: sealedSeccompBytes.length,
    network_seccomp_instructions: seccompInstructions.length,
    network_seccomp_denied_syscalls: 14,
    network_seccomp_probe_denials: 1,
    network_packet_count: 0,
    gate_1_pure_preflight_cases: 2,
    gate_1_atomic_claim_winners: 1,
    gate_1_atomic_claim_losers: 31,
    gate_1_concurrent_processes: 32,
    gate_1_concurrent_second_claim_rejected: true,
    gate_1_sigkill_claim_persisted: true,
    gate_1_sigkill_receipt_absent: true,
    gate_1_sigkill_replay_rejected: true,
    gate_1_receipt_write_error: receiptWriteError,
    gate_1_receipt_failure_claim_persisted: true,
    gate_1_receipt_failure_receipt_absent: true,
    gate_1_receipt_failure_replay_rejected: true,
    gate_1_missing_receipt_replay_rejected: true,
    actual_cli_preflight_invocations: 0,
    actual_Host_execution_count: 0,
    VCPToolBox_Git_command_count: 0,
    Host_operation_count: 0,
    actual_root_absent: true,
    claim_absent: true,
    receipt_absent: true
  })}\n`
);
