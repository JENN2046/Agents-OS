import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = resolve(dirname(TOOL_PATH), '..');
const WORKTREE_ROOT = resolve(PACKAGE_ROOT, '../..');
const COMMIT = /^[0-9a-f]{40}$/u;

function argument(argv, name) {
  const index = argv.indexOf(name);
  if (index < 0 || index + 1 >= argv.length) throw new Error(`MISSING:${name}`);
  return argv[index + 1];
}

function git(args, options = {}) {
  return spawnSync('git', args, {
    cwd: WORKTREE_ROOT,
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
    ...options
  });
}

export function parseClippyRun(run) {
  if (run.error !== undefined
    || !Number.isInteger(run.status)
    || run.signal !== null && run.signal !== undefined
    || typeof run.stdout !== 'string') {
    throw new Error('CLIPPY_COMPARISON_INFRASTRUCTURE_FAILURE');
  }
  const messages = [];
  for (const line of run.stdout.split('\n')) {
    if (line.length === 0) continue;
    try {
      messages.push(JSON.parse(line));
    } catch {
      throw new Error('CLIPPY_COMPARISON_INFRASTRUCTURE_FAILURE');
    }
  }
  const buildFinished = messages.filter(
    (message) => message.reason === 'build-finished'
  );
  const compilerReached = messages.some((message) => (
    message.reason === 'compiler-message'
    || message.reason === 'compiler-artifact'
  ));
  const counts = new Map();
  let nonLintCompilerError = false;
  for (const message of messages) {
    if (message.reason !== 'compiler-message'
      || message.message?.level !== 'error') {
      continue;
    }
    const diagnosticCode = message.message.code?.code;
    const lintDiagnostic = typeof diagnosticCode === 'string'
      && /^(?:clippy::[a-z0-9_]+|[a-z][a-z0-9_]*)$/u.test(diagnosticCode);
    if (!lintDiagnostic) {
      nonLintCompilerError = true;
      continue;
    }
    const primary = message.message.spans?.find((span) => span.is_primary);
    const identity = JSON.stringify({
      code: diagnosticCode,
      file: primary?.file_name ?? null,
      label: primary?.label ?? null,
      message: message.message.message,
      target: message.target?.name ?? null
    });
    counts.set(identity, (counts.get(identity) ?? 0) + 1);
  }
  const errorCount = [...counts.values()].reduce((sum, value) => sum + value, 0);
  const successfulBuild = run.status === 0
    && buildFinished.length === 1
    && buildFinished[0].success === true;
  const expectedLintFailure = run.status !== 0
    && buildFinished.length === 1
    && buildFinished[0].success === false
    && errorCount > 0
    && !nonLintCompilerError;
  if (!compilerReached
    || buildFinished.length !== 1
    || nonLintCompilerError
    || (!successfulBuild && !expectedLintFailure)) {
    throw new Error('CLIPPY_COMPARISON_INFRASTRUCTURE_FAILURE');
  }
  return {
    classification: successfulBuild
      ? 'SUCCESS'
      : 'LINT_DIAGNOSTICS_PRESENT',
    counts,
    exitCode: run.status
  };
}

function diagnosticCounts(packageRoot, targetRoot) {
  const run = spawnSync(
    'cargo',
    ['clippy', '--all-targets', '--message-format=json', '--', '-D', 'warnings'],
    {
      cwd: packageRoot,
      encoding: 'utf8',
      env: { ...process.env, CARGO_TARGET_DIR: targetRoot },
      maxBuffer: 128 * 1024 * 1024
    }
  );
  return parseClippyRun(run);
}

function addedDiagnostics(base, candidate) {
  const added = [];
  for (const [identity, count] of candidate.counts) {
    const extra = count - (base.counts.get(identity) ?? 0);
    if (extra > 0) added.push({ count: extra, identity: JSON.parse(identity) });
  }
  return added;
}

export function compareParsedClippyRuns(baseRun, candidateRun) {
  const base = parseClippyRun(baseRun);
  const candidate = parseClippyRun(candidateRun);
  const addedFindings = addedDiagnostics(base, candidate);
  return Object.freeze({
    addedFindings,
    base,
    candidate,
    result: addedFindings.length === 0
      ? 'CLIPPY_PREDECESSOR_CANDIDATE_DIFF_PASS'
      : 'CLIPPY_PREDECESSOR_CANDIDATE_DIFF_FAIL'
  });
}

export function compareClippyDiagnostics(baseCommit, candidateCommit) {
  if (!COMMIT.test(baseCommit) || !COMMIT.test(candidateCommit)) {
    throw new Error('COMMIT_INVALID');
  }
  const head = git(['rev-parse', 'HEAD']).stdout.trim();
  if (head !== candidateCommit
    || git(['status', '--porcelain']).stdout.length !== 0) {
    throw new Error('CANDIDATE_WORKTREE_NOT_CLEAN_OR_EXACT');
  }
  const ownedRoot = mkdtempSync(resolve(tmpdir(), 'resident-r2-clippy-'));
  const baseWorktree = resolve(ownedRoot, 'base');
  try {
    const added = git(['worktree', 'add', '--detach', baseWorktree, baseCommit]);
    if (added.status !== 0) throw new Error('BASE_WORKTREE_ADD_FAILED');
    const base = diagnosticCounts(
      resolve(baseWorktree, 'extensions/agents-os-resident'),
      resolve(ownedRoot, 'target-base')
    );
    const candidate = diagnosticCounts(
      PACKAGE_ROOT,
      resolve(ownedRoot, 'target-candidate')
    );
    const addedFindings = addedDiagnostics(base, candidate);
    return Object.freeze({
      result: addedFindings.length === 0
        ? 'CLIPPY_PREDECESSOR_CANDIDATE_DIFF_PASS'
        : 'CLIPPY_PREDECESSOR_CANDIDATE_DIFF_FAIL',
      baseCommit,
      candidateCommit,
      baseDiagnosticCount: [...base.counts.values()]
        .reduce((sum, value) => sum + value, 0),
      baseRunClassification: base.classification,
      candidateDiagnosticCount: [...candidate.counts.values()]
        .reduce((sum, value) => sum + value, 0),
      candidateRunClassification: candidate.classification,
      addedFindings
    });
  } finally {
    git(['worktree', 'remove', '--force', baseWorktree]);
    rmSync(ownedRoot, { recursive: true, force: true });
  }
}

function main(argv) {
  const result = compareClippyDiagnostics(
    argument(argv, '--base'),
    argument(argv, '--candidate')
  );
  process.stdout.write(`${JSON.stringify(result)}\n`);
  if (result.addedFindings.length !== 0) process.exit(1);
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`CLIPPY_DIFF_FAILED:${error.message}\n`);
    process.exit(2);
  }
}
