'use strict';

const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const test = require('node:test');

// Opt-in: select an already-present official Node image by immutable image ID.
// No pulls, accounts, host installation, systemd or provider execution occurs.
const image = process.env.AGENTS_OS_RESIDENT_CROSS_UID_IMAGE;
test('isolated real-kernel cross-UID daemon transport qualification', {
  skip: image ? false : 'set AGENTS_OS_RESIDENT_CROSS_UID_IMAGE to an existing official Node image ID',
  timeout: 60000
}, (t) => {
  assert.match(image, /^(?:sha256:)?[a-f0-9]{12,64}$/u);
  const name = `resident-cross-uid-${randomUUID()}`;
  const source = path.resolve(__dirname, '..');
  try {
    const result = spawnSync('docker', [
      'run', '--rm', '--pull', 'never', '--name', name,
      '--network', 'none', '--read-only', '--pids-limit', '64',
      '--memory', '512m', '--cap-drop', 'ALL',
      '--cap-add', 'CHOWN', '--cap-add', 'SETUID', '--cap-add', 'SETGID',
      '--cap-add', 'DAC_OVERRIDE', '--security-opt', 'no-new-privileges',
      '--tmpfs', '/opt/resident:rw,exec,nosuid,nodev,mode=0755',
      '--tmpfs', '/etc/agents-os-resident:rw,noexec,nosuid,nodev,mode=0755',
      '--tmpfs', '/run:rw,noexec,nosuid,nodev,mode=0755',
      '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,mode=1777',
      '--mount', `type=bind,source=${source},target=/source,readonly`,
      '--entrypoint', '/usr/local/bin/node', image,
      '/source/tests/fixtures/cross-uid-daemon-identity.cjs', 'orchestrate'
    ], { encoding: 'utf8', timeout: 45000, maxBuffer: 16384 });
    assert.equal(result.error, undefined, result.error?.message);
    assert.equal(result.status, 0, result.stderr || result.stdout);
    assert.match(result.stdout, /CROSS_UID_TRANSPORT_FIXTURE_PASS/u);
    const evidence = JSON.parse(result.stdout.trim().split('\n').at(-1));
    assert.equal(evidence.positiveExchanges, 3);
    assert.equal(evidence.wrongUidDispatched, 0);
    assert.equal(evidence.impostorReceivedBytes, 0);
    assert.equal(evidence.protectedRewriteDenials, 9);
    assert.equal(evidence.hostOwnedStateAncestorRejected, true);
    assert.equal(evidence.installationQualification, false);
    t.diagnostic(JSON.stringify(evidence));
  } finally {
    spawnSync('docker', ['rm', '-f', name], {
      encoding: 'utf8', timeout: 5000, maxBuffer: 1024
    });
  }
});
