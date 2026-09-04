'use strict';

const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const {
  chmodSync,
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  renameSync,
  rmSync,
  symlinkSync,
  unlinkSync,
  writeFileSync
} = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { Worker } = require('node:worker_threads');

const {
  BODY_DESCRIPTOR_SCHEMA,
  BODY_FORMAT,
  BODY_PUBLICATION_RECEIPT_SCHEMA,
  MAX_MEMORY_BODY_BYTES,
  MemoryBodyWriter,
  createMemoryBodyWriter
} = require('../companion/memory-body-writer');

const IDENTITY = `resident:v1:${'4'.repeat(64)}`;
const MEMORY = `memory:v1:${'7'.repeat(64)}`;
const SENTINEL_TEXT = 'SENTINEL_RAW_MEMORY_BODY_MUST_NOT_ESCAPE_6d2f';
const BODY = Buffer.from(
  `# ${SENTINEL_TEXT}\r\n\r\nExact UTF-8 bytes: 雪 / cafe\u0301`,
  'utf8'
);
// Frozen against Rust memory::body_locator/body_relative_path test material.
const RUST_LOCATOR_GOLDEN = Object.freeze({
  bodyDigest:
    '109342665fc73b177bc168304cb87fbc8f3c5abe0c87ce8984ae37fbacc29a68',
  identityDigest:
    '0844f1b5ad9ad01390ad6a67d8cf30da26bdb37870be8e410567ba2383442de8',
  memoryDigest:
    '8dd22b810169f8ef3c30beee190c873535f6d8699157902cb99e49d2f1cb4fac'
});

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

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value === null
    || typeof value !== 'object'
    || Object.getPrototypeOf(value) !== Object.prototype) return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonicalize(value[key])])
  );
}

function fixture(t) {
  const parent = mkdtempSync(path.join(tmpdir(), 'memory-body-writer-'));
  const bodyRoot = path.join(parent, 'private-body-root');
  const residentRoot = path.join(parent, 'resident-root');
  mkdirSync(bodyRoot, { mode: 0o700 });
  mkdirSync(residentRoot, { mode: 0o700 });
  t.after(() => rmSync(parent, { force: true, recursive: true }));
  return { bodyRoot, parent, residentRoot };
}

function writerConfig(roots) {
  return {
    bodyRoot: roots.bodyRoot,
    expectedIdentityOpaqueId: IDENTITY,
    residentRoot: roots.residentRoot
  };
}

function expectedLocation(body = BODY) {
  const identityDigest = digestText(
    'agents-os.local-owner.memory-body-identity.v1',
    IDENTITY
  );
  const memoryDigest = digestText(
    'agents-os.local-owner.memory-body-memory-id.v1',
    MEMORY
  );
  const bodyDigest = sha256(body);
  return {
    bodyDigest,
    bodyRef: `memory-body:v1:${identityDigest}:${memoryDigest}:${bodyDigest}`,
    identityDigest,
    memoryDigest
  };
}

function mode(filePath) {
  return lstatSync(filePath).mode & 0o777;
}

function captureError(action) {
  try {
    action();
  } catch (error) {
    return error;
  }
  assert.fail('expected a fixed publication error');
}

function assertFixedLowDisclosure(error, code, secrets) {
  assert.equal(error.code, code);
  assert.equal(error.message, code);
  const surfaces = [
    error.code,
    error.message,
    JSON.stringify(error),
    JSON.stringify({ code: error.code, message: error.message })
  ].join('\n');
  for (const secret of secrets) {
    assert.equal(surfaces.includes(secret), false);
  }
}

