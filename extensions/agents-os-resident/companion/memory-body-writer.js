'use strict';

/*
 * Daemon-private filesystem primitive. The authenticated publication handler
 * selects startup roots and binds expectedIdentityOpaqueId to fresh Presence.
 * Each publication may select only a Memory id beneath that bound identity.
 * The roots must remain mount-stable: this module rejects path and symlink
 * aliases but does not claim to authenticate callers or detect same-device bind mounts.
 * Do not re-export this filesystem primitive through a public/model API.
 * The private daemon operation accepts only body data and bound identity claims,
 * never caller-selected roots; its receipt is noncurrent and nonauthoritative.
 */

const { createHash, randomBytes } = require('node:crypto');
const { isUtf8 } = require('node:buffer');
const {
  closeSync,
  constants: fsConstants,
  fchmodSync,
  fstatSync,
  fsyncSync,
  linkSync,
  lstatSync,
  mkdirSync,
  openSync,
  readSync,
  realpathSync,
  unlinkSync,
  writeSync
} = require('node:fs');
const path = require('node:path');

const { fixedError } = require('./constants');

const BODY_DESCRIPTOR_SCHEMA = 'AGENTS_OS_MEMORY_BODY_DESCRIPTOR_V1';
const BODY_PUBLICATION_RECEIPT_SCHEMA =
  'AGENTS_OS_MEMORY_BODY_PUBLICATION_RECEIPT_V1';
const BODY_FORMAT = 'UTF8_MARKDOWN';
const MAX_MEMORY_BODY_BYTES = 1024 * 1024;
const MAX_OPERATION_REF_BYTES = 200;

const IDENTITY_DIGEST_DOMAIN =
  'agents-os.local-owner.memory-body-identity.v1';
const MEMORY_DIGEST_DOMAIN =
  'agents-os.local-owner.memory-body-memory-id.v1';
const OPERATION_REF_DIGEST_DOMAIN =
  'agents-os.local-owner.memory-body-operation-ref.v1';
const RECEIPT_DIGEST_DOMAIN =
  'agents-os.local-owner.memory-body-publication-receipt.v1';

const RESIDENT_ID = /^resident:v1:[0-9a-f]{64}$/u;
const MEMORY_ID = /^memory:v1:[0-9a-f]{64}$/u;
const HEX_DIGEST = /^[0-9a-f]{64}$/u;
const FIXED_PUBLICATION_ERRORS = new Set([
  'MEMORY_BODY_PUBLICATION_CONFLICT',
  'MEMORY_BODY_PUBLICATION_OVERSIZE',
  'MEMORY_BODY_PUBLICATION_REJECTED',
  'MEMORY_BODY_PUBLICATION_UNAVAILABLE',
  'MEMORY_BODY_WRITER_ROOT_REJECTED'
]);

const DIRECTORY_OPEN_FLAGS = fsConstants.O_RDONLY
  | fsConstants.O_DIRECTORY
  | fsConstants.O_NOFOLLOW;
const BODY_TEMP_OPEN_FLAGS = fsConstants.O_RDWR
  | fsConstants.O_CREAT
  | fsConstants.O_EXCL
  | fsConstants.O_NOFOLLOW;
const BODY_REOPEN_FLAGS = fsConstants.O_RDONLY | fsConstants.O_NOFOLLOW;
const MAX_TEMP_CREATE_ATTEMPTS = 16;

function hasFixedCode(error, code) {
  try {
    return error !== null
      && typeof error === 'object'
      && error.code === code;
  } catch {
    return false;
  }
}

function isFixedPublicationError(error) {
  try {
    return error !== null
      && typeof error === 'object'
      && FIXED_PUBLICATION_ERRORS.has(error.code);
  } catch {
    return false;
  }
}

function isPlainObject(value) {
  return value !== null
    && typeof value === 'object'
    && !Array.isArray(value)
    && (Object.getPrototypeOf(value) === Object.prototype
      || Object.getPrototypeOf(value) === null);
}

