import assert from 'node:assert/strict';
import {
  chmodSync,
  chownSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync
} from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  renderDaemonIdentityPolicy,
  renderSystemdUnit
} from '../tools/render-systemd-unit.mjs';

function fixture(t) {
  const root = mkdtempSync(path.join(
    tmpdir(),
    'agents-os-resident-systemd-renderer-'
  ));
  chmodSync(root, 0o700);
  const pluginRoot = path.join(root, 'plugin');
  const stateRoot = path.join(root, 'state');
  const activationRoot = path.join(
    stateRoot,
    'agents-os-resident-local-owner-v1'
  );
  const witnessRoot = path.join(stateRoot, 'protected-witness');
  const memoryBodyRoot = path.join(stateRoot, 'private-memory-bodies');
  const currentUid = process.getuid();
  const daemonUid = currentUid === 0 ? 2001 : currentUid;
  const socketGid = process.getgid() === 0 ? 2002 : process.getgid();
  for (const directory of [
    pluginRoot,
    stateRoot,
    activationRoot,
    witnessRoot,
    memoryBodyRoot
  ]) {
    mkdirSync(directory, { mode: 0o700 });
    chmodSync(directory, 0o700);
  }
  if (currentUid === 0) {
    for (const directory of [activationRoot, witnessRoot, memoryBodyRoot]) {
      chownSync(directory, daemonUid, socketGid);
    }
  }
  t.after(() => rmSync(root, { force: true, recursive: true }));
  return {
    activationRoot,
    buildId: `sha256:${'d'.repeat(64)}`,
    daemonUid,
    clientUid: currentUid === 0 ? 2002 : daemonUid === 65534 ? 65533 : 65534,
    socketGid,
    memoryBodyRoot,
    nodeBinary: '/usr/bin/node',
    pluginRoot,
    root,
    stateRoot,
    witnessRoot
  };
}

function renderConfig(value) {
  return {
    activationRoot: value.activationRoot,
    buildId: value.buildId,
    daemonUid: value.daemonUid,
    clientUid: value.clientUid,
    socketGid: value.socketGid,
    memoryBodyRoot: value.memoryBodyRoot,
    nodeBinary: value.nodeBinary,
    pluginRoot: value.pluginRoot,
    witnessRoot: value.witnessRoot
  };
}

test('systemd renderer binds exact protected argv and least-privilege root access', (t) => {
  const roots = fixture(t);
  const rendered = renderSystemdUnit(renderConfig(roots));

  assert.match(rendered, /RestrictAddressFamilies=AF_UNIX/);
  assert.match(rendered, /IPAddressDeny=any/);
  assert.match(rendered, /ProtectSystem=strict/);
  assert.match(rendered, /^RestrictSUIDSGID=no$/mu);
  assert.doesNotMatch(rendered, /^RestrictSUIDSGID=yes$/mu);
  assert.match(rendered, /RuntimeDirectoryMode=0750/);
  assert.ok(rendered.includes(`\nUser=${roots.daemonUid}\n`));
  assert.ok(rendered.includes(`\nGroup=${roots.socketGid}\n`));
  assert.match(rendered, /StandardOutput=null/);
  assert.match(rendered, /StandardError=null/);
  assert.match(rendered, /WantedBy=multi-user\.target/);
  const execStart = rendered.split('\n').find((line) =>
    line.startsWith('ExecStart='));
  assert.equal(execStart, [
    `ExecStart=${roots.nodeBinary}`,
    `${roots.pluginRoot}/companion/resident-daemon.js`,
    '--root',
    roots.activationRoot,
    '--socket',
    '/run/agents-os-resident/control.sock',
    '--expected-build-id',
    roots.buildId,
    '--witness-root',
    roots.witnessRoot,
    '--memory-body-root',
    roots.memoryBodyRoot
  ].join(' '));
  assert.equal(
    rendered.split('\n').find((line) => line.startsWith('ReadOnlyPaths=')),
    `ReadOnlyPaths=${roots.pluginRoot} ${roots.witnessRoot}`
  );
  assert.equal(
    rendered.split('\n').find((line) => line.startsWith('ReadWritePaths=')),
    `ReadWritePaths=${roots.activationRoot} ${roots.memoryBodyRoot}`
  );
  assert.doesNotMatch(rendered, /--continuity-evidence/);
  assert.doesNotMatch(rendered, /--genesis-authority-file/);
  assert.doesNotMatch(rendered, /--genesis-provisioning-authority/);
  assert.doesNotMatch(rendered, /PartOf=/);
  assert.doesNotMatch(rendered, /BindsTo=/);
  assert.doesNotMatch(rendered, /MemoryDenyWriteExecute=/);
  assert.doesNotMatch(rendered, /SystemCallFilter=/);
});

