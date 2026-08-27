'use strict';

const assert = require('node:assert/strict');
const path = require('node:path');
const test = require('node:test');
const { pathToFileURL } = require('node:url');

const PACKAGE_ROOT = path.resolve(__dirname, '..');

async function tool(relativePath) {
  return import(pathToFileURL(path.join(PACKAGE_ROOT, relativePath)).href);
}

function compilerMessage(message = 'lint finding') {
  return {
    message: {
      code: { code: 'clippy::example' },
      level: 'error',
      message,
      spans: [{ file_name: 'src/lib.rs', is_primary: true, label: null }]
    },
    reason: 'compiler-message',
    target: { name: 'agents_os_resident' }
  };
}

function run(status, messages, error) {
  return {
    error,
    status,
    stdout: `${messages.map(JSON.stringify).join('\n')}\n`
  };
}

test('second-review clippy parser accepts only completed compiler runs', async () => {
  const { parseClippyRun } = await tool('tools/compare-clippy-diagnostics.mjs');
  const success = parseClippyRun(run(0, [
    { reason: 'compiler-artifact', target: { name: 'agents_os_resident' } },
    { reason: 'build-finished', success: true }
  ]));
  assert.equal(success.exitCode, 0);
  assert.equal(success.counts.size, 0);

  const lintFailure = parseClippyRun(run(101, [
    compilerMessage(),
    { reason: 'build-finished', success: false }
  ]));
  assert.equal(lintFailure.exitCode, 101);
  assert.equal([...lintFailure.counts.values()][0], 1);

  for (const invalid of [
    run(1, []),
    run(0, [{ reason: 'build-finished', success: true }]),
    run(1, [{ reason: 'build-finished', success: false }]),
    { error: new Error('spawn failed'), status: null, stdout: '' },
    { error: undefined, status: 0, stdout: 'not-json\n' }
  ]) {
    assert.throws(
      () => parseClippyRun(invalid),
      /CLIPPY_COMPARISON_INFRASTRUCTURE_FAILURE/u
    );
  }
});

test('second-review prerequisite identity/hash checks fail closed', async () => {
  const {
    checkR2ValidationPrerequisites,
    enforceExpectedRepository
  } = await tool('tools/check-r2-validation-prerequisites.mjs');
  const actual = {
    identityOrCommit: 'a'.repeat(40),
    sourceBundle: { sha256: 'b'.repeat(64) }
  };
  assert.throws(
    () => enforceExpectedRepository('HOST', actual, {
      identityOrCommit: 'c'.repeat(40),
      sourceBundleSha256: 'b'.repeat(64)
    }),
    /HOST_COMMIT_MISMATCH/u
  );
  assert.throws(
    () => enforceExpectedRepository('HOST', actual, {
      identityOrCommit: 'a'.repeat(40),
      sourceBundleSha256: 'd'.repeat(64)
    }),
    /HOST_SOURCE_BUNDLE_MISMATCH/u
  );
  assert.throws(
    () => checkR2ValidationPrerequisites({
      AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT: '/tmp/exercised-workspace',
      AGENTS_OS_RESIDENT_VCPCHAT_ROOT: '/tmp/different-vcpchat',
      MMR_P4A_RECOVERY_DOMAIN: '/tmp'
    }),
    /VCPCHAT_CHECKED_ROOT_NOT_EXERCISED_ROOT/u
  );
  assert.throws(
    () => checkR2ValidationPrerequisites({
      AGENTS_OS_RESIDENT_VALIDATION_WORKSPACE_ROOT: '/tmp/exercised-workspace',
      AGENTS_OS_RESIDENT_VCPCHAT_ROOT:
        '/tmp/exercised-workspace/runtime/VCPChat',
      MMR_P4A_RECOVERY_DOMAIN: PACKAGE_ROOT
    }),
    /RECOVERY_DOMAIN_NOT_INDEPENDENT/u
  );
});
