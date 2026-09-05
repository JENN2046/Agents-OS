'use strict';

const assert = require('node:assert/strict');
const {
  chmodSync,
  linkSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  realpathSync,
  renameSync,
  rmSync,
  symlinkSync,
  writeFileSync
} = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  exitCodeFor,
  parseDaemonArgs,
  prepareResidentRoots,
  provisionResident,
  startDaemon
} = require('../companion/resident-daemon');
const {
  ACTIVATION_CONFIRMATION,
  ACTIVATION_MODE
} = require('../companion/constants');

const BUILD_ID = `sha256:${'a'.repeat(64)}`;
const PREPARED = 'RESIDENT_PROTECTED_ROOTS_PREPARED';
const SUCCESS = 'RESIDENT_WITNESS_PROVISIONED';

function canonicalAuthority(overrides = {}) {
  return JSON.stringify({
    authorityId: 'authority:SELFTEST:ONE-SHOT',
    protocol: 'MMR0_GENESIS_PROVISIONING_V1',
    provisioningId: 'provisioning:SELFTEST:ONE-SHOT',
    residentId: 'resident:LOCAL_OWNER_SESSION_V1:jenn',
    ...overrides
  });
}

function createFixture(t, authorityBytes = canonicalAuthority()) {
  const quarantine = mkdtempSync(
    path.join(tmpdir(), 'agents-os-resident-provisioning-unit-')
  );
  chmodSync(quarantine, 0o700);
  const rootPath = path.join(
    quarantine,
    'agents-os-resident-local-owner-v1'
  );
  const witnessRootPath = path.join(quarantine, 'protected-witness');
  const memoryBodyRootPath = path.join(quarantine, 'private-memory-bodies');
  mkdirSync(rootPath, { mode: 0o700 });
  mkdirSync(witnessRootPath, { mode: 0o700 });
  mkdirSync(memoryBodyRootPath, { mode: 0o700 });
  const authorityFilePath = path.join(quarantine, 'genesis-authority.json');
  writeFileSync(authorityFilePath, authorityBytes, {
    flag: 'wx',
    mode: 0o600
  });
  chmodSync(authorityFilePath, 0o600);
  t.after(() => rmSync(quarantine, { recursive: true, force: true }));
  return {
    authorityFilePath,
    memoryBodyRootPath,
    quarantine,
    rootPath,
    witnessRootPath
  };
}

function provisionArgv(fixture, overrides = {}) {
  const values = {
    '--expected-build-id': BUILD_ID,
    '--genesis-authority-file': fixture.authorityFilePath,
    '--memory-body-root': fixture.memoryBodyRootPath,
    '--operation': 'provision',
    '--root': fixture.rootPath,
    '--witness-root': fixture.witnessRootPath,
    ...overrides
  };
  return [
    '--operation', values['--operation'],
    '--root', values['--root'],
    '--witness-root', values['--witness-root'],
    '--memory-body-root', values['--memory-body-root'],
    '--expected-build-id', values['--expected-build-id'],
    '--genesis-authority-file', values['--genesis-authority-file']
  ];
}

function prepareRootsArgv(fixture, overrides = {}) {
  const values = {
    '--expected-build-id': BUILD_ID,
    '--memory-body-root': fixture.memoryBodyRootPath,
    '--operation': 'prepare-roots',
    '--root': fixture.rootPath,
    '--witness-root': fixture.witnessRootPath,
    ...overrides
  };
  return [
    '--operation', values['--operation'],
    '--root', values['--root'],
    '--witness-root', values['--witness-root'],
    '--memory-body-root', values['--memory-body-root'],
    '--expected-build-id', values['--expected-build-id']
  ];
}

function removeFixtureRoots(fixture) {
  for (const rootPath of [
    fixture.rootPath,
    fixture.witnessRootPath,
    fixture.memoryBodyRootPath
  ]) {
    rmSync(rootPath, { recursive: true });
  }
}