test('identity policy binds exactly the same daemon, client, group and build as the unit', (t) => {
  const roots = fixture(t);
  const config = renderConfig(roots);
  const policy = renderDaemonIdentityPolicy(config);
  assert.deepEqual(policy, {
    schema: 'agents-os-resident.daemon-identity.v1',
    daemonUid: roots.daemonUid,
    clientUid: roots.clientUid,
    socketGid: roots.socketGid,
    packageRoot: roots.pluginRoot,
    nodeBinary: roots.nodeBinary,
    buildId: roots.buildId
  });
  assert.ok(Object.isFrozen(policy));
  assert.ok(!roots.activationRoot.startsWith(`${roots.pluginRoot}/`));
  assert.doesNotThrow(() => renderSystemdUnit(config));
});

test('both projections reject shared, root, malformed and missing identities', (t) => {
  const roots = fixture(t);
  const config = renderConfig(roots);
  for (const render of [renderSystemdUnit, renderDaemonIdentityPolicy]) {
    assert.throws(() => render({ ...config, clientUid: config.daemonUid }),
      /SYSTEMD_RENDER_INPUT_INVALID/);
    for (const key of ['daemonUid', 'clientUid', 'socketGid']) {
      for (const value of [0, -1, 1.5, '1000', null, NaN, Infinity, 0xffffffff]) {
        assert.throws(() => render({ ...config, [key]: value }),
          /SYSTEMD_RENDER_INPUT_INVALID/);
      }
      const missing = { ...config };
      delete missing[key];
      assert.throws(() => render(missing), /SYSTEMD_RENDER_INPUT_INVALID/);
    }
    assert.throws(() => render({
      ...config,
      daemonUid: config.clientUid,
      clientUid: config.daemonUid
    }), /SYSTEMD_RENDER_PROTECTED_ROOT_INVALID/);
    assert.doesNotThrow(() => render({
      ...config, clientUid: 0xfffffffe, socketGid: 0xfffffffe
    }));
  }
});

