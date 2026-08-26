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
export const PREFLIGHT_CONTINUITY_EVIDENCE_JSON =
  '{"availability":"AVAILABLE","evidenceId":"evidence:projection-preflight","protocol":"MMR0_CONTINUITY_EVIDENCE_V1","state":"EMPTY","witnessId":"witness:projection-preflight"}';
export const PREFLIGHT_GENESIS_PROVISIONING_AUTHORITY_JSON =
  '{"authorityId":"authority:projection-preflight","protocol":"MMR0_GENESIS_PROVISIONING_V1","provisioningId":"provisioning:projection-preflight","residentId":"resident:LOCAL_OWNER_SESSION_V1:jenn"}';

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
  const activationRoot = resolve(
    pluginRoot,
    'state/agents-os-resident-local-owner-v1'
  );
  const unitPath = resolve(ownedRoot, 'systemd/agents-os-resident.service');

  try {
    mkdirSync(pluginRoot, { recursive: true, mode: 0o700 });
    copyBoundPackage(pluginRoot, sourceIntegrity);
    mkdirSync(activationRoot, { recursive: true, mode: 0o700 });
    chmodSync(resolve(pluginRoot, 'state'), 0o700);
    chmodSync(activationRoot, 0o700);
    mkdirSync(dirname(unitPath), { recursive: true, mode: 0o700 });
    writeFileSync(unitPath, renderSystemdUnit({
      continuityEvidenceJson: PREFLIGHT_CONTINUITY_EVIDENCE_JSON,
      genesisProvisioningAuthorityJson:
        PREFLIGHT_GENESIS_PROVISIONING_AUTHORITY_JSON,
      nodeBinary: process.execPath,
      pluginRoot,
      activationRoot,
      buildId: sourceIntegrity.buildId
    }), { flag: 'wx', mode: 0o644 });

    const staged = verifyCompanionIntegrity({ packageRoot: pluginRoot });
    const stagedRequire = createRequire(resolve(pluginRoot, 'package.json'));
    const stagedAdapter = stagedRequire('./companion/adapter.js');
    if (staged.buildId !== sourceIntegrity.buildId
      || staged.packageVersion !== sourceIntegrity.packageVersion
      || typeof stagedAdapter.createResidentAdapter !== 'function'
      || !existsSync(resolve(pluginRoot, 'plugin-manifest.json'))
      || !existsSync(unitPath)
      || existsSync(resolve(pluginRoot, 'config.env'))) {
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