function rootProfile(rootPath) {
  const stat = lstatSync(rootPath);
  return {
    canonical: realpathSync.native(rootPath) === rootPath,
    dev: stat.dev,
    directory: stat.isDirectory(),
    ino: stat.ino,
    mode: stat.mode & 0o777,
    symlink: stat.isSymbolicLink(),
    uid: stat.uid
  };
}

function serveArgv(fixture, extras = []) {
  return [
    '--root', fixture.rootPath,
    '--socket', path.join(fixture.quarantine, 'runtime', 'control.sock'),
    '--expected-build-id', BUILD_ID,
    '--witness-root', fixture.witnessRootPath,
    '--memory-body-root', fixture.memoryBodyRootPath,
    ...extras
  ];
}

async function assertAuthorityRejected(t, authorityBytes, mutate = null) {
  const fixture = createFixture(t, authorityBytes);
  mutate?.(fixture);
  let lifecycleCalls = 0;
  await assert.rejects(
    provisionResident({
      argv: provisionArgv(fixture),
      verifyIntegrity: () => ({ buildId: BUILD_ID }),
      createLifecycle: () => {
        lifecycleCalls += 1;
        throw new Error('LIFECYCLE_MUST_NOT_BE_CREATED');
      }
    }),
    (error) => error.code === 'RESIDENT_PROVISIONING_AUTHORITY_REJECTED'
      && error.message === 'RESIDENT_PROVISIONING_AUTHORITY_REJECTED'
  );
  assert.equal(lifecycleCalls, 0);
}

test('provision parser is one exact profile and protected serve has no genesis bypass', (t) => {
  const fixture = createFixture(t);
  const valid = provisionArgv(fixture);
  assert.deepEqual(parseDaemonArgs(valid), {
    authorityFilePath: fixture.authorityFilePath,
    continuityEvidence: null,
    expectedBuildId: BUILD_ID,
    genesisProvisioningAuthority: null,
    memoryBodyRootPath: fixture.memoryBodyRootPath,
    operation: 'provision',
    rootPath: fixture.rootPath,
    socketPath: null,
    witnessRootPath: fixture.witnessRootPath
  });

  const reject = (argv) => assert.throws(
    () => parseDaemonArgs(argv),
    {
      code: 'RESIDENT_DAEMON_CONFIGURATION_INVALID',
      message: 'RESIDENT_DAEMON_CONFIGURATION_INVALID'
    }
  );
  for (const required of [
    '--operation',
    '--root',
    '--witness-root',
    '--memory-body-root',
    '--expected-build-id',
    '--genesis-authority-file'
  ]) {
    const index = valid.indexOf(required);
    reject([...valid.slice(0, index), ...valid.slice(index + 2)]);
  }
  reject([...valid, '--socket', '/tmp/forbidden.sock']);
  reject([...valid, '--continuity-evidence', '{}']);
  reject([...valid, '--genesis-provisioning-authority', canonicalAuthority()]);
  reject([...valid, '--root', fixture.rootPath]);
  reject([...valid, '--unknown']);
  reject(valid.map((value) => value === 'provision' ? 'PROVISION' : value));
  reject(valid.map((value) => value === fixture.authorityFilePath
    ? 'relative-authority.json'
    : value));
  reject(provisionArgv(fixture, {
    '--witness-root': fixture.rootPath
  }));
  reject(provisionArgv(fixture, {
    '--witness-root': path.join(fixture.rootPath, 'nested-witness')
  }));
  reject(provisionArgv(fixture, {
    '--memory-body-root': `${fixture.quarantine}/alias/../private-memory-bodies`
  }));
  reject(provisionArgv(fixture, {
    '--root': path.join(fixture.quarantine, 'wrong-resident-leaf')
  }));

  reject(serveArgv(fixture, [
    '--genesis-provisioning-authority',
    canonicalAuthority()
  ]));
  reject(serveArgv(fixture, [
    '--continuity-evidence',
    '{}'
  ]));
  reject(serveArgv(fixture).map((value) => value === fixture.witnessRootPath
    ? fixture.rootPath
    : value));
});

