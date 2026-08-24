'use strict';

const { createHash } = require('node:crypto');
const {
  lstatSync,
  readFileSync,
  realpathSync
} = require('node:fs');
const path = require('node:path');

const { fixedError } = require('./constants');
const { BUILD_ID, hasExactKeys, isPlainObject } = require('./protocol');

const MANIFEST_SCHEMA = 'agents-os-resident.companion-integrity.v1';
const MANIFEST_KEYS = Object.freeze([
  'buildId',
  'files',
  'packageVersion',
  'schemaVersion'
]);
const FILE_KEYS = Object.freeze(['byteLength', 'path', 'sha256']);
const SHA256 = /^[0-9a-f]{64}$/;

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function canonicalJson(value) {
  const canonicalize = (input) => {
    if (Array.isArray(input)) {
      return input.map(canonicalize);
    }
    if (isPlainObject(input)) {
      return Object.fromEntries(
        Object.keys(input).sort().map((key) => [key, canonicalize(input[key])])
      );
    }
    return input;
  };
  return Buffer.from(JSON.stringify(canonicalize(value)), 'utf8');
}

function safeRelativePath(value) {
  return typeof value === 'string'
    && value.length > 0
    && value.normalize('NFC') === value
    && !value.startsWith('/')
    && !value.includes('\\')
    && !value.includes('\0')
    && value.split('/').every((segment) => segment !== ''
      && segment !== '.'
      && segment !== '..');
}

function parseManifest(bytes) {
  let manifest;
  try {
    manifest = JSON.parse(bytes.toString('utf8'));
  } catch {
    throw fixedError('RESIDENT_INTEGRITY_UNAVAILABLE');
  }
  if (!hasExactKeys(manifest, MANIFEST_KEYS)
    || manifest.schemaVersion !== MANIFEST_SCHEMA
    || typeof manifest.packageVersion !== 'string'
    || manifest.packageVersion.length === 0
    || !BUILD_ID.test(manifest.buildId)
    || !Array.isArray(manifest.files)
    || manifest.files.length === 0) {
    throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
  }

  let previousPath = null;
  const seen = new Set();
  for (const file of manifest.files) {
    if (!hasExactKeys(file, FILE_KEYS)
      || !safeRelativePath(file.path)
      || !Number.isSafeInteger(file.byteLength)
      || file.byteLength < 0
      || !SHA256.test(file.sha256)
      || seen.has(file.path)
      || (previousPath !== null
        && Buffer.compare(Buffer.from(previousPath), Buffer.from(file.path)) >= 0)) {
      throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
    }
    seen.add(file.path);
    previousPath = file.path;
  }

  const calculatedBuildId = `sha256:${sha256(canonicalJson({
    schemaVersion: manifest.schemaVersion,
    packageVersion: manifest.packageVersion,
    files: manifest.files
  }))}`;
  if (calculatedBuildId !== manifest.buildId) {
    throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
  }
  return manifest;
}

function verifyCompanionIntegrity({
  packageRoot = path.resolve(__dirname, '..'),
  manifestPath = path.resolve(packageRoot, 'companion-integrity.json')
} = {}) {
  let canonicalRoot;
  let manifest;
  try {
    canonicalRoot = realpathSync(packageRoot);
    const rootStat = lstatSync(canonicalRoot);
    if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) {
      throw fixedError('RESIDENT_INTEGRITY_UNAVAILABLE');
    }
    manifest = parseManifest(readFileSync(manifestPath));
  } catch (error) {
    if (error?.code?.startsWith?.('RESIDENT_')) {
      throw error;
    }
    throw fixedError('RESIDENT_INTEGRITY_UNAVAILABLE');
  }

  for (const file of manifest.files) {
    const absolute = path.resolve(canonicalRoot, file.path);
    const relative = path.relative(canonicalRoot, absolute).split(path.sep).join('/');
    if (relative !== file.path || relative.startsWith('../')) {
      throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
    }
    let stat;
    let bytes;
    try {
      stat = lstatSync(absolute);
      if (!stat.isFile() || stat.isSymbolicLink() || stat.nlink !== 1) {
        throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
      }
      bytes = readFileSync(absolute);
    } catch (error) {
      if (error?.code?.startsWith?.('RESIDENT_')) {
        throw error;
      }
      throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
    }
    if (bytes.length !== file.byteLength || sha256(bytes) !== file.sha256) {
      throw fixedError('RESIDENT_INTEGRITY_MISMATCH');
    }
  }

  return Object.freeze({
    buildId: manifest.buildId,
    packageVersion: manifest.packageVersion
  });
}

module.exports = Object.freeze({
  MANIFEST_SCHEMA,
  canonicalJson,
  parseManifest,
  safeRelativePath,
  sha256,
  verifyCompanionIntegrity
});