function publishInWorker(roots, operationRef) {
  const source = String.raw`
    'use strict';
    const { parentPort, workerData } = require('node:worker_threads');
    const { MemoryBodyWriter } = require(workerData.modulePath);
    const writer = new MemoryBodyWriter(workerData.roots);
    let outcome;
    try {
      const result = writer.publish({
        body: Buffer.from(workerData.bodyBase64, 'base64'),
        memoryId: workerData.memoryId,
        operationRef: workerData.operationRef
      });
      outcome = { code: null, ok: true, receiptId: result.receipt.receiptId };
    } catch (error) {
      outcome = { code: error.code, ok: false, receiptId: null };
    } finally {
      writer.close();
    }
    parentPort.postMessage(outcome);
  `;
  return new Promise((resolve, reject) => {
    const worker = new Worker(source, {
      eval: true,
      workerData: {
        bodyBase64: BODY.toString('base64'),
        memoryId: MEMORY,
        modulePath: path.resolve(
          __dirname,
          '../companion/memory-body-writer.js'
        ),
        operationRef,
        roots: writerConfig(roots)
      }
    });
    let delivered = false;
    worker.once('message', (message) => {
      delivered = true;
      resolve(message);
    });
    worker.once('error', reject);
    worker.once('exit', (code) => {
      if (!delivered && code !== 0) {
        reject(new Error(`worker exited with code ${code}`));
      }
    });
  });
}

test('publishes exact bytes with the Rust-compatible locator, protected modes, and a non-authoritative receipt', (t) => {
  const roots = fixture(t);
  const writer = createMemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  const operationRef = `${SENTINEL_TEXT}:${roots.bodyRoot}`;

  const result = writer.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef
  });
  const location = expectedLocation();
  assert.deepEqual({
    bodyDigest: location.bodyDigest,
    identityDigest: location.identityDigest,
    memoryDigest: location.memoryDigest
  }, RUST_LOCATOR_GOLDEN);
  const bodyPath = path.join(
    roots.bodyRoot,
    location.identityDigest,
    location.memoryDigest,
    `${location.bodyDigest}.body`
  );

  assert.deepEqual(result.descriptor, {
    bodyByteLength: BODY.length,
    bodyFormat: BODY_FORMAT,
    bodyRef: location.bodyRef,
    bodySha256: `sha256:${location.bodyDigest}`,
    schema: BODY_DESCRIPTOR_SCHEMA
  });
  const receiptMaterial = {
    authoritative: false,
    bodyByteLength: BODY.length,
    bodyRef: location.bodyRef,
    bodySha256: `sha256:${location.bodyDigest}`,
    current: false,
    identityDomainRef:
      `memory-body-identity:v1:${location.identityDigest}`,
    memoryId: MEMORY,
    operationRefDigest: `sha256:${digestText(
      'agents-os.local-owner.memory-body-operation-ref.v1',
      operationRef
    )}`,
    publicationStatus: 'PUBLISHED_NON_CURRENT',
    schema: BODY_PUBLICATION_RECEIPT_SCHEMA,
    verificationStatus: 'UNVERIFIED_WRITER_RECEIPT'
  };
  const expectedReceiptId = `memory-body-publication:v1:${domainDigest(
    'agents-os.local-owner.memory-body-publication-receipt.v1',
    Buffer.from(JSON.stringify(canonicalize(receiptMaterial)), 'utf8')
  )}`;
  assert.deepEqual(result.receipt, {
    receiptId: expectedReceiptId,
    ...receiptMaterial
  });
  assert.equal(Object.isFrozen(result), true);
  assert.equal(Object.isFrozen(result.descriptor), true);
  assert.equal(Object.isFrozen(result.receipt), true);

  assert.deepEqual(readFileSync(bodyPath), BODY);
  assert.equal(mode(path.join(roots.bodyRoot, location.identityDigest)), 0o700);
  assert.equal(mode(path.join(
    roots.bodyRoot,
    location.identityDigest,
    location.memoryDigest
  )), 0o700);
  assert.equal(mode(bodyPath), 0o600);
  assert.equal(lstatSync(bodyPath).nlink, 1);
  assert.equal(lstatSync(bodyPath).uid, process.geteuid());
  assert.deepEqual(readdirSync(roots.bodyRoot), [location.identityDigest]);
  assert.deepEqual(readdirSync(path.dirname(bodyPath)), [
    `${location.bodyDigest}.body`
  ]);

  const serialized = JSON.stringify(result);
  for (const secret of [
    SENTINEL_TEXT,
    roots.bodyRoot,
    roots.residentRoot,
    bodyPath,
    operationRef
  ]) {
    assert.equal(serialized.includes(secret), false);
  }
});