test('provision rejects an invalid Resident leaf before creating protected roots', async (t) => {
  const fixture = createFixture(t);
  removeFixtureRoots(fixture);
  const invalidRoot = path.join(fixture.quarantine, 'wrong-resident-leaf');
  let integrityCalls = 0;
  let lifecycleCalls = 0;
  await assert.rejects(
    provisionResident({
      argv: provisionArgv(fixture, { '--root': invalidRoot }),
      verifyIntegrity: () => {
        integrityCalls += 1;
        return { buildId: BUILD_ID };
      },
      createLifecycle: () => {
        lifecycleCalls += 1;
        throw new Error('LIFECYCLE_MUST_NOT_BE_CREATED');
      }
    }),
    { code: 'RESIDENT_DAEMON_CONFIGURATION_INVALID' }
  );
  assert.equal(integrityCalls, 0);
  assert.equal(lifecycleCalls, 0);
  for (const rootPath of [
    invalidRoot,
    fixture.witnessRootPath,
    fixture.memoryBodyRootPath
  ]) assert.equal(lstatSync(rootPath, { throwIfNoEntry: false }), undefined);
});

test('root-only preparation creates exact protected roots once and preserves identity', (t) => {
  const fixture = createFixture(t);
  removeFixtureRoots(fixture);
  const argv = prepareRootsArgv(fixture);
  assert.deepEqual(parseDaemonArgs(argv), {
    authorityFilePath: null,
    continuityEvidence: null,
    expectedBuildId: BUILD_ID,
    genesisProvisioningAuthority: null,
    memoryBodyRootPath: fixture.memoryBodyRootPath,
    operation: 'prepare-roots',
    rootPath: fixture.rootPath,
    socketPath: null,
    witnessRootPath: fixture.witnessRootPath
  });

  const first = prepareResidentRoots({
    argv,
    verifyIntegrity: () => ({ buildId: BUILD_ID })
  });
  assert.deepEqual(first, {
    operation: 'prepare-roots',
    result: PREPARED
  });
  const firstProfiles = [
    fixture.rootPath,
    fixture.witnessRootPath,
    fixture.memoryBodyRootPath
  ].map(rootProfile);
  for (const profile of firstProfiles) {
    assert.equal(profile.directory, true);
    assert.equal(profile.symlink, false);
    assert.equal(profile.canonical, true);
    assert.equal(profile.uid, process.geteuid());
    assert.equal(profile.mode, 0o700);
  }
  assert.equal(new Set(firstProfiles.map(
    (profile) => `${profile.dev}:${profile.ino}`
  )).size, 3);
  assert.deepEqual(readdirSync(fixture.rootPath), []);
  assert.deepEqual(readdirSync(fixture.witnessRootPath), []);
  assert.deepEqual(readdirSync(fixture.memoryBodyRootPath), []);

  const second = prepareResidentRoots({
    argv,
    verifyIntegrity: () => ({ buildId: BUILD_ID })
  });
  assert.deepEqual(second, first);
  const secondProfiles = [
    fixture.rootPath,
    fixture.witnessRootPath,
    fixture.memoryBodyRootPath
  ].map(rootProfile);
  assert.deepEqual(secondProfiles, firstProfiles);
});

