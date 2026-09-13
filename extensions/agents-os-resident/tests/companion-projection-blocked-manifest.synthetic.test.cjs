'use strict';

// Execute the real ESM projection logic with an entirely synthetic filesystem.
// No Companion implementation, native module, renderer, service or provider loads.
// This test verifies projection naming/refusal, not native or integrity readiness.
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { dirname, resolve } = require('node:path');
const { fileURLToPath } = require('node:url');
const { test } = require('node:test');
const vm = require('node:vm');

const source = readFileSync(
  resolve(__dirname, '../tools/validate-companion-projection.mjs'), 'utf8'
);
const SOURCE_ROOT = '/fixture/source/extensions/agents-os-resident';
const OWNED_ROOT = '/fixture/tmp/agents-os-resident-projection-synthetic';
const PLUGIN_ROOT = `${OWNED_ROOT}/Plugin/AGENTSOSResident`;
const BLOCKED = 'plugin-manifest.json.block';
const ENABLED = 'plugin-manifest.json';
const BLOCKED_BYTES = '{"name":"synthetic-disabled-fixture"}\n';
const BUILD_ID = 'a'.repeat(64);
const VERSION = '0.0.0-synthetic';

async function project(options = {}) {
  const files = new Map();
  const calls = { copied: [], daemon: 0, integrity: [], removed: [], imported: [] };
  let nextInode = 100;
  let snapshot;
  function checked(path) {
    assert.equal(typeof path, 'string');
    assert.ok(path === '/fixture' || path.startsWith('/fixture/'),
      'virtual filesystem rejects paths outside the synthetic fixture');
    return path;
  }
  function directory(path, recursive = true, mode = 0o700) {
    checked(path);
    if (files.has(path)) {
      assert.equal(files.get(path).kind, 'directory');
      return;
    }
    if (path !== '/fixture') {
      const parent = dirname(path);
      if (recursive) directory(parent);
      else assert.ok(files.has(parent), 'synthetic parent must exist');
    }
    files.set(path, { kind: 'directory', mode, uid: 1000, gid: 1000, ino: nextInode++ });
  }
  function put(path, bytes, mode = 0o600) {
    checked(path);
    directory(dirname(path));
    files.set(path, { kind: 'file', bytes: Buffer.from(bytes), mode, uid: 1000,
      gid: 1000, ino: nextInode++ });
  }
  function get(path) {
    checked(path);
    if (!files.has(path)) throw new Error('SYNTHETIC_FILE_MISSING');
    return files.get(path);
  }
  const inventory = ['package.json'];
  if (options.boundBlocked) inventory.push(BLOCKED);
  if (options.boundEnabled) inventory.push(ENABLED);
  const integrity = { buildId: BUILD_ID, packageVersion: VERSION,
    files: inventory.map((path) => ({ path })) };
  put(`${SOURCE_ROOT}/package.json`, '{"name":"synthetic-package"}\n');
  put(`${SOURCE_ROOT}/companion-integrity.json`, JSON.stringify(integrity));
  if (!options.missingSourceBlocked) put(`${SOURCE_ROOT}/${BLOCKED}`, BLOCKED_BYTES);
  if (options.boundEnabled) put(`${SOURCE_ROOT}/${ENABLED}`, '{"synthetic":"enabled"}\n');

  const realpathSync = (path) => { get(path); return path; };
  realpathSync.native = realpathSync;
  const fs = {
    chmodSync(path, mode) { get(path).mode = mode; },
    chownSync(path, uid, gid) { Object.assign(get(path), { uid, gid }); },
    copyFileSync(from, to) {
      const entry = get(from);
      assert.equal(entry.kind, 'file');
      calls.copied.push({ from, to });
      put(to, entry.bytes);
    },
    existsSync(path) { checked(path); return files.has(path); },
    lstatSync(path) {
      const entry = get(path);
      return { ...entry, dev: 1, isDirectory: () => entry.kind === 'directory',
        isSymbolicLink: () => false };
    },
    mkdirSync(path, args = {}) { directory(path, Boolean(args.recursive), args.mode); },
    mkdtempSync(prefix) {
      assert.equal(prefix, '/fixture/tmp/agents-os-resident-projection-');
      directory(OWNED_ROOT);
      if (options.existingEnabled) put(`${PLUGIN_ROOT}/${ENABLED}`, 'synthetic-stale');
      return OWNED_ROOT;
    },
    readdirSync(path) {
      get(path);
      return [...files.keys()].filter((key) => key !== path && dirname(key) === path)
        .map((key) => key.slice(path.length + 1));
    },
    realpathSync,
    readFileSync(path, encoding) {
      const entry = get(path);
      assert.equal(entry.kind, 'file');
      return encoding ? entry.bytes.toString(encoding) : Buffer.from(entry.bytes);
    },
    rmSync(path, args) {
      assert.equal(path, OWNED_ROOT);
      assert.equal(args.recursive, true);
      assert.equal(args.force, true);
      snapshot = new Map(files);
      calls.removed.push(path);
      for (const key of files.keys()) {
        if (key === path || key.startsWith(`${path}/`)) files.delete(key);
      }
    },
    writeFileSync(path, bytes, args) {
      assert.equal(path, `${OWNED_ROOT}/systemd/agents-os-resident.service`);
      assert.equal(args.flag, 'wx');
      assert.equal(files.has(path), false);
      put(path, bytes, args.mode);
      if (options.lateEnabled) put(`${PLUGIN_ROOT}/${ENABLED}`, 'synthetic-late');
      if (options.lateMissingBlocked) files.delete(`${PLUGIN_ROOT}/${BLOCKED}`);
      if (options.lateConfiguration) put(`${PLUGIN_ROOT}/config.env`, 'SYNTHETIC_ONLY=1');
    }
  };
  function verifyCompanionIntegrity(args) {
    calls.integrity.push(args ? args.packageRoot : 'source');
    if (args) assert.equal(args.packageRoot, PLUGIN_ROOT);
    const mismatch = args ? options.stagedMismatch : options.sourceMismatch;
    return { buildId: mismatch ? 'b'.repeat(64) : BUILD_ID, packageVersion: VERSION };
  }
  function createRequire(origin) {
    const isSource = origin === `file://${SOURCE_ROOT}/tools/validate-companion-projection.mjs`;
    if (!isSource) assert.equal(origin, `${PLUGIN_ROOT}/package.json`);
    return (specifier) => {
      calls.imported.push(specifier);
      if (isSource && specifier === '../companion/integrity') {
        return { verifyCompanionIntegrity };
      }
      if (!isSource && specifier === './companion/resident-daemon.js') {
        return { prepareResidentRoots({ argv }) {
          calls.daemon++;
          assert.equal(argv[0], '--operation');
          assert.equal(argv[1], 'prepare-roots');
          assert.equal(argv[argv.length - 1], BUILD_ID);
          for (const flag of ['--root', '--witness-root', '--memory-body-root']) {
            directory(argv[argv.indexOf(flag) + 1]);
          }
        } };
      }
      if (!isSource && specifier === './companion/adapter.js') {
        return { createResidentAdapter() { throw new Error('ADAPTER_EXECUTION_FORBIDDEN'); } };
      }
      throw new Error(`UNADMITTED_REQUIRE:${specifier}`);
    };
  }
  function renderSystemdUnit(args) {
    assert.equal(args.pluginRoot, PLUGIN_ROOT);
    assert.equal(args.buildId, BUILD_ID);
    return `synthetic-unit\n--witness-root ${args.witnessRoot} --memory-body-root ${args.memoryBodyRoot}\n`
      + `ReadWritePaths=${args.activationRoot} ${args.memoryBodyRoot}\n`
      + `ReadOnlyPaths=${args.pluginRoot} ${args.witnessRoot}\n`;
  }
  const forbidden = () => { throw new Error('REAL_PROCESS_CAPABILITY_FORBIDDEN'); };
  const context = vm.createContext({ process: {
    argv: ['/fixture/node', '/fixture/test-only'], execPath: '/fixture/node',
    getuid: () => 1000, geteuid: () => 1000, getgid: () => 1000,
    stdout: { write: forbidden }, stderr: { write: forbidden }, exit: forbidden
  } });
  const imports = new Map([
    ['node:fs', fs], ['node:os', { tmpdir: () => '/fixture/tmp' }],
    ['node:path', { dirname, resolve }], ['node:module', { createRequire }],
    ['node:url', { fileURLToPath }], ['./render-systemd-unit.mjs', { renderSystemdUnit }]
  ]);
  const module = new vm.SourceTextModule(source, {
    context, identifier: 'synthetic-projection-under-test',
    initializeImportMeta(meta) {
      meta.url = `file://${SOURCE_ROOT}/tools/validate-companion-projection.mjs`;
    }
  });
  await module.link((specifier) => {
    assert.ok(imports.has(specifier), `unadmitted ESM import ${specifier}`);
    const values = imports.get(specifier);
    return new vm.SyntheticModule(Object.keys(values), function () {
      for (const [name, value] of Object.entries(values)) this.setExport(name, value);
    }, { context });
  });
  await module.evaluate();
  let result;
  let error;
  try { result = module.namespace.runProjectionPreflight(); }
  catch (caught) { error = caught; }
  return { result, error, calls, snapshot, files };
}