test('uses create-new semantics and never overwrites an exact duplicate body revision', (t) => {
  const roots = fixture(t);
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  const input = {
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:duplicate:1'
  };
  writer.publish(input);
  const location = expectedLocation();
  const bodyPath = path.join(
    roots.bodyRoot,
    location.identityDigest,
    location.memoryDigest,
    `${location.bodyDigest}.body`
  );
  const before = lstatSync(bodyPath, { bigint: true });

  const error = captureError(() => writer.publish({
    ...input,
    operationRef: 'operation:synthetic:memory-body:duplicate:2'
  }));
  assertFixedLowDisclosure(error, 'MEMORY_BODY_PUBLICATION_CONFLICT', [
    SENTINEL_TEXT,
    roots.bodyRoot,
    roots.residentRoot,
    bodyPath
  ]);
  const after = lstatSync(bodyPath, { bigint: true });
  assert.equal(after.ino, before.ino);
  assert.equal(after.size, before.size);
  assert.deepEqual(readFileSync(bodyPath), BODY);
});

test('a pre-publication file-sync failure exposes no final leaf and the same digest can retry', (t) => {
  const roots = fixture(t);
  const location = expectedLocation();
  const memoryDirectory = path.join(
    roots.bodyRoot,
    location.identityDigest,
    location.memoryDigest
  );
  const bodyPath = path.join(
    memoryDirectory,
    `${location.bodyDigest}.body`
  );
  const modulePath = require.resolve('../companion/memory-body-writer');
  const originalCachedModule = require.cache[modulePath];
  const nodeFs = require('node:fs');
  const originalFsyncSync = nodeFs.fsyncSync;
  let injected = false;
  nodeFs.fsyncSync = (fd) => {
    if (!injected && nodeFs.fstatSync(fd).isFile()) {
      injected = true;
      const error = new Error('synthetic file sync failure');
      error.code = 'EIO';
      throw error;
    }
    return originalFsyncSync(fd);
  };

  let FailingWriter;
  try {
    delete require.cache[modulePath];
    ({ MemoryBodyWriter: FailingWriter } = require(modulePath));
  } finally {
    nodeFs.fsyncSync = originalFsyncSync;
    require.cache[modulePath] = originalCachedModule;
  }
  const failingWriter = new FailingWriter(writerConfig(roots));
  t.after(() => failingWriter.close());
  const error = captureError(() => failingWriter.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:sync-failure'
  }));
  assert.equal(injected, true);
  assertFixedLowDisclosure(error, 'MEMORY_BODY_PUBLICATION_UNAVAILABLE', [
    SENTINEL_TEXT,
    roots.bodyRoot,
    roots.residentRoot,
    bodyPath
  ]);
  assert.equal(existsSync(bodyPath), false);
  assert.deepEqual(readdirSync(memoryDirectory), []);

  const retryWriter = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => retryWriter.close());
  retryWriter.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:sync-failure-retry'
  });
  assert.deepEqual(readFileSync(bodyPath), BODY);
  assert.deepEqual(readdirSync(memoryDirectory), [
    `${location.bodyDigest}.body`
  ]);
});