test('root-only preparation rejects parent replacement before descriptor acquisition', (t) => {
  const fixture = createFixture(t);
  const stateParent = path.join(fixture.quarantine, 'state-parent');
  const retainedParent = path.join(fixture.quarantine, 'retained-parent');
  const replacementParent = path.join(fixture.quarantine, 'replacement-parent');
  mkdirSync(stateParent, { mode: 0o700 });
  mkdirSync(replacementParent, { mode: 0o700 });
  const replacedFixture = {
    ...fixture,
    rootPath: path.join(stateParent, 'agents-os-resident-local-owner-v1'),
    witnessRootPath: path.join(stateParent, 'protected-witness'),
    memoryBodyRootPath: path.join(stateParent, 'private-memory-bodies')
  };

  assert.throws(
    () => prepareResidentRoots({
      argv: prepareRootsArgv(replacedFixture),
      verifyIntegrity: () => ({ buildId: BUILD_ID }),
      loadNative: () => {
        renameSync(stateParent, retainedParent);
        symlinkSync(replacementParent, stateParent);
        return require('../agents-os-resident.linux-x64-gnu.node');
      }
    }),
    { code: 'RESIDENT_PROVISIONING_ROOT_REJECTED' }
  );
  for (const leaf of [
    'agents-os-resident-local-owner-v1',
    'protected-witness',
    'private-memory-bodies'
  ]) {
    assert.equal(lstatSync(path.join(replacementParent, leaf), {
      throwIfNoEntry: false
    }), undefined);
    assert.equal(lstatSync(path.join(retainedParent, leaf), {
      throwIfNoEntry: false
    }), undefined);
  }
});

test('root-only preparation fails closed before creation for unsafe existing state', async (t) => {
  await t.test('wrong mode', (inner) => {
    const fixture = createFixture(inner);
    removeFixtureRoots(fixture);
    mkdirSync(fixture.witnessRootPath, { mode: 0o750 });
    assert.throws(
      () => prepareResidentRoots({
        argv: prepareRootsArgv(fixture),
        verifyIntegrity: () => ({ buildId: BUILD_ID })
      }),
      { code: 'RESIDENT_PROVISIONING_ROOT_REJECTED' }
    );
    assert.equal(lstatSync(fixture.witnessRootPath).mode & 0o777, 0o750);
    assert.equal(lstatSync(fixture.rootPath, { throwIfNoEntry: false }), undefined);
    assert.equal(
      lstatSync(fixture.memoryBodyRootPath, { throwIfNoEntry: false }),
      undefined
    );
  });

  await t.test('symlink', (inner) => {
    const fixture = createFixture(inner);
    removeFixtureRoots(fixture);
    const outside = path.join(fixture.quarantine, 'outside');
    mkdirSync(outside, { mode: 0o700 });
    symlinkSync(outside, fixture.witnessRootPath);
    assert.throws(
      () => prepareResidentRoots({
        argv: prepareRootsArgv(fixture),
        verifyIntegrity: () => ({ buildId: BUILD_ID })
      }),
      { code: 'RESIDENT_PROVISIONING_ROOT_REJECTED' }
    );
    assert.equal(lstatSync(fixture.witnessRootPath).isSymbolicLink(), true);
    assert.equal(lstatSync(fixture.rootPath, { throwIfNoEntry: false }), undefined);
    assert.equal(
      lstatSync(fixture.memoryBodyRootPath, { throwIfNoEntry: false }),
      undefined
    );
  });

  await t.test('wrong type', (inner) => {
    const fixture = createFixture(inner);
    removeFixtureRoots(fixture);
    writeFileSync(fixture.witnessRootPath, '', { flag: 'wx', mode: 0o600 });
    assert.throws(
      () => prepareResidentRoots({
        argv: prepareRootsArgv(fixture),
        verifyIntegrity: () => ({ buildId: BUILD_ID })
      }),
      { code: 'RESIDENT_PROVISIONING_ROOT_REJECTED' }
    );
    assert.equal(lstatSync(fixture.witnessRootPath).isFile(), true);
    assert.equal(lstatSync(fixture.rootPath, { throwIfNoEntry: false }), undefined);
    assert.equal(
      lstatSync(fixture.memoryBodyRootPath, { throwIfNoEntry: false }),
      undefined
    );
  });

  await t.test('overlapping topology', (inner) => {
    const fixture = createFixture(inner);
    assert.throws(
      () => parseDaemonArgs(prepareRootsArgv(fixture, {
        '--memory-body-root': path.join(fixture.witnessRootPath, 'memory')
      })),
      { code: 'RESIDENT_DAEMON_CONFIGURATION_INVALID' }
    );
  });
});