function assertCleaned(run) {
  assert.deepEqual(run.calls.removed, [OWNED_ROOT]);
  assert.equal([...run.files.keys()].some((key) => key.startsWith(OWNED_ROOT)), false);
}

for (const boundBlocked of [false, true]) {
  test(`preserves blocked bytes and never emits enabled manifest (inventory includes blocked: ${boundBlocked})`, async () => {
    const run = await project({ boundBlocked });
    assert.equal(run.error, undefined);
    assert.equal(run.snapshot.get(`${PLUGIN_ROOT}/${BLOCKED}`)?.bytes.toString(), BLOCKED_BYTES);
    assert.equal(run.snapshot.has(`${PLUGIN_ROOT}/${ENABLED}`), false);
    assert.equal(run.calls.copied.some(({ to }) => to === `${PLUGIN_ROOT}/${ENABLED}`), false);
    assert.equal(run.calls.daemon, 2);
    assert.deepEqual(JSON.parse(JSON.stringify(run.result)), {
      result: 'COMPANION_PROJECTION_PREFLIGHT_VERIFIED', runtimeUsable: false,
      installedProjectionWritten: false, serviceInstalled: false, serviceStarted: false
    });
    assertCleaned(run);
  });
}

for (const option of ['boundEnabled', 'existingEnabled']) {
  test(`rejects ${option} before package copying or root preparation`, async () => {
    const run = await project({ [option]: true });
    assert.equal(run.error?.message, 'COMPANION_PROJECTION_INVALID');
    assert.equal(run.calls.copied.length, 0);
    assert.equal(run.calls.daemon, 0);
    assertCleaned(run);
  });
}

