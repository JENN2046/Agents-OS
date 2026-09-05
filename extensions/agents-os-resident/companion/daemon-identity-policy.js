'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { fixedError } = require('./constants');
const { parseManifest, verifyCompanionIntegrity } = require('./integrity');

const IDENTITY_PATH = '/etc/agents-os-resident/daemon-identity.json';
const SOCKET_PATH = '/run/agents-os-resident/control.sock';
const HELPER_NAME = 'resident-peer-credentials';
const POLICY_SCHEMA = 'agents-os-resident.daemon-identity.v1';
const POLICY_KEYS = ['schema', 'daemonUid', 'clientUid', 'socketGid',
  'packageRoot', 'nodeBinary', 'buildId'].sort();

function reject() { throw fixedError('RESIDENT_DAEMON_IDENTITY_UNTRUSTED'); }

function validId(value) {
  return Number.isSafeInteger(value) && value > 0 && value < 0xffffffff;
}

function absolute(value) {
  return typeof value === 'string' && value.startsWith('/') && value !== '/'
    && path.normalize(value) === value && !/[\0\r\n]/u.test(value);
}

// Public installation metadata, never a secret or a user setting.
function parseIdentityPolicy(bytes) {
  if (!Buffer.isBuffer(bytes) || bytes.length === 0 || bytes.length > 8192) reject();
  let value;
  try { value = JSON.parse(bytes.toString('utf8')); } catch { reject(); }
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || JSON.stringify(Object.keys(value).sort()) !== JSON.stringify(POLICY_KEYS)
    || value.schema !== POLICY_SCHEMA
    || !validId(value.daemonUid) || !validId(value.clientUid)
    || !validId(value.socketGid) || value.daemonUid === value.clientUid
    || !absolute(value.packageRoot) || !absolute(value.nodeBinary)
    || !/^sha256:[0-9a-f]{64}$/u.test(value.buildId)) reject();
  return Object.freeze(value);
}

// Check every ancestor: a root-owned leaf beneath a writable home is not a
// trust anchor. The host UID cannot race any accepted ancestor.
function requireRootOwnedPath(absolutePath, kind, { stat = fs.lstatSync } = {}) {
  if (!absolute(absolutePath)) reject();
  const parts = absolutePath.split('/').filter(Boolean);
  let current = '/';
  for (let index = -1; index < parts.length; index += 1) {
    if (index >= 0) current = path.join(current, parts[index]);
    let metadata;
    try { metadata = stat(current); } catch { reject(); }
    const leaf = index === parts.length - 1;
    if (metadata.isSymbolicLink() || metadata.uid !== 0
      || (metadata.mode & 0o022) !== 0
      || (leaf && kind === 'file'
        ? !metadata.isFile() || metadata.nlink !== 1
        : !metadata.isDirectory())) reject();
  }
}

function requirePolicyRole(policy, role, uid = process.getuid?.()) {
  if (role === 'client' ? uid !== policy.clientUid
    : role === 'daemon' ? uid !== policy.daemonUid : true) reject();
}

function requireProtectedStatePath(root, daemonUid, { stat = fs.lstatSync } = {}) {
  if (!absolute(root) || !validId(daemonUid)) reject();
  const parts = root.split('/').filter(Boolean);
  let current = '/';
  for (let index = -1; index < parts.length; index += 1) {
    if (index >= 0) current = path.join(current, parts[index]);
    let metadata;
    try { metadata = stat(current); } catch { reject(); }
    if (metadata.isSymbolicLink() || !metadata.isDirectory()
      || ![0, daemonUid].includes(metadata.uid) || (metadata.mode & 0o022) !== 0
      || (index === parts.length - 1
        && (metadata.uid !== daemonUid || (metadata.mode & 0o7777) !== 0o700))) reject();
  }
}

function loadDaemonIdentityPolicy({ role = 'client' } = {}) {
  try {
    requireRootOwnedPath(IDENTITY_PATH, 'file');
    const descriptor = fs.openSync(IDENTITY_PATH,
      fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
    let policy;
    try {
      const metadata = fs.fstatSync(descriptor);
      if (!metadata.isFile() || metadata.uid !== 0 || metadata.nlink !== 1
        || (metadata.mode & 0o7777) !== 0o644
        || metadata.size < 1 || metadata.size > 8192) reject();
      policy = parseIdentityPolicy(fs.readFileSync(descriptor));
    } finally { fs.closeSync(descriptor); }
    requirePolicyRole(policy, role);
    requireRootOwnedPath(policy.packageRoot, 'directory');
    requireRootOwnedPath(policy.nodeBinary, 'file');
    const manifestPath = path.join(policy.packageRoot, 'companion-integrity.json');
    requireRootOwnedPath(manifestPath, 'file');
    const manifest = parseManifest(fs.readFileSync(manifestPath));
    if (manifest.buildId !== policy.buildId
      || !manifest.files.some((file) => file.path === HELPER_NAME)) reject();
    for (const file of manifest.files) {
      requireRootOwnedPath(path.join(policy.packageRoot, file.path), 'file');
    }
    const helper = fs.lstatSync(path.join(policy.packageRoot, HELPER_NAME));
    if ((helper.mode & 0o111) === 0 || (helper.mode & 0o6000) !== 0) reject();
    verifyCompanionIntegrity({ packageRoot: policy.packageRoot, manifestPath });
    return policy;
  } catch (error) {
    if (error?.code === 'RESIDENT_DAEMON_IDENTITY_UNTRUSTED') throw error;
    throw fixedError('RESIDENT_DAEMON_IDENTITY_UNAVAILABLE');
  }
}

module.exports = Object.freeze({
  HELPER_NAME, IDENTITY_PATH, POLICY_SCHEMA, SOCKET_PATH,
  loadDaemonIdentityPolicy, parseIdentityPolicy, requirePolicyRole,
  requireRootOwnedPath, requireProtectedStatePath
});