test('ordinary one-shot provisioning reuses source-owned root preparation', async (t) => {
  const fixture = createFixture(t);
  removeFixtureRoots(fixture);
  let initializeCalls = 0;
  const result = await provisionResident({
    argv: provisionArgv(fixture),
    verifyIntegrity: () => ({ buildId: BUILD_ID }),
    createLifecycle: () => ({
      initialize: async () => {
        initializeCalls += 1;
      },
      shutdown: async () => {}
    })
  });
  assert.deepEqual(result, {
    operation: 'provision',
    result: SUCCESS
  });
  assert.equal(initializeCalls, 1);
  for (const rootPath of [
    fixture.rootPath,
    fixture.witnessRootPath,
    fixture.memoryBodyRootPath
  ]) {
    const profile = rootProfile(rootPath);
    assert.equal(profile.canonical, true);
    assert.equal(profile.directory, true);
    assert.equal(profile.mode, 0o700);
    assert.equal(profile.symlink, false);
    assert.equal(profile.uid, process.geteuid());
  }
});

test('one-shot provisioning verifies integrity, initializes, shuts down, and never starts a server', async (t) => {
  const fixture = createFixture(t);
  const events = [];
  let activationConfig;
  let serverCalls = 0;
  const result = await provisionResident({
    argv: provisionArgv(fixture),
    verifyIntegrity: () => {
      events.push('integrity');
      return { buildId: BUILD_ID };
    },
    createLifecycle: () => {
      events.push('create-lifecycle');
      return {
        initialize: async (config) => {
          events.push('initialize');
          activationConfig = config;
        },
        shutdown: async () => {
          events.push('shutdown');
        }
      };
    },
    createServer: () => {
      serverCalls += 1;
      throw new Error('SERVER_MUST_NOT_BE_CREATED');
    }
  });
  assert.deepEqual(events, [
    'integrity',
    'create-lifecycle',
    'initialize',
    'shutdown'
  ]);
  assert.equal(serverCalls, 0);
  assert.deepEqual(activationConfig, {
    AGENTS_OS_RESIDENT_ACTIVATION_CONFIRMATION: ACTIVATION_CONFIRMATION,
    AGENTS_OS_RESIDENT_ACTIVATION_MODE: ACTIVATION_MODE,
    AGENTS_OS_RESIDENT_GENESIS_PROVISIONING_AUTHORITY: JSON.parse(
      canonicalAuthority()
    ),
    AGENTS_OS_RESIDENT_MEMORY_BODY_ROOT: fixture.memoryBodyRootPath,
    AGENTS_OS_RESIDENT_ROOT: fixture.rootPath,
    AGENTS_OS_RESIDENT_WITNESS_ROOT: fixture.witnessRootPath
  });
  assert.deepEqual(result, {
    operation: 'provision',
    result: SUCCESS
  });

  let lifecycleCalls = 0;
  await assert.rejects(
    provisionResident({
      argv: provisionArgv(fixture, {
        '--expected-build-id': `sha256:${'0'.repeat(64)}`
      }),
      verifyIntegrity: () => ({ buildId: BUILD_ID }),
      createLifecycle: () => {
        lifecycleCalls += 1;
      }
    }),
    { code: 'RESIDENT_INTEGRITY_MISMATCH' }
  );
  assert.equal(lifecycleCalls, 0);

  await assert.rejects(
    provisionResident({
      argv: provisionArgv(fixture, {
        '--expected-build-id': `sha256:${'0'.repeat(64)}`,
        '--genesis-authority-file': path.join(
          fixture.quarantine,
          'authority-must-not-be-read.json'
        )
      }),
      verifyIntegrity: () => ({ buildId: BUILD_ID }),
      createLifecycle: () => {
        throw new Error('LIFECYCLE_MUST_NOT_BE_CREATED');
      }
    }),
    { code: 'RESIDENT_INTEGRITY_MISMATCH' }
  );

  await assert.rejects(
    provisionResident({
      argv: provisionArgv(fixture),
      verifyIntegrity: () => ({ buildId: BUILD_ID }),
      createLifecycle: () => ({
        initialize: async () => {},
        shutdown: async () => {
          throw new Error('PRIVATE_SHUTDOWN_DETAIL');
        }
      })
    }),
    {
      code: 'RESIDENT_PROVISIONING_FAILED',
      message: 'RESIDENT_PROVISIONING_FAILED'
    }
  );
  assert.equal(exitCodeFor({ code: 'RESIDENT_PROVISIONING_FAILED' }), 73);
});