test('CLI renders a matching policy and unit only with explicit distinct numeric identities', (t) => {
  const roots = fixture(t);
  const output = path.join(roots.root, 'resident.service');
  const identityOutput = path.join(roots.root, 'daemon-identity.json');
  const cli = new URL('../tools/render-systemd-unit.mjs', import.meta.url);
  const args = [
    cli.pathname,
    '--activation-root', roots.activationRoot,
    '--client-uid', String(roots.clientUid),
    '--daemon-uid', String(roots.daemonUid),
    '--identity-output', identityOutput,
    '--memory-body-root', roots.memoryBodyRoot,
    '--node', roots.nodeBinary,
    '--output', output,
    '--plugin-root', roots.pluginRoot,
    '--socket-gid', String(roots.socketGid),
    '--witness-root', roots.witnessRoot
  ];
  const result = spawnSync(process.execPath, args, { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  const policy = JSON.parse(readFileSync(identityOutput, 'utf8'));
  const unit = readFileSync(output, 'utf8');
  assert.deepEqual(policy, renderDaemonIdentityPolicy({
    ...renderConfig(roots), buildId: policy.buildId
  }));
  assert.ok(unit.includes(`--expected-build-id ${policy.buildId}`));
  assert.ok(unit.includes(`\nUser=${policy.daemonUid}\n`));
  assert.ok(unit.includes(`\nGroup=${policy.socketGid}\n`));
  const daemonIndex = args.indexOf('--daemon-uid') + 1;
  for (const badUid of ['0', '-1', '1.5', '1e3', '01000', '4294967295']) {
    const invalid = [...args];
    invalid[daemonIndex] = badUid;
    assert.equal(spawnSync(process.execPath, invalid).status, 1);
    assert.equal(readFileSync(output, 'utf8'), unit);
    assert.equal(readFileSync(identityOutput, 'utf8'), `${JSON.stringify(policy, null, 2)}\n`);
  }
  const sameOutput = [...args];
  sameOutput[sameOutput.indexOf('--identity-output') + 1] = output;
  assert.equal(spawnSync(process.execPath, sameOutput).status, 1);
  assert.equal(readFileSync(output, 'utf8'), unit);
  assert.equal(readFileSync(identityOutput, 'utf8'), `${JSON.stringify(policy, null, 2)}\n`);
  const aliasParent = path.join(roots.root, 'output-alias');
  symlinkSync(roots.root, aliasParent, 'dir');
  for (const aliasedTarget of [path.basename(output), path.basename(identityOutput)]) {
    const aliasedOutput = [...args];
    aliasedOutput[aliasedOutput.indexOf('--identity-output') + 1]
      = path.join(aliasParent, aliasedTarget);
    assert.equal(spawnSync(process.execPath, aliasedOutput).status, 1);
    assert.equal(readFileSync(output, 'utf8'), unit);
    assert.equal(readFileSync(identityOutput, 'utf8'), `${JSON.stringify(policy, null, 2)}\n`);
  }
  const missing = args.filter((_, index) => index !== daemonIndex
    && index !== daemonIndex - 1);
  assert.equal(spawnSync(process.execPath, missing).status, 1);
});

test('--check is explicitly disposable structural verification', () => {
  const result = spawnSync(process.execPath, [
    new URL('../tools/render-systemd-unit.mjs', import.meta.url).pathname,
    '--check'
  ], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout,
    'SYSTEMD_UNIT_STRUCTURAL_CHECK_PASSED; NOT_INSTALLATION_QUALIFICATION\n');
});

test('systemd renderer rejects caller continuity mixing and missing protected roots', (t) => {
  const roots = fixture(t);
  const config = renderConfig(roots);
  assert.throws(() => renderSystemdUnit({
    ...config,
    continuityEvidenceJson: '{}'
  }), /SYSTEMD_RENDER_INPUT_INVALID/);
  assert.throws(() => renderSystemdUnit({
    ...config,
    genesisProvisioningAuthorityJson: '{}'
  }), /SYSTEMD_RENDER_INPUT_INVALID/);
  const withoutWitness = { ...config };
  delete withoutWitness.witnessRoot;
  assert.throws(
    () => renderSystemdUnit(withoutWitness),
    /SYSTEMD_RENDER_INPUT_INVALID/
  );
  const withoutMemory = { ...config };
  delete withoutMemory.memoryBodyRoot;
  assert.throws(
    () => renderSystemdUnit(withoutMemory),
    /SYSTEMD_RENDER_INPUT_INVALID/
  );
});

test('systemd renderer rejects aliased, nested, missing and non-owner-only roots', (t) => {
  const roots = fixture(t);
  const config = renderConfig(roots);
  const witnessAlias = path.join(roots.stateRoot, 'witness-alias');
  symlinkSync(roots.witnessRoot, witnessAlias, 'dir');
  assert.throws(
    () => renderSystemdUnit({ ...config, witnessRoot: witnessAlias }),
    /SYSTEMD_RENDER_PROTECTED_ROOT_INVALID/
  );

  const nestedMemory = path.join(roots.witnessRoot, 'nested-memory');
  mkdirSync(nestedMemory, { mode: 0o700 });
  chmodSync(nestedMemory, 0o700);
  if (process.getuid() === 0) chownSync(nestedMemory, roots.daemonUid, roots.socketGid);
  assert.throws(
    () => renderSystemdUnit({ ...config, memoryBodyRoot: nestedMemory }),
    /SYSTEMD_RENDER_PROTECTED_ROOT_OVERLAP/
  );

  assert.throws(
    () => renderSystemdUnit({
      ...config,
      memoryBodyRoot: path.join(roots.stateRoot, 'missing-memory')
    }),
    /SYSTEMD_RENDER_PROTECTED_ROOT_INVALID/
  );

  const specifierRoot = path.join(roots.stateRoot, 'memory-%t');
  mkdirSync(specifierRoot, { mode: 0o700 });
  chmodSync(specifierRoot, 0o700);
  assert.throws(
    () => renderSystemdUnit({ ...config, memoryBodyRoot: specifierRoot }),
    /SYSTEMD_RENDER_INPUT_INVALID/
  );

  // Root fixtures need only CAP_CHOWN, not CAP_FOWNER, to change this owned
  // disposable directory's mode and restore its synthetic daemon ownership.
  if (process.getuid() === 0) chownSync(roots.memoryBodyRoot, 0, roots.socketGid);
  chmodSync(roots.memoryBodyRoot, 0o755);
  if (process.getuid() === 0) {
    chownSync(roots.memoryBodyRoot, roots.daemonUid, roots.socketGid);
  }
  assert.throws(
    () => renderSystemdUnit(config),
    /SYSTEMD_RENDER_PROTECTED_ROOT_INVALID/
  );
});
