import assert from 'node:assert/strict';
import {
  chmodSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  symlinkSync
} from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { renderSystemdUnit } from '../tools/render-systemd-unit.mjs';

function fixture(t) {
  const root = mkdtempSync(path.join(
    tmpdir(),
    'agents-os-resident-systemd-renderer-'
  ));
  chmodSync(root, 0o700);
  const pluginRoot = path.join(root, 'plugin');
  const stateRoot = path.join(pluginRoot, 'state');
  const activationRoot = path.join(
    stateRoot,
    'agents-os-resident-local-owner-v1'
  );
  const witnessRoot = path.join(stateRoot, 'protected-witness');
  const memoryBodyRoot = path.join(stateRoot, 'private-memory-bodies');
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
  t.after(() => rmSync(root, { force: true, recursive: true }));
  return {
    activationRoot,
    buildId: `sha256:${'d'.repeat(64)}`,
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
  assert.match(rendered, /RuntimeDirectoryMode=0700/);
  assert.match(rendered, /StandardOutput=null/);
  assert.match(rendered, /StandardError=null/);
  assert.match(rendered, /WantedBy=default\.target/);
  const execStart = rendered.split('\n').find((line) =>
    line.startsWith('ExecStart='));
  assert.equal(execStart, [
    `ExecStart=${roots.nodeBinary}`,
    `${roots.pluginRoot}/companion/resident-daemon.js`,
    '--root',
    roots.activationRoot,
    '--socket',
    '%t/agents-os-resident/control.sock',
    '--expected-build-id',
    roots.buildId,
    '--witness-root',
    roots.witnessRoot,
    '--memory-body-root',
    roots.memoryBodyRoot
  ].join(' '));
  assert.equal(
    rendered.split('\n').find((line) => line.startsWith('ReadOnlyPaths=')),
    `ReadOnlyPaths=${roots.pluginRoot} ${roots.witnessRoot} ${roots.memoryBodyRoot}`
  );
  assert.equal(
    rendered.split('\n').find((line) => line.startsWith('ReadWritePaths=')),
    `ReadWritePaths=${roots.activationRoot}`
  );
  assert.doesNotMatch(rendered, /--continuity-evidence/);
  assert.doesNotMatch(rendered, /--genesis-authority-file/);
  assert.doesNotMatch(rendered, /--genesis-provisioning-authority/);
  assert.doesNotMatch(rendered, /PartOf=/);
  assert.doesNotMatch(rendered, /BindsTo=/);
  assert.doesNotMatch(rendered, /MemoryDenyWriteExecute=/);
  assert.doesNotMatch(rendered, /SystemCallFilter=/);
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

  chmodSync(roots.memoryBodyRoot, 0o755);
  assert.throws(
    () => renderSystemdUnit(config),
    /SYSTEMD_RENDER_PROTECTED_ROOT_INVALID/
  );
});
