import {
  chmodSync,
  chownSync,
  copyFileSync,
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  realpathSync,
  readFileSync,
  rmSync,
  writeFileSync
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

import { renderSystemdUnit } from './render-systemd-unit.mjs';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const require = createRequire(import.meta.url);
const { verifyCompanionIntegrity } = require('../companion/integrity');
const PREFIX = 'agents-os-resident-projection-';

function copyBoundPackage(packageRoot, integrity) {
  if (existsSync(resolve(packageRoot, 'plugin-manifest.json'))
    || integrity.files.some((file) => file.path === 'plugin-manifest.json')) {
    throw new Error('COMPANION_PROJECTION_INVALID');
  }
  for (const file of integrity.files) {
    const destination = resolve(packageRoot, file.path);
    mkdirSync(dirname(destination), { recursive: true, mode: 0o700 });
    copyFileSync(resolve(PACKAGE_ROOT, file.path), destination);
  }
  copyFileSync(
    resolve(PACKAGE_ROOT, 'companion-integrity.json'),
    resolve(packageRoot, 'companion-integrity.json')
  );
  copyFileSync(
    resolve(PACKAGE_ROOT, 'plugin-manifest.json.block'),
    resolve(packageRoot, 'plugin-manifest.json.block')
  );
}

export function runProjectionPreflight() {
  const sourceVerified = verifyCompanionIntegrity();
  const sourceIntegrity = JSON.parse(
    readFileSync(resolve(PACKAGE_ROOT, 'companion-integrity.json'), 'utf8')
  );
  if (sourceVerified.buildId !== sourceIntegrity.buildId
    || sourceVerified.packageVersion !== sourceIntegrity.packageVersion) {
    throw new Error('COMPANION_SOURCE_INTEGRITY_INVALID');
  }
  const ownedRoot = mkdtempSync(resolve(tmpdir(), PREFIX));
  chmodSync(ownedRoot, 0o700);
  const pluginRoot = resolve(ownedRoot, 'Plugin/AGENTSOSResident');
  const stateRoot = resolve(pluginRoot, 'state');
  const activationRoot = resolve(
    stateRoot,
    'agents-os-resident-local-owner-v1'
  );
  const witnessRoot = resolve(stateRoot, 'protected-witness');
  const memoryBodyRoot = resolve(stateRoot, 'private-memory-bodies');
  const unitPath = resolve(ownedRoot, 'systemd/agents-os-resident.service');

  try {
    mkdirSync(pluginRoot, { recursive: true, mode: 0o700 });
    copyBoundPackage(pluginRoot, sourceIntegrity);
    mkdirSync(stateRoot, { mode: 0o700 });
    chmodSync(stateRoot, 0o700);
    const stagedRequire = createRequire(resolve(pluginRoot, 'package.json'));
    const stagedDaemon = stagedRequire('./companion/resident-daemon.js');
    const rootArgs = [
      '--operation', 'prepare-roots',
      '--root', activationRoot,
      '--witness-root', witnessRoot,
      '--memory-body-root', memoryBodyRoot,
      '--expected-build-id', sourceIntegrity.buildId
    ];
    if ([activationRoot, witnessRoot, memoryBodyRoot]
      .some((directory) => existsSync(directory))) {
      throw new Error('COMPANION_PROJECTION_ROOTS_NOT_FRESH');
    }
    stagedDaemon.prepareResidentRoots({ argv: rootArgs });
    const firstRootIdentities = [activationRoot, witnessRoot, memoryBodyRoot]
      .map((directory) => {
        const stat = lstatSync(directory);
        if (!stat.isDirectory()
          || stat.isSymbolicLink()
          || stat.uid !== process.geteuid()
          || (stat.mode & 0o777) !== 0o700
          || realpathSync.native(directory) !== directory
          || readdirSync(directory).length !== 0) {
          throw new Error('COMPANION_PROJECTION_ROOT_PROFILE_INVALID');
        }
        return `${stat.dev}:${stat.ino}`;
      });
    if (new Set(firstRootIdentities).size !== 3) {
      throw new Error('COMPANION_PROJECTION_ROOT_TOPOLOGY_INVALID');
    }
    stagedDaemon.prepareResidentRoots({ argv: rootArgs });
    const secondRootIdentities = [activationRoot, witnessRoot, memoryBodyRoot]
      .map((directory) => {
        const stat = lstatSync(directory);
        return `${stat.dev}:${stat.ino}`;
      });
    if (JSON.stringify(secondRootIdentities) !== JSON.stringify(firstRootIdentities)) {
      throw new Error('COMPANION_PROJECTION_ROOT_IDEMPOTENCY_INVALID');
    }
    const currentUid = process.getuid();
    const daemonUid = currentUid === 0 ? 2001 : currentUid;
    const socketGid = process.getgid() === 0 ? 2002 : process.getgid();
    if (currentUid === 0) {
      // Only the fresh, empty fixture roots above acquire the synthetic UID.
      for (const directory of [activationRoot, witnessRoot, memoryBodyRoot]) {
        chownSync(directory, daemonUid, socketGid);
      }
    }
    mkdirSync(dirname(unitPath), { recursive: true, mode: 0o700 });
    const renderedUnit = renderSystemdUnit({
      daemonUid,
      clientUid: currentUid === 0 ? 2002 : daemonUid === 65534 ? 65533 : 65534,
      socketGid,
      activationRoot,
      buildId: sourceIntegrity.buildId,
      memoryBodyRoot,
      nodeBinary: process.execPath,
      pluginRoot,
      witnessRoot
    });
    writeFileSync(unitPath, renderedUnit, { flag: 'wx', mode: 0o644 });

    const staged = verifyCompanionIntegrity({ packageRoot: pluginRoot });
    const stagedAdapter = stagedRequire('./companion/adapter.js');
    if (staged.buildId !== sourceIntegrity.buildId
      || staged.packageVersion !== sourceIntegrity.packageVersion
      || typeof stagedAdapter.createResidentAdapter !== 'function'
      || !existsSync(resolve(pluginRoot, 'plugin-manifest.json.block'))
      || existsSync(resolve(pluginRoot, 'plugin-manifest.json'))
      || !existsSync(unitPath)
      || existsSync(resolve(pluginRoot, 'config.env'))
      || !renderedUnit.includes(
        `--witness-root ${witnessRoot} --memory-body-root ${memoryBodyRoot}`
      )
      || !renderedUnit.includes(`\nReadWritePaths=${activationRoot} ${memoryBodyRoot}\n`)
      || !renderedUnit.includes(
        `\nReadOnlyPaths=${pluginRoot} ${witnessRoot}\n`
      )
      || renderedUnit.includes('--continuity-evidence')
      || renderedUnit.includes('--genesis-provisioning-authority')) {
      throw new Error('COMPANION_PROJECTION_INVALID');
    }
    return Object.freeze({
      result: 'COMPANION_PROJECTION_PREFLIGHT_VERIFIED',
      runtimeUsable: false,
      installedProjectionWritten: false,
      serviceInstalled: false,
      serviceStarted: false
    });
  } finally {
    rmSync(ownedRoot, { recursive: true, force: true });
  }
}

function main(argv) {
  if (argv.length !== 1 || argv[0] !== '--check') {
    throw new Error('COMPANION_PROJECTION_ARGUMENTS_INVALID');
  }
  const result = runProjectionPreflight();
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch {
    process.stderr.write('COMPANION_PROJECTION_PREFLIGHT_FAILED\n');
    process.exit(1);
  }
}