test('serve and provision entrypoints reject the other operation before lifecycle or server creation', async (t) => {
  const fixture = createFixture(t);
  let lifecycleCalls = 0;
  let serverCalls = 0;
  await assert.rejects(
    startDaemon({
      argv: provisionArgv(fixture),
      verifyIntegrity: () => ({ buildId: BUILD_ID }),
      createLifecycle: () => {
        lifecycleCalls += 1;
      },
      createServer: () => {
        serverCalls += 1;
      }
    }),
    { code: 'RESIDENT_DAEMON_CONFIGURATION_INVALID' }
  );
  await assert.rejects(
    provisionResident({
      argv: serveArgv(fixture),
      verifyIntegrity: () => ({ buildId: BUILD_ID }),
      createLifecycle: () => {
        lifecycleCalls += 1;
      }
    }),
    { code: 'RESIDENT_DAEMON_CONFIGURATION_INVALID' }
  );
  assert.equal(lifecycleCalls, 0);
  assert.equal(serverCalls, 0);
});

test('provisioning rejects unsafe existing protected roots without repair', async (t) => {
  for (const key of ['rootPath', 'witnessRootPath', 'memoryBodyRootPath']) {
    await t.test(`${key} mode`, async (inner) => {
      const fixture = createFixture(inner);
      chmodSync(fixture[key], 0o750);
      let lifecycleCalls = 0;
      await assert.rejects(
        provisionResident({
          argv: provisionArgv(fixture),
          verifyIntegrity: () => ({ buildId: BUILD_ID }),
          createLifecycle: () => {
            lifecycleCalls += 1;
          }
        }),
        {
          code: 'RESIDENT_PROVISIONING_ROOT_REJECTED',
          message: 'RESIDENT_PROVISIONING_ROOT_REJECTED'
        }
      );
      assert.equal(lifecycleCalls, 0);
    });
  }

  await t.test('symlinked root or ancestor', async (inner) => {
    const fixture = createFixture(inner);
    const target = path.join(fixture.quarantine, 'actual-witness');
    const alias = path.join(fixture.quarantine, 'aliased-witness');
    mkdirSync(target, { mode: 0o700 });
    symlinkSync(target, alias);
    const aliasedFixture = { ...fixture, witnessRootPath: alias };
    await assert.rejects(
      provisionResident({
        argv: provisionArgv(aliasedFixture),
        verifyIntegrity: () => ({ buildId: BUILD_ID }),
        createLifecycle: () => {
          throw new Error('LIFECYCLE_MUST_NOT_BE_CREATED');
        }
      }),
      { code: 'RESIDENT_PROVISIONING_ROOT_REJECTED' }
    );
  });
});

