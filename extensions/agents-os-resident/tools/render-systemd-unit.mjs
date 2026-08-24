import {
  chmodSync,
  lstatSync,
  readFileSync,
  renameSync,
  writeFileSync
} from 'node:fs';
import { dirname, isAbsolute, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const TEMPLATE_PATH = resolve(
  PACKAGE_ROOT,
  'systemd/agents-os-resident.service.template'
);
const INTEGRITY_PATH = resolve(PACKAGE_ROOT, 'companion-integrity.json');
const REQUIRED_PLACEHOLDERS = Object.freeze([
  '@@ACTIVATION_ROOT@@',
  '@@BUILD_ID@@',
  '@@CONTINUITY_EVIDENCE_JSON@@',
  '@@GENESIS_PROVISIONING_AUTHORITY_JSON@@',
  '@@NODE_BINARY@@',
  '@@PLUGIN_ROOT@@'
]);

function isPlainObject(value) {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false;
  }
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function serializedJsonObject(value, name) {
  if (typeof value !== 'string' || value.length === 0 || value.includes('\0')) {
    throw new Error(`SYSTEMD_RENDER_INPUT_INVALID:${name}`);
  }
  let parsed;
  try {
    parsed = JSON.parse(value);
  } catch {
    throw new Error(`SYSTEMD_RENDER_INPUT_INVALID:${name}`);
  }
  if (!isPlainObject(parsed)) {
    throw new Error(`SYSTEMD_RENDER_INPUT_INVALID:${name}`);
  }
  return value;
}

function safeAbsolute(value) {
  return typeof value === 'string'
    && value.length > 0
    && isAbsolute(value)
    && normalize(value) === value
    && !/[\0\r\n\t ]/.test(value);
}

function parseIntegrity() {
  const manifest = JSON.parse(readFileSync(INTEGRITY_PATH, 'utf8'));
  if (!/^sha256:[0-9a-f]{64}$/.test(manifest.buildId)) {
    throw new Error('SYSTEMD_RENDER_INTEGRITY_INVALID');
  }
  return manifest;
}

export function renderSystemdUnit({
  continuityEvidenceJson,
  genesisProvisioningAuthorityJson,
  nodeBinary,
  pluginRoot,
  activationRoot,
  buildId
}) {
  if (!safeAbsolute(nodeBinary)
    || !safeAbsolute(pluginRoot)
    || !safeAbsolute(activationRoot)
    || !/^sha256:[0-9a-f]{64}$/.test(buildId)
    || !activationRoot.startsWith(`${pluginRoot}/state/`)) {
    throw new Error('SYSTEMD_RENDER_INPUT_INVALID');
  }
  serializedJsonObject(continuityEvidenceJson, 'CONTINUITY_EVIDENCE_JSON');
  serializedJsonObject(
    genesisProvisioningAuthorityJson,
    'GENESIS_PROVISIONING_AUTHORITY_JSON'
  );
  const templateStat = lstatSync(TEMPLATE_PATH);
  if (!templateStat.isFile() || templateStat.isSymbolicLink()) {
    throw new Error('SYSTEMD_TEMPLATE_INVALID');
  }
  let rendered = readFileSync(TEMPLATE_PATH, 'utf8');
  for (const placeholder of REQUIRED_PLACEHOLDERS) {
    if (!rendered.includes(placeholder)) {
      throw new Error('SYSTEMD_TEMPLATE_INVALID');
    }
  }
  rendered = rendered
    .replaceAll('@@CONTINUITY_EVIDENCE_JSON@@', continuityEvidenceJson)
    .replaceAll('@@GENESIS_PROVISIONING_AUTHORITY_JSON@@', genesisProvisioningAuthorityJson)
    .replaceAll('@@NODE_BINARY@@', nodeBinary)
    .replaceAll('@@PLUGIN_ROOT@@', pluginRoot)
    .replaceAll('@@ACTIVATION_ROOT@@', activationRoot)
    .replaceAll('@@BUILD_ID@@', buildId);
  if (REQUIRED_PLACEHOLDERS.some((placeholder) => rendered.includes(placeholder))
    || !rendered.includes('RestrictAddressFamilies=AF_UNIX')
    || !rendered.includes('IPAddressDeny=any')
    || !rendered.includes('StandardOutput=null')
    || !rendered.includes('StandardError=null')
    || rendered.includes('PartOf=')
    || rendered.includes('BindsTo=')
    || rendered.includes('MemoryDenyWriteExecute=')
    || rendered.includes('SystemCallFilter=')) {
    throw new Error('SYSTEMD_RENDER_OUTPUT_INVALID');
  }
  return `${rendered.trimEnd()}\n`;
}

function parseArgs(argv) {
  if (argv.length === 1 && argv[0] === '--check') {
    return Object.freeze({ check: true });
  }
  const parsed = {};
  for (let index = 0; index < argv.length; index += 2) {
    parsed[argv[index]] = argv[index + 1];
  }
  if (!Object.hasOwn(parsed, '--activation-root')
    || !Object.hasOwn(parsed, '--continuity-evidence')
    || !Object.hasOwn(parsed, '--genesis-provisioning-authority')
    || !Object.hasOwn(parsed, '--node')
    || !Object.hasOwn(parsed, '--output')
    || !Object.hasOwn(parsed, '--plugin-root')) {
    throw new Error('SYSTEMD_RENDER_ARGUMENTS_INVALID');
  }
  return Object.freeze({
    activationRoot: parsed['--activation-root'],
    continuityEvidenceJson: parsed['--continuity-evidence'],
    genesisProvisioningAuthorityJson: parsed['--genesis-provisioning-authority'],
    nodeBinary: parsed['--node'],
    output: parsed['--output'],
    pluginRoot: parsed['--plugin-root']
  });
}

function main(argv) {
  const args = parseArgs(argv);
  const integrity = parseIntegrity();
  if (args.check) {
    renderSystemdUnit({
      continuityEvidenceJson: '{"availability":"AVAILABLE","evidenceId":"evidence:check","protocol":"MMR0_CONTINUITY_EVIDENCE_V1","state":"EMPTY","witnessId":"witness:check"}',
      genesisProvisioningAuthorityJson: '{"authorityId":"authority:check","protocol":"MMR0_GENESIS_PROVISIONING_V1","provisioningId":"provisioning:check","residentId":"resident:LOCAL_OWNER_SESSION_V1:jenn"}',
      nodeBinary: process.execPath,
      pluginRoot: PACKAGE_ROOT,
      activationRoot: resolve(PACKAGE_ROOT, 'state/agents-os-resident-local-owner-v1'),
      buildId: integrity.buildId
    });
    process.stdout.write('SYSTEMD_UNIT_TEMPLATE_VERIFIED\n');
    return;
  }
  if (!safeAbsolute(args.output)) {
    throw new Error('SYSTEMD_RENDER_OUTPUT_PATH_INVALID');
  }
  const rendered = renderSystemdUnit({
    continuityEvidenceJson: args.continuityEvidenceJson,
    genesisProvisioningAuthorityJson: args.genesisProvisioningAuthorityJson,
    nodeBinary: args.nodeBinary,
    pluginRoot: args.pluginRoot,
    activationRoot: args.activationRoot,
    buildId: integrity.buildId
  });
  const temporary = `${args.output}.tmp-${process.pid}`;
  writeFileSync(temporary, rendered, { flag: 'wx', mode: 0o644 });
  chmodSync(temporary, 0o644);
  renameSync(temporary, args.output);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch {
    process.stderr.write('SYSTEMD_UNIT_RENDER_FAILED\n');
    process.exit(1);
  }
}
