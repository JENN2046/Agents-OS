import { fileURLToPath } from 'node:url';

const TOOL_PATH = fileURLToPath(import.meta.url);

/**
 * This validator produced the historical second-review candidate artifacts.
 * It is deliberately fail-closed after the third independent review found
 * that its repair surface, per-finding disposition checks, and candidate-tree
 * admission were too weak for merge-readiness authority.
 *
 * The replacement is validate-pr41-merge-p2-candidate.mjs, which consumes an
 * append-only candidate identity freeze and validates the full PR surface,
 * repair delta, and each merge-blocking finding independently.
 */
export function validateSecondReviewCandidate() {
  throw new Error(
    'SECOND_REVIEW_VALIDATOR_SUPERSEDED_USE_VALIDATE_PR41_MERGE_P2_CANDIDATE'
  );
}

function main() {
  validateSecondReviewCandidate();
}

if (process.argv[1] === TOOL_PATH) {
  try {
    main();
  } catch (error) {
    process.stderr.write(
      `PR41_SECOND_REVIEW_CANDIDATE_VALIDATION_FAILED:${error.message}\n`
    );
    process.exit(2);
  }
}