test('authority file accepts only stable owner 0600 O_NOFOLLOW canonical UTF-8 JSON', async (t) => {
  await t.test('pretty or trailing JSON', async (inner) => {
    await assertAuthorityRejected(inner, `${JSON.stringify(
      JSON.parse(canonicalAuthority()),
      null,
      2
    )}\n`);
  });
  await t.test('wrong key order', async (inner) => {
    await assertAuthorityRejected(inner, JSON.stringify({
      residentId: 'resident:LOCAL_OWNER_SESSION_V1:jenn',
      provisioningId: 'provisioning:SELFTEST:ONE-SHOT',
      protocol: 'MMR0_GENESIS_PROVISIONING_V1',
      authorityId: 'authority:SELFTEST:ONE-SHOT'
    }));
  });
  await t.test('extra key', async (inner) => {
    await assertAuthorityRejected(inner, canonicalAuthority({ extra: false }));
  });
  await t.test('missing key', async (inner) => {
    await assertAuthorityRejected(inner, JSON.stringify({
      authorityId: 'authority:SELFTEST:ONE-SHOT',
      protocol: 'MMR0_GENESIS_PROVISIONING_V1',
      residentId: 'resident:LOCAL_OWNER_SESSION_V1:jenn'
    }));
  });
  await t.test('wrong protocol', async (inner) => {
    await assertAuthorityRejected(inner, canonicalAuthority({
      protocol: 'MMR0_GENESIS_PROVISIONING_V2'
    }));
  });
  await t.test('non-canonical token', async (inner) => {
    await assertAuthorityRejected(inner, canonicalAuthority({
      authorityId: 'authority:has whitespace'
    }));
  });
  await t.test('UTF-8 BOM', async (inner) => {
    await assertAuthorityRejected(inner, Buffer.concat([
      Buffer.from([0xef, 0xbb, 0xbf]),
      Buffer.from(canonicalAuthority(), 'utf8')
    ]));
  });
  await t.test('invalid UTF-8', async (inner) => {
    await assertAuthorityRejected(inner, Buffer.from([0xc3, 0x28]));
  });
  await t.test('empty file', async (inner) => {
    await assertAuthorityRejected(inner, Buffer.alloc(0));
  });
  await t.test('oversize', async (inner) => {
    await assertAuthorityRejected(inner, Buffer.alloc(4097, 0x61));
  });
  await t.test('0644 mode', async (inner) => {
    await assertAuthorityRejected(inner, canonicalAuthority(), (fixture) => {
      chmodSync(fixture.authorityFilePath, 0o644);
    });
  });
  await t.test('hard link', async (inner) => {
    await assertAuthorityRejected(inner, canonicalAuthority(), (fixture) => {
      linkSync(
        fixture.authorityFilePath,
        path.join(fixture.quarantine, 'authority-hardlink.json')
      );
    });
  });
  await t.test('final symlink', async (inner) => {
    const fixture = createFixture(inner);
    const target = path.join(fixture.quarantine, 'authority-target.json');
    writeFileSync(target, canonicalAuthority(), { mode: 0o600 });
    chmodSync(target, 0o600);
    rmSync(fixture.authorityFilePath);
    symlinkSync(target, fixture.authorityFilePath);
    let lifecycleCalls = 0;
    await assert.rejects(
      provisionResident({
        argv: provisionArgv(fixture),
        verifyIntegrity: () => ({ buildId: BUILD_ID }),
        createLifecycle: () => {
          lifecycleCalls += 1;
        }
      }),
      { code: 'RESIDENT_PROVISIONING_AUTHORITY_REJECTED' }
    );
    assert.equal(lifecycleCalls, 0);
  });
  await t.test('symlinked ancestor', async (inner) => {
    const fixture = createFixture(inner);
    const actual = path.join(fixture.quarantine, 'actual-authority-directory');
    const alias = path.join(fixture.quarantine, 'authority-directory-alias');
    mkdirSync(actual, { mode: 0o700 });
    const target = path.join(actual, 'genesis-authority.json');
    writeFileSync(target, canonicalAuthority(), { mode: 0o600 });
    chmodSync(target, 0o600);
    symlinkSync(actual, alias);
    const aliasedFixture = {
      ...fixture,
      authorityFilePath: path.join(alias, 'genesis-authority.json')
    };
    await assert.rejects(
      provisionResident({
        argv: provisionArgv(aliasedFixture),
        verifyIntegrity: () => ({ buildId: BUILD_ID }),
        createLifecycle: () => {
          throw new Error('LIFECYCLE_MUST_NOT_BE_CREATED');
        }
      }),
      { code: 'RESIDENT_PROVISIONING_AUTHORITY_REJECTED' }
    );
  });
});