function hasExactKeys(value, expected) {
  if (!isPlainObject(value)) return false;
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length
    && actual.every((key, index) => key === wanted[index]);
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (!isPlainObject(value)) return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonicalize(value[key])])
  );
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function domainDigest(domain, bytes) {
  return sha256(Buffer.concat([
    Buffer.from(domain, 'utf8'),
    Buffer.from([0]),
    bytes
  ]));
}

function digestText(domain, value) {
  return domainDigest(domain, Buffer.from(value, 'utf8'));
}

function sameDirectoryIdentity(left, right) {
  return left.dev === right.dev && left.ino === right.ino;
}

function ownedProtectedDirectory(stat) {
  return stat.isDirectory()
    && !stat.isSymbolicLink()
    && stat.uid === BigInt(process.geteuid())
    && (stat.mode & 0o777n) === 0o700n;
}

function canonicalAbsoluteDirectory(directoryPath, requireOwnerOnly) {
  if (process.platform !== 'linux'
    || typeof directoryPath !== 'string'
    || directoryPath.length === 0
    || directoryPath.includes('\0')
    || !path.isAbsolute(directoryPath)
    || path.normalize(directoryPath) !== directoryPath) {
    throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
  }

  try {
    const before = lstatSync(directoryPath, { bigint: true });
    const canonical = realpathSync.native(directoryPath);
    if (!before.isDirectory()
      || before.isSymbolicLink()
      || canonical !== directoryPath
      || (requireOwnerOnly && !ownedProtectedDirectory(before))) {
      throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
    }

    const fd = openSync(directoryPath, DIRECTORY_OPEN_FLAGS);
    try {
      const opened = fstatSync(fd, { bigint: true });
      const after = lstatSync(directoryPath, { bigint: true });
      if (!sameDirectoryIdentity(before, opened)
        || !sameDirectoryIdentity(opened, after)
        || !after.isDirectory()
        || after.isSymbolicLink()
        || (requireOwnerOnly && !ownedProtectedDirectory(opened))) {
        throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
      }
      return { canonical, dev: opened.dev, fd, ino: opened.ino };
    } catch (error) {
      closeSync(fd);
      throw error;
    }
  } catch (error) {
    if (error?.code === 'MEMORY_BODY_WRITER_ROOT_REJECTED') throw error;
    throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
  }
}

function pathsOverlap(left, right) {
  const relative = path.relative(left, right);
  return relative === ''
    || (relative !== '..'
      && !relative.startsWith(`..${path.sep}`)
      && !path.isAbsolute(relative));
}

function validateBoundRoot(binding, requireOwnerOnly) {
  try {
    const byPath = lstatSync(binding.canonical, { bigint: true });
    const byFd = fstatSync(binding.fd, { bigint: true });
    if (realpathSync.native(binding.canonical) !== binding.canonical
      || !byPath.isDirectory()
      || byPath.isSymbolicLink()
      || !sameDirectoryIdentity(binding, byPath)
      || !sameDirectoryIdentity(binding, byFd)
      || (requireOwnerOnly
        && (!ownedProtectedDirectory(byPath)
          || !ownedProtectedDirectory(byFd)))) {
      throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
    }
  } catch (error) {
    if (error?.code === 'MEMORY_BODY_WRITER_ROOT_REJECTED') throw error;
    throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
  }
}

function procChildPath(parentFd, leaf) {
  if (!HEX_DIGEST.test(leaf)) {
    throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
  }
  return `/proc/self/fd/${parentFd}/${leaf}`;
}