test('a post-link directory-sync failure returns unavailable without rewriting the complete final leaf', (t) => {
  const roots = fixture(t);
  const location = expectedLocation();
  const bodyPath = path.join(
    roots.bodyRoot,
    location.identityDigest,
    location.memoryDigest,
    `${location.bodyDigest}.body`
  );
  const modulePath = require.resolve('../companion/memory-body-writer');
  const originalCachedModule = require.cache[modulePath];
  const nodeFs = require('node:fs');
  const originalFsyncSync = nodeFs.fsyncSync;
  let fileSynced = false;
  let injected = false;
  nodeFs.fsyncSync = (fd) => {
    const stat = nodeFs.fstatSync(fd);
    if (stat.isFile()) fileSynced = true;
    if (fileSynced && stat.isDirectory() && !injected) {
      injected = true;
      const error = new Error('synthetic directory sync failure');
      error.code = 'EIO';
      throw error;
    }
    return originalFsyncSync(fd);
  };

  let FailingWriter;
  try {
    delete require.cache[modulePath];
    ({ MemoryBodyWriter: FailingWriter } = require(modulePath));
  } finally {
    nodeFs.fsyncSync = originalFsyncSync;
    require.cache[modulePath] = originalCachedModule;
  }
  const failingWriter = new FailingWriter(writerConfig(roots));
  t.after(() => failingWriter.close());
  const error = captureError(() => failingWriter.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:directory-sync-failure'
  }));
  assert.equal(injected, true);
  assertFixedLowDisclosure(error, 'MEMORY_BODY_PUBLICATION_UNAVAILABLE', [
    SENTINEL_TEXT,
    roots.bodyRoot,
    roots.residentRoot,
    bodyPath
  ]);
  const beforeRetry = lstatSync(bodyPath, { bigint: true });
  assert.equal(beforeRetry.nlink, 1n);
  assert.deepEqual(readFileSync(bodyPath), BODY);

  const retryWriter = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => retryWriter.close());
  const retryError = captureError(() => retryWriter.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:directory-sync-retry'
  }));
  assertFixedLowDisclosure(retryError, 'MEMORY_BODY_PUBLICATION_CONFLICT', [
    SENTINEL_TEXT,
    roots.bodyRoot,
    roots.residentRoot,
    bodyPath
  ]);
  const afterRetry = lstatSync(bodyPath, { bigint: true });
  assert.equal(afterRetry.ino, beforeRetry.ino);
  assert.equal(afterRetry.nlink, 1n);
  assert.deepEqual(readFileSync(bodyPath), BODY);
  assert.deepEqual(readdirSync(path.dirname(bodyPath)), [
    `${location.bodyDigest}.body`
  ]);
});

test('an unrelated private crash-residue temp inode does not block the same digest publication', (t) => {
  const roots = fixture(t);
  const location = expectedLocation();
  const identityDirectory = path.join(
    roots.bodyRoot,
    location.identityDigest
  );
  const memoryDirectory = path.join(
    identityDirectory,
    location.memoryDigest
  );
  mkdirSync(identityDirectory, { mode: 0o700 });
  mkdirSync(memoryDirectory, { mode: 0o700 });
  const residueLeaf = [
    `.${location.bodyDigest}`,
    'a'.repeat(64),
    'body.tmp'
  ].join('.');
  const residuePath = path.join(memoryDirectory, residueLeaf);
  const residueBytes = Buffer.from(`partial:${SENTINEL_TEXT}`, 'utf8');
  writeFileSync(residuePath, residueBytes, { flag: 'wx', mode: 0o600 });

  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  writer.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:crash-residue-retry'
  });
  const bodyPath = path.join(
    memoryDirectory,
    `${location.bodyDigest}.body`
  );
  assert.deepEqual(readFileSync(bodyPath), BODY);
  assert.equal(lstatSync(bodyPath).nlink, 1);
  assert.deepEqual(readFileSync(residuePath), residueBytes);
  assert.deepEqual(readdirSync(memoryDirectory).sort(), [
    residueLeaf,
    `${location.bodyDigest}.body`
  ].sort());
});

test('does not overwrite a preplanted wrong file or a final-leaf symlink', (t) => {
  const location = expectedLocation();
  const prepareTarget = (roots) => {
    const identityDirectory = path.join(
      roots.bodyRoot,
      location.identityDigest
    );
    const memoryDirectory = path.join(
      identityDirectory,
      location.memoryDigest
    );
    mkdirSync(identityDirectory, { mode: 0o700 });
    mkdirSync(memoryDirectory, { mode: 0o700 });
    return path.join(memoryDirectory, `${location.bodyDigest}.body`);
  };

  const roots = fixture(t);
  const wrongTarget = prepareTarget(roots);
  const wrongBytes = Buffer.from(`wrong:${SENTINEL_TEXT}`, 'utf8');
  writeFileSync(wrongTarget, wrongBytes, { flag: 'wx', mode: 0o600 });
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  assertFixedLowDisclosure(captureError(() => writer.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:wrong-preplant'
  })), 'MEMORY_BODY_PUBLICATION_CONFLICT', [
    SENTINEL_TEXT,
    roots.bodyRoot,
    wrongTarget
  ]);
  assert.deepEqual(readFileSync(wrongTarget), wrongBytes);

  const secondRoots = fixture(t);
  const linkTarget = prepareTarget(secondRoots);
  const outsideTarget = path.join(secondRoots.parent, 'outside-final-body');
  const outsideBytes = Buffer.from(`outside:${SENTINEL_TEXT}`, 'utf8');
  writeFileSync(outsideTarget, outsideBytes, { flag: 'wx', mode: 0o600 });
  symlinkSync(outsideTarget, linkTarget, 'file');
  const secondWriter = new MemoryBodyWriter(writerConfig(secondRoots));
  t.after(() => secondWriter.close());
  assertFixedLowDisclosure(captureError(() => secondWriter.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:leaf-symlink'
  })), 'MEMORY_BODY_PUBLICATION_CONFLICT', [
    SENTINEL_TEXT,
    secondRoots.bodyRoot,
    linkTarget,
    outsideTarget
  ]);
  assert.equal(lstatSync(linkTarget).isSymbolicLink(), true);
  assert.deepEqual(readFileSync(outsideTarget), outsideBytes);
});

