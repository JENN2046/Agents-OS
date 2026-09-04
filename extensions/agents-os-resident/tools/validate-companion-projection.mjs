import {
  chmodSync,
  copyFileSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
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
    resolve(packageRoot, 'plugin-manifest.json')
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
    for (const directory of [
      stateRoot,
      activationRoot,
      witnessRoot,
      memoryBodyRoot
    ]) {
      mkdirSync(directory, { mode: 0o700 });
      chmodSync(directory, 0o700);
    }
    mkdirSync(dirname(unitPath), { recursive: true, mode: 0o700 });
    const renderedUnit = renderSystemdUnit({
      activationRoot,
      buildId: sourceIntegrity.buildId,
      memoryBodyRoot,
      nodeBinary: process.execPath,
      pluginRoot,
      witnessRoot
    });
    writeFileSync(unitPath, renderedUnit, { flag: 'wx', mode: 0o644 });

    const staged = verifyCompanionIntegrity({ packageRoot: pluginRoot });
    const stagedRequire = createRequire(resolve(pluginRoot, 'package.json'));
    const stagedAdapter = stagedRequire('./companion/adapter.js');
    if (staged.buildId !== sourceIntegrity.buildId
      || staged.packageVersion !== sourceIntegrity.packageVersion
      || typeof stagedAdapter.createResidentAdapter !== 'function'
      || !existsSync(resolve(pluginRoot, 'plugin-manifest.json'))
      || !existsSync(unitPath)
      || existsSync(resolve(pluginRoot, 'config.env'))
      || !renderedUnit.includes(
        `--witness-root ${witnessRoot} --memory-body-root ${memoryBodyRoot}`
      )
      || !renderedUnit.includes(`ReadWritePaths=${activationRoot}`)
      || !renderedUnit.includes(
        `ReadOnlyPaths=${pluginRoot} ${witnessRoot} ${memoryBodyRoot}`
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