for (const option of ['lateEnabled', 'lateMissingBlocked']) {
  test(`rejects ${option} at final projection validation and cleans fixture`, async () => {
    const run = await project({ [option]: true });
    assert.equal(run.error?.message, 'COMPANION_PROJECTION_INVALID');
    assert.equal(run.calls.daemon, 2);
    assertCleaned(run);
  });
}

test('missing source blocked manifest fails without preparing roots', async () => {
  const run = await project({ missingSourceBlocked: true });
  assert.equal(run.error?.message, 'SYNTHETIC_FILE_MISSING');
  assert.equal(run.calls.daemon, 0);
  assertCleaned(run);
});

test('source integrity mismatch still refuses before creating a projection', async () => {
  const run = await project({ sourceMismatch: true });
  assert.equal(run.error?.message, 'COMPANION_SOURCE_INTEGRITY_INVALID');
  assert.deepEqual(run.calls.removed, []);
  assert.equal(run.calls.copied.length, 0);
  assert.equal(run.calls.daemon, 0);
});

test('staged integrity mismatch still refuses and cleans fixture', async () => {
  const run = await project({ stagedMismatch: true });
  assert.equal(run.error?.message, 'COMPANION_PROJECTION_INVALID');
  assertCleaned(run);
});

test('an unexpected staged configuration still refuses and cleans fixture', async () => {
  const run = await project({ lateConfiguration: true });
  assert.equal(run.error?.message, 'COMPANION_PROJECTION_INVALID');
  assertCleaned(run);
});