test('allows only one of two concurrent identical body publications', async (t) => {
  const roots = fixture(t);
  const outcomes = await Promise.all([
    publishInWorker(roots, 'operation:synthetic:memory-body:concurrent:1'),
    publishInWorker(roots, 'operation:synthetic:memory-body:concurrent:2')
  ]);
  assert.equal(outcomes.filter((outcome) => outcome.ok).length, 1);
  assert.deepEqual(
    outcomes.filter((outcome) => !outcome.ok).map((outcome) => outcome.code),
    ['MEMORY_BODY_PUBLICATION_CONFLICT']
  );
  const location = expectedLocation();
  const bodyPath = path.join(
    roots.bodyRoot,
    location.identityDigest,
    location.memoryDigest,
    `${location.bodyDigest}.body`
  );
  assert.deepEqual(readFileSync(bodyPath), BODY);
  assert.equal(mode(bodyPath), 0o600);
  assert.equal(lstatSync(bodyPath).nlink, 1);
  assert.deepEqual(readdirSync(path.dirname(bodyPath)), [
    `${location.bodyDigest}.body`
  ]);
});

test('rejects a same-UID leaf replacement between durable close and final reopen', (t) => {
  const roots = fixture(t);
  const location = expectedLocation();
  const bodyPath = path.join(
    roots.bodyRoot,
    location.identityDigest,
    location.memoryDigest,
    `${location.bodyDigest}.body`
  );
  const replacement = Buffer.alloc(BODY.length, 0x58);
  Buffer.from(SENTINEL_TEXT, 'utf8').copy(replacement);
  const modulePath = require.resolve('../companion/memory-body-writer');
  const originalCachedModule = require.cache[modulePath];
  const nodeFs = require('node:fs');
  const originalCloseSync = nodeFs.closeSync;
  let replaced = false;
  nodeFs.closeSync = (fd) => {
    let regularFile = false;
    try {
      regularFile = nodeFs.fstatSync(fd).isFile();
    } catch {
      // The real close below preserves the module's fixed-error behavior.
    }
    originalCloseSync(fd);
    if (regularFile && !replaced) {
      unlinkSync(bodyPath);
      writeFileSync(bodyPath, replacement, { flag: 'wx', mode: 0o600 });
      replaced = true;
    }
  };

  let RaceCheckedWriter;
  try {
    delete require.cache[modulePath];
    ({ MemoryBodyWriter: RaceCheckedWriter } = require(modulePath));
  } finally {
    nodeFs.closeSync = originalCloseSync;
    require.cache[modulePath] = originalCachedModule;
  }
  const writer = new RaceCheckedWriter(writerConfig(roots));
  t.after(() => writer.close());
  const error = captureError(() => writer.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:replace-race'
  }));
  assert.equal(replaced, true);
  assertFixedLowDisclosure(error, 'MEMORY_BODY_PUBLICATION_REJECTED', [
    SENTINEL_TEXT,
    roots.bodyRoot,
    roots.residentRoot,
    bodyPath
  ]);
  assert.deepEqual(readFileSync(bodyPath), replacement);
});