function openProtectedChildDirectory(parentFd, leaf) {
  const childPath = procChildPath(parentFd, leaf);
  let created = false;
  try {
    mkdirSync(childPath, { mode: 0o700 });
    created = true;
  } catch (error) {
    if (error?.code !== 'EEXIST') {
      throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
    }
  }

  let fd;
  try {
    const before = lstatSync(childPath, { bigint: true });
    if (!before.isDirectory()
      || before.isSymbolicLink()
      || before.uid !== BigInt(process.geteuid())
      || (!created && (before.mode & 0o777n) !== 0o700n)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
    fd = openSync(childPath, DIRECTORY_OPEN_FLAGS);
    if (created) fchmodSync(fd, 0o700);
    const opened = fstatSync(fd, { bigint: true });
    const after = lstatSync(childPath, { bigint: true });
    if (!ownedProtectedDirectory(opened)
      || !ownedProtectedDirectory(after)
      || !sameDirectoryIdentity(before, opened)
      || !sameDirectoryIdentity(opened, after)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
    return fd;
  } catch (error) {
    if (fd !== undefined) {
      try {
        closeSync(fd);
      } catch {
        // The public failure remains fixed and contains no filesystem detail.
      }
    }
    if (FIXED_PUBLICATION_ERRORS.has(error?.code)) throw error;
    throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
  }
}

function validateChildDirectory(parentFd, leaf, childFd) {
  const childPath = procChildPath(parentFd, leaf);
  try {
    const byPath = lstatSync(childPath, { bigint: true });
    const byFd = fstatSync(childFd, { bigint: true });
    if (!ownedProtectedDirectory(byPath)
      || !ownedProtectedDirectory(byFd)
      || !sameDirectoryIdentity(byPath, byFd)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
  } catch (error) {
    if (error?.code === 'MEMORY_BODY_PUBLICATION_REJECTED') throw error;
    throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
  }
}

function validOperationRef(value) {
  return typeof value === 'string'
    && value.length > 0
    && value.trim() === value
    && value.normalize('NFC') === value
    && Buffer.byteLength(value, 'utf8') <= MAX_OPERATION_REF_BYTES
    && !/[\u0000-\u001f\u007f]/u.test(value);
}

function normalizePublicationInput(value) {
  try {
    if (!hasExactKeys(value, [
      'body',
      'memoryId',
      'operationRef'
    ])) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
    const body = value.body;
    const memoryId = value.memoryId;
    const operationRef = value.operationRef;
    if (!Buffer.isBuffer(body)
      || !isUtf8(body)
      || !MEMORY_ID.test(memoryId)
      || !validOperationRef(operationRef)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
    if (body.length > MAX_MEMORY_BODY_BYTES) {
      throw fixedError('MEMORY_BODY_PUBLICATION_OVERSIZE');
    }
    return Object.freeze({
      body: Buffer.from(body),
      memoryId,
      operationRef
    });
  } catch (error) {
    if (hasFixedCode(error, 'MEMORY_BODY_PUBLICATION_REJECTED')
      || hasFixedCode(error, 'MEMORY_BODY_PUBLICATION_OVERSIZE')) {
      throw error;
    }
    throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
  }
}

function finalBodyPath(memoryDirectoryFd, bodyDigest) {
  if (!HEX_DIGEST.test(bodyDigest)) {
    throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
  }
  return `/proc/self/fd/${memoryDirectoryFd}/${bodyDigest}.body`;
}

function createTemporaryBody(memoryDirectoryFd, bodyDigest) {
  for (let attempt = 0; attempt < MAX_TEMP_CREATE_ATTEMPTS; attempt += 1) {
    let nonce;
    try {
      nonce = randomBytes(32).toString('hex');
    } catch {
      throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
    }
    const temporaryPath = [
      `/proc/self/fd/${memoryDirectoryFd}/.${bodyDigest}`,
      nonce,
      'body.tmp'
    ].join('.');
    try {
      return {
        fd: openSync(temporaryPath, BODY_TEMP_OPEN_FLAGS, 0o600),
        path: temporaryPath
      };
    } catch (error) {
      if (error?.code === 'EEXIST') continue;
      throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
    }
  }
  throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
}

function validateExactOpenBody(fd, expectedDigest, expectedLength) {
  let readBuffer;
  try {
    const before = fstatSync(fd, { bigint: true });
    if (!before.isFile()
      || before.isSymbolicLink()
      || before.uid !== BigInt(process.geteuid())
      || (before.mode & 0o777n) !== 0o600n
      || before.nlink !== 1n
      || before.size !== BigInt(expectedLength)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }

    const hasher = createHash('sha256');
    readBuffer = Buffer.allocUnsafe(8192);
    let total = 0;
    for (;;) {
      const read = readSync(
        fd,
        readBuffer,
        0,
        readBuffer.length,
        total
      );
      if (read === 0) break;
      total += read;
      if (total > expectedLength || total > MAX_MEMORY_BODY_BYTES) {
        throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
      }
      hasher.update(readBuffer.subarray(0, read));
      readBuffer.fill(0, 0, read);
    }
    readBuffer.fill(0);

    const after = fstatSync(fd, { bigint: true });
    if (total !== expectedLength
      || hasher.digest('hex') !== expectedDigest
      || !sameFileRevision(before, after)
      || after.nlink !== 1n) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
    return after;
  } catch (error) {
    if (hasFixedCode(error, 'MEMORY_BODY_PUBLICATION_REJECTED')) throw error;
    throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
  } finally {
    readBuffer?.fill(0);
  }
}

function unlinkRetainedTemporaryBody(temporaryPath, fd) {
  let byPath;
  try {
    byPath = lstatSync(temporaryPath, { bigint: true });
  } catch (error) {
    if (error?.code === 'ENOENT') return false;
    throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
  }
  const retained = fstatSync(fd, { bigint: true });
  if (!byPath.isFile()
    || byPath.isSymbolicLink()
    || !sameDirectoryIdentity(byPath, retained)) {
    throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
  }
  try {
    unlinkSync(temporaryPath);
  } catch {
    throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
  }
  return true;
}

function writeExactBody(memoryDirectoryFd, bodyDigest, body) {
  const bodyPath = finalBodyPath(memoryDirectoryFd, bodyDigest);
  let temporary;
  let durable;
  let failure;
  try {
    temporary = createTemporaryBody(memoryDirectoryFd, bodyDigest);
    fchmodSync(temporary.fd, 0o600);
    const created = fstatSync(temporary.fd, { bigint: true });
    const linkedTemporary = lstatSync(temporary.path, { bigint: true });
    if (!created.isFile()
      || created.isSymbolicLink()
      || created.uid !== BigInt(process.geteuid())
      || (created.mode & 0o777n) !== 0o600n
      || created.nlink !== 1n
      || !sameDirectoryIdentity(created, linkedTemporary)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }

    let offset = 0;
    while (offset < body.length) {
      const written = writeSync(
        temporary.fd,
        body,
        offset,
        body.length - offset,
        offset
      );
      if (!Number.isSafeInteger(written) || written <= 0) {
        throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
      }
      offset += written;
    }
    fsyncSync(temporary.fd);
    const verifiedTemporary = validateExactOpenBody(
      temporary.fd,
      bodyDigest,
      body.length
    );
    const durableTemporary = lstatSync(temporary.path, { bigint: true });
    if (!sameFileRevision(verifiedTemporary, durableTemporary)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }

    try {
      linkSync(temporary.path, bodyPath);
    } catch (error) {
      if (error?.code === 'EEXIST') {
        throw fixedError('MEMORY_BODY_PUBLICATION_CONFLICT');
      }
      throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
    }
    const retainedAfterPublish = fstatSync(temporary.fd, { bigint: true });
    const published = lstatSync(bodyPath, { bigint: true });
    const temporaryLink = lstatSync(temporary.path, { bigint: true });
    if (retainedAfterPublish.nlink !== 2n
      || published.nlink !== 2n
      || temporaryLink.nlink !== 2n
      || !sameFileRevision(retainedAfterPublish, published)
      || !sameFileRevision(retainedAfterPublish, temporaryLink)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }

    // The complete final link is made durable before the private temporary
    // name is removed. A crash cannot expose a partially written final leaf.
    // A stop between link and unlink can leave final+temp with nlink=2; this
    // writer does not guess provenance or auto-clean that narrow residue.
    // The Rust verifier keeps nlink=1 mandatory and therefore fails closed.
    fsyncSync(memoryDirectoryFd);
    unlinkRetainedTemporaryBody(temporary.path, temporary.fd);
    temporary.path = undefined;
    fsyncSync(memoryDirectoryFd);

    durable = fstatSync(temporary.fd, { bigint: true });
    const durableLink = lstatSync(bodyPath, { bigint: true });
    if (!durable.isFile()
      || durable.isSymbolicLink()
      || durable.uid !== BigInt(process.geteuid())
      || (durable.mode & 0o777n) !== 0o600n
      || durable.nlink !== 1n
      || durable.size !== BigInt(body.length)
      || !sameFileRevision(durable, durableLink)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
  } catch (error) {
    failure = FIXED_PUBLICATION_ERRORS.has(error?.code)
      ? error
      : fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
  } finally {
    if (temporary?.path !== undefined) {
      try {
        const removed = unlinkRetainedTemporaryBody(
          temporary.path,
          temporary.fd
        );
        if (removed) fsyncSync(memoryDirectoryFd);
      } catch (error) {
        failure ??= FIXED_PUBLICATION_ERRORS.has(error?.code)
          ? error
          : fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
      }
      temporary.path = undefined;
    }
  }
  if (failure !== undefined) {
    if (temporary?.fd !== undefined) {
      try {
        closeSync(temporary.fd);
      } catch {
        // The fixed publication failure remains the only public error surface.
      }
    }
    throw failure;
  }
  return { durable, fd: temporary.fd };
}

function validateDurableBody(
  memoryDirectoryFd,
  bodyDigest,
  bodyFile,
  bodyLength
) {
  const bodyPath = `/proc/self/fd/${memoryDirectoryFd}/${bodyDigest}.body`;
  try {
    const byFd = fstatSync(bodyFile.fd, { bigint: true });
    const byPath = lstatSync(bodyPath, { bigint: true });
    if (!byFd.isFile()
      || byFd.isSymbolicLink()
      || byFd.uid !== BigInt(process.geteuid())
      || (byFd.mode & 0o777n) !== 0o600n
      || byFd.nlink !== 1n
      || byFd.size !== BigInt(bodyLength)
      || !sameDirectoryIdentity(byFd, byPath)
      || !sameDirectoryIdentity(byFd, bodyFile.durable)
      || byFd.size !== bodyFile.durable.size
      || byFd.mtimeNs !== bodyFile.durable.mtimeNs
      || byFd.ctimeNs !== bodyFile.durable.ctimeNs) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
  } catch (error) {
    if (hasFixedCode(error, 'MEMORY_BODY_PUBLICATION_REJECTED')) throw error;
    throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
  }
}

function sameFileRevision(left, right) {
  return sameDirectoryIdentity(left, right)
    && left.size === right.size
    && left.mtimeNs === right.mtimeNs
    && left.ctimeNs === right.ctimeNs;
}

function reopenExactBody(
  memoryDirectoryFd,
  bodyDigest,
  durable,
  bodyLength
) {
  const bodyPath = `/proc/self/fd/${memoryDirectoryFd}/${bodyDigest}.body`;
  let fd;
  let failure;
  let readBuffer;
  try {
    fd = openSync(bodyPath, BODY_REOPEN_FLAGS);
    const before = fstatSync(fd, { bigint: true });
    const linked = lstatSync(bodyPath, { bigint: true });
    if (!before.isFile()
      || before.isSymbolicLink()
      || before.uid !== BigInt(process.geteuid())
      || (before.mode & 0o777n) !== 0o600n
      || before.nlink !== 1n
      || before.size !== BigInt(bodyLength)
      || !sameDirectoryIdentity(before, linked)
      || !sameFileRevision(before, durable)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }

    const hasher = createHash('sha256');
    readBuffer = Buffer.allocUnsafe(8192);
    let total = 0;
    for (;;) {
      const read = readSync(
        fd,
        readBuffer,
        0,
        readBuffer.length,
        null
      );
      if (read === 0) break;
      total += read;
      if (total > MAX_MEMORY_BODY_BYTES) {
        throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
      }
      hasher.update(readBuffer.subarray(0, read));
      readBuffer.fill(0, 0, read);
    }
    readBuffer.fill(0);

    const after = fstatSync(fd, { bigint: true });
    const relinked = lstatSync(bodyPath, { bigint: true });
    if (total !== bodyLength
      || hasher.digest('hex') !== bodyDigest
      || !sameFileRevision(before, after)
      || !sameDirectoryIdentity(after, relinked)) {
      throw fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
    }
  } catch (error) {
    failure = hasFixedCode(error, 'MEMORY_BODY_PUBLICATION_REJECTED')
      ? error
      : fixedError('MEMORY_BODY_PUBLICATION_REJECTED');
  }
  readBuffer?.fill(0);
  if (fd !== undefined) {
    try {
      closeSync(fd);
    } catch {
      failure ??= fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
    }
  }
  if (failure !== undefined) throw failure;
}

function publicationResult({
  bodyDigest,
  bodyLength,
  identityDigest,
  memoryDigest,
  memoryId,
  operationRefDigest
}) {
  const bodyRef = [
    'memory-body',
    'v1',
    identityDigest,
    memoryDigest,
    bodyDigest
  ].join(':');
  const descriptor = Object.freeze({
    bodyByteLength: bodyLength,
    bodyFormat: BODY_FORMAT,
    bodyRef,
    bodySha256: `sha256:${bodyDigest}`,
    schema: BODY_DESCRIPTOR_SCHEMA
  });
  const receiptMaterial = {
    authoritative: false,
    bodyByteLength: bodyLength,
    bodyRef,
    bodySha256: `sha256:${bodyDigest}`,
    current: false,
    identityDomainRef: `memory-body-identity:v1:${identityDigest}`,
    memoryId,
    operationRefDigest: `sha256:${operationRefDigest}`,
    publicationStatus: 'PUBLISHED_NON_CURRENT',
    schema: BODY_PUBLICATION_RECEIPT_SCHEMA,
    verificationStatus: 'UNVERIFIED_WRITER_RECEIPT'
  };
  const receiptId = `memory-body-publication:v1:${domainDigest(
    RECEIPT_DIGEST_DOMAIN,
    Buffer.from(JSON.stringify(canonicalize(receiptMaterial)), 'utf8')
  )}`;
  const receipt = Object.freeze({ receiptId, ...receiptMaterial });
  return Object.freeze({ descriptor, receipt });
}

class MemoryBodyWriter {
  #bodyRoot;

  #closed = false;

  #identityOpaqueId;

  #residentRoot;

  constructor(config) {
    let normalizedConfig;
    try {
      if (!hasExactKeys(config, [
        'bodyRoot',
        'expectedIdentityOpaqueId',
        'residentRoot'
      ])) {
        throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
      }
      normalizedConfig = {
        bodyRoot: config.bodyRoot,
        expectedIdentityOpaqueId: config.expectedIdentityOpaqueId,
        residentRoot: config.residentRoot
      };
      if (!RESIDENT_ID.test(normalizedConfig.expectedIdentityOpaqueId)) {
        throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
      }
    } catch (error) {
      if (hasFixedCode(error, 'MEMORY_BODY_WRITER_ROOT_REJECTED')) throw error;
      throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
    }

    let bodyRoot;
    let residentRoot;
    try {
      bodyRoot = canonicalAbsoluteDirectory(normalizedConfig.bodyRoot, true);
      residentRoot = canonicalAbsoluteDirectory(
        normalizedConfig.residentRoot,
        true
      );
      if (sameDirectoryIdentity(bodyRoot, residentRoot)
        || pathsOverlap(bodyRoot.canonical, residentRoot.canonical)
        || pathsOverlap(residentRoot.canonical, bodyRoot.canonical)) {
        throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
      }
    } catch (error) {
      if (bodyRoot !== undefined) {
        try {
          closeSync(bodyRoot.fd);
        } catch {
          // Constructor errors remain fixed and low disclosure.
        }
      }
      if (residentRoot !== undefined) {
        try {
          closeSync(residentRoot.fd);
        } catch {
          // Constructor errors remain fixed and low disclosure.
        }
      }
      if (error?.code === 'MEMORY_BODY_WRITER_ROOT_REJECTED') throw error;
      throw fixedError('MEMORY_BODY_WRITER_ROOT_REJECTED');
    }

    this.#bodyRoot = bodyRoot;
    this.#identityOpaqueId = normalizedConfig.expectedIdentityOpaqueId;
    this.#residentRoot = residentRoot;
    Object.freeze(this);
  }

  close() {
    if (this.#closed) return;
    this.#closed = true;
    let failed = false;
    for (const binding of [this.#bodyRoot, this.#residentRoot]) {
      try {
        closeSync(binding.fd);
      } catch {
        failed = true;
      }
    }
    if (failed) throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
  }

  publish(value) {
    let input;
    try {
      input = normalizePublicationInput(value);
      return this.#publishExact(input);
    } catch (error) {
      if (isFixedPublicationError(error)) throw error;
      throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
    } finally {
      input?.body.fill(0);
    }
  }

  #publishExact(input) {
    if (this.#closed) {
      throw fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
    }

    validateBoundRoot(this.#bodyRoot, true);
    validateBoundRoot(this.#residentRoot, true);

    const identityDigest = digestText(
      IDENTITY_DIGEST_DOMAIN,
      this.#identityOpaqueId
    );
    const memoryDigest = digestText(MEMORY_DIGEST_DOMAIN, input.memoryId);
    const operationRefDigest = digestText(
      OPERATION_REF_DIGEST_DOMAIN,
      input.operationRef
    );
    const bodyDigest = sha256(input.body);

    let identityDirectoryFd;
    let memoryDirectoryFd;
    let bodyFile;
    let failure;
    try {
      identityDirectoryFd = openProtectedChildDirectory(
        this.#bodyRoot.fd,
        identityDigest
      );
      memoryDirectoryFd = openProtectedChildDirectory(
        identityDirectoryFd,
        memoryDigest
      );
      bodyFile = writeExactBody(memoryDirectoryFd, bodyDigest, input.body);

      fsyncSync(memoryDirectoryFd);
      fsyncSync(identityDirectoryFd);
      fsyncSync(this.#bodyRoot.fd);

      validateChildDirectory(
        identityDirectoryFd,
        memoryDigest,
        memoryDirectoryFd
      );
      validateChildDirectory(
        this.#bodyRoot.fd,
        identityDigest,
        identityDirectoryFd
      );
      validateBoundRoot(this.#bodyRoot, true);
      validateBoundRoot(this.#residentRoot, true);
      validateDurableBody(
        memoryDirectoryFd,
        bodyDigest,
        bodyFile,
        input.body.length
      );
      closeSync(bodyFile.fd);
      bodyFile.fd = undefined;
      reopenExactBody(
        memoryDirectoryFd,
        bodyDigest,
        bodyFile.durable,
        input.body.length
      );
    } catch (error) {
      failure = FIXED_PUBLICATION_ERRORS.has(error?.code)
        ? error
        : fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
    } finally {
      for (const fd of [
        bodyFile?.fd,
        memoryDirectoryFd,
        identityDirectoryFd
      ]) {
        if (fd === undefined) continue;
        try {
          closeSync(fd);
        } catch {
          failure ??= fixedError('MEMORY_BODY_PUBLICATION_UNAVAILABLE');
        }
      }
    }
    if (failure !== undefined) throw failure;

    return publicationResult({
      bodyDigest,
      bodyLength: input.body.length,
      identityDigest,
      memoryDigest,
      memoryId: input.memoryId,
      operationRefDigest
    });
  }
}

function createMemoryBodyWriter(config) {
  return new MemoryBodyWriter(config);
}

module.exports = Object.freeze({
  BODY_DESCRIPTOR_SCHEMA,
  BODY_FORMAT,
  BODY_PUBLICATION_RECEIPT_SCHEMA,
  MAX_MEMORY_BODY_BYTES,
  MemoryBodyWriter,
  createMemoryBodyWriter
});