test('rejects symlink roots, parent aliases, and same or nested Resident roots', (t) => {
  const roots = fixture(t);
  const bodyRootLink = path.join(roots.parent, 'body-root-link');
  const parentAlias = path.join(roots.parent, 'parent-alias');
  symlinkSync(roots.bodyRoot, bodyRootLink, 'dir');
  symlinkSync(roots.parent, parentAlias, 'dir');

  for (const config of [
    {
      bodyRoot: bodyRootLink,
      expectedIdentityOpaqueId: IDENTITY,
      residentRoot: roots.residentRoot
    },
    {
      bodyRoot: path.join(parentAlias, path.basename(roots.bodyRoot)),
      expectedIdentityOpaqueId: IDENTITY,
      residentRoot: roots.residentRoot
    },
    {
      bodyRoot: roots.bodyRoot,
      expectedIdentityOpaqueId: IDENTITY,
      residentRoot: roots.bodyRoot
    }
  ]) {
    const error = captureError(() => new MemoryBodyWriter(config));
    assertFixedLowDisclosure(error, 'MEMORY_BODY_WRITER_ROOT_REJECTED', [
      SENTINEL_TEXT,
      roots.bodyRoot,
      roots.residentRoot,
      bodyRootLink,
      parentAlias
    ]);
  }

  chmodSync(roots.residentRoot, 0o755);
  assertFixedLowDisclosure(captureError(() => new MemoryBodyWriter(
    writerConfig(roots)
  )), 'MEMORY_BODY_WRITER_ROOT_REJECTED', [roots.residentRoot]);
  chmodSync(roots.residentRoot, 0o700);

  const residentAncestor = path.join(roots.parent, 'resident-ancestor');
  const nestedBody = path.join(residentAncestor, 'nested-body');
  mkdirSync(residentAncestor, { mode: 0o700 });
  mkdirSync(nestedBody, { mode: 0o700 });
  assertFixedLowDisclosure(captureError(() => new MemoryBodyWriter({
    bodyRoot: nestedBody,
    expectedIdentityOpaqueId: IDENTITY,
    residentRoot: residentAncestor
  })), 'MEMORY_BODY_WRITER_ROOT_REJECTED', [nestedBody, residentAncestor]);

  const bodyAncestor = path.join(roots.parent, 'body-ancestor');
  const nestedResident = path.join(bodyAncestor, 'nested-resident');
  mkdirSync(bodyAncestor, { mode: 0o700 });
  mkdirSync(nestedResident, { mode: 0o700 });
  assertFixedLowDisclosure(captureError(() => new MemoryBodyWriter({
    bodyRoot: bodyAncestor,
    expectedIdentityOpaqueId: IDENTITY,
    residentRoot: nestedResident
  })), 'MEMORY_BODY_WRITER_ROOT_REJECTED', [bodyAncestor, nestedResident]);
});

test('does not follow identity or memory-directory symlinks and does not write through aliases', (t) => {
  const roots = fixture(t);
  const location = expectedLocation();
  const outsideIdentity = path.join(roots.parent, 'outside-identity');
  mkdirSync(outsideIdentity, { mode: 0o700 });
  symlinkSync(
    outsideIdentity,
    path.join(roots.bodyRoot, location.identityDigest),
    'dir'
  );
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  const error = captureError(() => writer.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:identity-link'
  }));
  assertFixedLowDisclosure(error, 'MEMORY_BODY_PUBLICATION_REJECTED', [
    SENTINEL_TEXT,
    roots.bodyRoot,
    outsideIdentity
  ]);
  assert.deepEqual(readdirSync(outsideIdentity), []);

  const secondRoots = fixture(t);
  const identityDirectory = path.join(
    secondRoots.bodyRoot,
    location.identityDigest
  );
  const outsideMemory = path.join(secondRoots.parent, 'outside-memory');
  mkdirSync(identityDirectory, { mode: 0o700 });
  mkdirSync(outsideMemory, { mode: 0o700 });
  symlinkSync(
    outsideMemory,
    path.join(identityDirectory, location.memoryDigest),
    'dir'
  );
  const secondWriter = new MemoryBodyWriter(writerConfig(secondRoots));
  t.after(() => secondWriter.close());
  const secondError = captureError(() => secondWriter.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:memory-link'
  }));
  assertFixedLowDisclosure(
    secondError,
    'MEMORY_BODY_PUBLICATION_REJECTED',
    [SENTINEL_TEXT, secondRoots.bodyRoot, outsideMemory]
  );
  assert.deepEqual(readdirSync(outsideMemory), []);
});

test('rechecks the bound root identity and owner-only mode on every publication', (t) => {
  const roots = fixture(t);
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  chmodSync(roots.bodyRoot, 0o755);
  const error = captureError(() => writer.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:retarget-check'
  }));
  chmodSync(roots.bodyRoot, 0o700);
  assertFixedLowDisclosure(error, 'MEMORY_BODY_WRITER_ROOT_REJECTED', [
    SENTINEL_TEXT,
    roots.bodyRoot,
    roots.residentRoot
  ]);
  assert.deepEqual(readdirSync(roots.bodyRoot), []);
});

test('rejects body-root and Resident-root inode retargeting after construction', (t) => {
  const roots = fixture(t);
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  const movedBodyRoot = path.join(roots.parent, 'moved-body-root');
  const outside = path.join(roots.parent, 'retarget-outside');
  renameSync(roots.bodyRoot, movedBodyRoot);
  mkdirSync(outside, { mode: 0o700 });
  symlinkSync(outside, roots.bodyRoot, 'dir');
  const bodyRetargetError = captureError(() => writer.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:body-root-retarget'
  }));
  assertFixedLowDisclosure(
    bodyRetargetError,
    'MEMORY_BODY_WRITER_ROOT_REJECTED',
    [SENTINEL_TEXT, roots.bodyRoot, roots.residentRoot, outside]
  );
  assert.deepEqual(readdirSync(movedBodyRoot), []);
  assert.deepEqual(readdirSync(outside), []);

  const secondRoots = fixture(t);
  const secondWriter = new MemoryBodyWriter(writerConfig(secondRoots));
  t.after(() => secondWriter.close());
  const movedResidentRoot = path.join(
    secondRoots.parent,
    'moved-resident-root'
  );
  renameSync(secondRoots.residentRoot, movedResidentRoot);
  mkdirSync(secondRoots.residentRoot, { mode: 0o700 });
  const residentRetargetError = captureError(() => secondWriter.publish({
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:resident-root-retarget'
  }));
  assertFixedLowDisclosure(
    residentRetargetError,
    'MEMORY_BODY_WRITER_ROOT_REJECTED',
    [
      SENTINEL_TEXT,
      secondRoots.bodyRoot,
      secondRoots.residentRoot,
      movedResidentRoot
    ]
  );
  assert.deepEqual(readdirSync(secondRoots.bodyRoot), []);
});

test('binds identity at trusted construction and rejects per-call identity or bounded-operation violations before placement', (t) => {
  const roots = fixture(t);
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  const base = {
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:validation'
  };
  const invalidInputs = [
    { ...base, identityOpaqueId: IDENTITY },
    { ...base, identityOpaqueId: `resident:v1:${'5'.repeat(64)}` },
    { ...base, memoryId: 'memory:v1:../../outside' },
    { ...base, memoryId: `memory:v2:${'1'.repeat(64)}` },
    { ...base, operationRef: 'operation:invalid\nline' },
    { ...base, operationRef: 'x'.repeat(201) },
    { ...base, body: SENTINEL_TEXT },
    { ...base, unexpectedPath: '../outside' }
  ];
  for (const input of invalidInputs) {
    const error = captureError(() => writer.publish(input));
    assertFixedLowDisclosure(error, 'MEMORY_BODY_PUBLICATION_REJECTED', [
      SENTINEL_TEXT,
      roots.bodyRoot,
      roots.residentRoot,
      '../outside'
    ]);
  }
  for (const expectedIdentityOpaqueId of [
    'resident:v1:../../outside',
    `resident:v1:${'A'.repeat(64)}`,
    `resident:v1:${'1'.repeat(63)}`
  ]) {
    assertFixedLowDisclosure(captureError(() => new MemoryBodyWriter({
      ...writerConfig(roots),
      expectedIdentityOpaqueId
    })), 'MEMORY_BODY_WRITER_ROOT_REJECTED', [
      SENTINEL_TEXT,
      roots.bodyRoot,
      roots.residentRoot,
      expectedIdentityOpaqueId
    ]);
  }
  const poisonedInput = {
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:poisoned-input'
  };
  Object.defineProperty(poisonedInput, 'body', {
    enumerable: true,
    get() {
      throw new Error(`${SENTINEL_TEXT}:${roots.bodyRoot}`);
    }
  });
  assertFixedLowDisclosure(
    captureError(() => writer.publish(poisonedInput)),
    'MEMORY_BODY_PUBLICATION_REJECTED',
    [SENTINEL_TEXT, roots.bodyRoot, roots.residentRoot]
  );
  assert.deepEqual(readdirSync(roots.bodyRoot), []);
  assert.equal(existsSync(path.join(roots.parent, 'outside')), false);
});

test('snapshots accessor-backed inputs once before validation and use', (t) => {
  const roots = fixture(t);
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  const values = {
    body: BODY,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:single-snapshot'
  };
  const poisoned = {
    body: Buffer.from(`changed:${SENTINEL_TEXT}`),
    memoryId: 'memory:v1:../../changed',
    operationRef: `${SENTINEL_TEXT}:${roots.bodyRoot}`
  };
  const reads = Object.fromEntries(
    Object.keys(values).map((key) => [key, 0])
  );
  const input = {};
  for (const key of Object.keys(values)) {
    Object.defineProperty(input, key, {
      enumerable: true,
      get() {
        reads[key] += 1;
        return reads[key] === 1 ? values[key] : poisoned[key];
      }
    });
  }

  const result = writer.publish(input);
  assert.deepEqual(reads, {
    body: 1,
    memoryId: 1,
    operationRef: 1
  });
  assert.equal(result.descriptor.bodyRef, expectedLocation().bodyRef);
  const serialized = JSON.stringify(result);
  assert.equal(serialized.includes(SENTINEL_TEXT), false);
  assert.equal(serialized.includes(roots.bodyRoot), false);
});

test('rejects malformed UTF-8 before publication and leaves no body artifact', (t) => {
  const roots = fixture(t);
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  const malformedUtf8 = Buffer.from([0x66, 0x6f, 0x80, 0x6f]);
  const error = captureError(() => writer.publish({
    body: malformedUtf8,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:malformed-utf8'
  }));
  assertFixedLowDisclosure(error, 'MEMORY_BODY_PUBLICATION_REJECTED', [
    roots.bodyRoot,
    roots.residentRoot
  ]);
  assert.deepEqual(readdirSync(roots.bodyRoot), []);
});

test('rejects bodies over one MiB with a fixed low-disclosure error', (t) => {
  const roots = fixture(t);
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  const oversize = Buffer.alloc(MAX_MEMORY_BODY_BYTES + 1, 0x53);
  Buffer.from(SENTINEL_TEXT).copy(oversize);
  const error = captureError(() => writer.publish({
    body: oversize,
    memoryId: MEMORY,
    operationRef: 'operation:synthetic:memory-body:oversize'
  }));
  assertFixedLowDisclosure(error, 'MEMORY_BODY_PUBLICATION_OVERSIZE', [
    SENTINEL_TEXT,
    roots.bodyRoot,
    roots.residentRoot
  ]);
  assert.deepEqual(readdirSync(roots.bodyRoot), []);
});

test('limits the module surface and serialized instance discloses no bound paths', (t) => {
  const roots = fixture(t);
  const writer = new MemoryBodyWriter(writerConfig(roots));
  t.after(() => writer.close());
  assert.equal(JSON.stringify(writer), '{}');
  assert.deepEqual(
    Object.keys(require('../companion/memory-body-writer')).sort(),
    [
      'BODY_DESCRIPTOR_SCHEMA',
      'BODY_FORMAT',
      'BODY_PUBLICATION_RECEIPT_SCHEMA',
      'MAX_MEMORY_BODY_BYTES',
      'MemoryBodyWriter',
      'createMemoryBodyWriter'
    ]
  );
  assert.equal(JSON.stringify(writer).includes(roots.bodyRoot), false);
  assert.equal(JSON.stringify(writer).includes(roots.residentRoot), false);

  const poisonedConfig = new Proxy({}, {
    getPrototypeOf() {
      throw new Error(`${SENTINEL_TEXT}:${roots.bodyRoot}`);
    }
  });
  assertFixedLowDisclosure(
    captureError(() => new MemoryBodyWriter(poisonedConfig)),
    'MEMORY_BODY_WRITER_ROOT_REJECTED',
    [SENTINEL_TEXT, roots.bodyRoot, roots.residentRoot]
  );
});
