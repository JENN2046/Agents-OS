import { createHash } from 'node:crypto';
import { TextDecoder } from 'node:util';

export const CONTRACT_SCHEMA =
  'MMR-0-TD2-R4-P6-PR41-VALIDATOR-ADMISSION-AUTHORITY-v0.4';
export const CONTRACT_VERSION = 'v0.4';
export const CONTRACT_DOMAIN = 'MMR0_PR41_VALIDATOR_ADMISSION_AUTHORITY_V1';
export const BINDING_DOMAIN = 'MMR0_PR41_FINDING_EVIDENCE_BINDING_V2';
export const BASE_COMMIT = 'd2d564a5f29a2dcd5aa8e2a3562039a2ab19bbf9';
export const PREDECESSOR_COMMIT =
  '693c2a31f49b00471a97f8123a2782952463f226';
export const ARTIFACT_ROLE = Object.freeze({
  contract: 'VALIDATOR_ADMISSION_AUTHORITY_CONTRACT',
  disposition: 'VALIDATOR_ADMISSION_REPAIR_DISPOSITION',
  evidence: 'VALIDATOR_ADMISSION_REPAIR_EVIDENCE',
  freeze: 'VALIDATOR_ADMISSION_CANDIDATE_IDENTITY_FREEZE'
});
export const AUTHORITY_MODE = Object.freeze({
  current: 'CURRENT_CANDIDATE_AUTHORITY',
  precommit: 'PRECOMMIT_VALIDATION_ONLY'
});
export const FINDING_IDS = Object.freeze([
  'MMR0-P6-PR41-R2-P2-003',
  'MMR0-P6-PR41-R2-P2-004',
  'MMR0-P6-PR41-THIRD-R1-NEW-P2-003',
  'MMR0-P6-PR41-VALIDATOR-QA-R1-NEW-P2-001'
]);
export const FINDING_STATUS = Object.freeze({
  'MMR0-P6-PR41-R2-P2-003': 'INDEPENDENTLY_CLOSED',
  'MMR0-P6-PR41-R2-P2-004': 'REMAINS_FROZEN_CLOSED',
  'MMR0-P6-PR41-THIRD-R1-NEW-P2-003':
    'REPAIRED_PENDING_INDEPENDENT_REVIEW',
  'MMR0-P6-PR41-VALIDATOR-QA-R1-NEW-P2-001':
    'REPAIRED_PENDING_INDEPENDENT_REVIEW'
});
export const MODIFICATION_POLICY = Object.freeze({
  'MMR0-P6-PR41-R2-P2-003': 'FROZEN',
  'MMR0-P6-PR41-R2-P2-004': 'FROZEN',
  'MMR0-P6-PR41-THIRD-R1-NEW-P2-003': 'REPAIR_AUTHORIZED',
  'MMR0-P6-PR41-VALIDATOR-QA-R1-NEW-P2-001': 'REPAIR_AUTHORIZED'
});
export const EVIDENCE_TYPE = Object.freeze({
  'MMR0-P6-PR41-R2-P2-003':
    'INDEPENDENT_RECOVERY_CLOSURE_REFERENCE_V1',
  'MMR0-P6-PR41-R2-P2-004':
    'FROZEN_CLIPPY_CONTROL_REFERENCE_V1',
  'MMR0-P6-PR41-THIRD-R1-NEW-P2-003':
    'VALIDATOR_TYPED_EVIDENCE_REPAIR_CONTINUITY_V1',
  'MMR0-P6-PR41-VALIDATOR-QA-R1-NEW-P2-001':
    'VALIDATOR_ADMISSION_AUTHORITY_REPAIR_V1'
});
export const REQUIRED_RECEIPT_IDS = Object.freeze([
  'D25',
  'D26',
  'MALFORMED_UTF8',
  'NULL_RESOLUTION',
  'EMPTY_RECOVERY_PARITY',
  'EMPTY_VALIDATOR_ATTACKS',
  'EMPTY_CANONICAL_COMPATIBILITY',
  'APPEND_ONLY_FALSE',
  'WRONG_BASE',
  'WRONG_PREDECESSOR',
  'NULL_SCOPE',
  'EVIDENCE_STRING',
  'EVIDENCE_ARRAY',
  'BOOLEAN_AS_STRING',
  'NUMBER_AS_STRING',
  'OBJECT_INSTEAD_OF_ENUM',
  'UNKNOWN_TOP_LEVEL',
  'UNKNOWN_FINDING_FIELD',
  'UNKNOWN_EVIDENCE_FIELD',
  'UNKNOWN_NESTED_SCOPE',
  'UNKNOWN_REGRESSION_FIELD',
  'UNKNOWN_TYPED_EVIDENCE_FIELD',
  'WRONG_NESTED_TYPE'
]);

export const RECEIPT_REPLAY_SPEC = Object.freeze(Object.fromEntries(
  REQUIRED_RECEIPT_IDS.map((id) => [id, Object.freeze({
    fixture_class: id,
    expected_authoritative_outcome: 'REJECT'
  })])
));

export const CANONICAL_FILE_NAMES = Object.freeze({
  contract:
    'MMR-0_TD2_R4_P6_PR41_Validator_Admission_Authority_Contract_R1.yaml',
  disposition:
    'MMR-0_TD2_R4_P6_PR41_Validator_Admission_Repair_Disposition_R1.yaml',
  evidence:
    'MMR-0_TD2_R4_P6_PR41_Validator_Admission_Repair_Adversarial_Evidence_R1.json',
  freeze:
    'MMR-0_TD2_R4_P6_PR41_Validator_Admission_Candidate_Identity_Freeze_R1.yaml',
  validator:
    'MMR-0_TD2_R4_P6_PR41_Validator_Admission_Candidate_Validator_Result_R1.json'
});

export function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function canonicalValue(value) {
  if (value === null || typeof value === 'boolean' || typeof value === 'string') {
    return value;
  }
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('CANONICAL_JSON_NONFINITE_NUMBER');
    return value;
  }
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (typeof value === 'object' && value !== undefined) {
    const output = {};
    for (const key of Object.keys(value).sort()) {
      if (value[key] === undefined) throw new Error('CANONICAL_JSON_UNDEFINED');
      output[key] = canonicalValue(value[key]);
    }
    return output;
  }
  throw new Error('CANONICAL_JSON_UNSUPPORTED_VALUE');
}

export function canonicalJson(value) {
  return JSON.stringify(canonicalValue(value));
}

export function canonicalSha256(value) {
  return sha256(Buffer.from(canonicalJson(value), 'utf8'));
}

export function jsonBytes(value) {
  return Buffer.from(`${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function strictJsonScanner(text, label) {
  let index = 0;
  function whitespace() {
    while ([' ', '\t', '\n', '\r'].includes(text[index])) index += 1;
  }
  function string() {
    if (text[index] !== '"') throw new Error(`${label}_JSON_STRING_EXPECTED`);
    const start = index;
    index += 1;
    while (index < text.length) {
      const character = text[index];
      if (character === '"') {
        index += 1;
        return JSON.parse(text.slice(start, index));
      }
      if (character === '\\') {
        index += 1;
        if (text[index] === 'u') {
          if (!/^[0-9a-fA-F]{4}$/u.test(text.slice(index + 1, index + 5))) {
            throw new Error(`${label}_JSON_ESCAPE_INVALID`);
          }
          index += 5;
          continue;
        }
        if (!/^["\\/bfnrt]$/u.test(text[index] ?? '')) {
          throw new Error(`${label}_JSON_ESCAPE_INVALID`);
        }
      } else if (character.charCodeAt(0) < 0x20) {
        throw new Error(`${label}_JSON_CONTROL_CHARACTER`);
      }
      index += 1;
    }
    throw new Error(`${label}_JSON_STRING_UNTERMINATED`);
  }
  function value() {
    whitespace();
    if (text[index] === '{') return object();
    if (text[index] === '[') return array();
    if (text[index] === '"') {
      string();
      return;
    }
    for (const literal of ['true', 'false', 'null']) {
      if (text.startsWith(literal, index)) {
        index += literal.length;
        return;
      }
    }
    const number = text.slice(index).match(
      /^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/u
    )?.[0];
    if (number) {
      index += number.length;
      return;
    }
    throw new Error(`${label}_JSON_VALUE_INVALID`);
  }
  function object() {
    index += 1;
    whitespace();
    const keys = new Set();
    if (text[index] === '}') {
      index += 1;
      return;
    }
    while (true) {
      whitespace();
      const key = string();
      if (keys.has(key)) throw new Error(`${label}_DUPLICATE_KEY:${key}`);
      keys.add(key);
      whitespace();
      if (text[index] !== ':') throw new Error(`${label}_JSON_COLON_EXPECTED`);
      index += 1;
      value();
      whitespace();
      if (text[index] === '}') {
        index += 1;
        return;
      }
      if (text[index] !== ',') throw new Error(`${label}_JSON_COMMA_EXPECTED`);
      index += 1;
    }
  }
  function array() {
    index += 1;
    whitespace();
    if (text[index] === ']') {
      index += 1;
      return;
    }
    while (true) {
      value();
      whitespace();
      if (text[index] === ']') {
        index += 1;
        return;
      }
      if (text[index] !== ',') throw new Error(`${label}_JSON_COMMA_EXPECTED`);
      index += 1;
    }
  }
  value();
  whitespace();
  if (index !== text.length) throw new Error(`${label}_JSON_TRAILING_BYTES`);
}

export function parseStrictJsonBytes(bytes, label = 'DOCUMENT') {
  let text;
  try {
    text = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.from(bytes));
  } catch {
    throw new Error(`${label}_MALFORMED_UTF8`);
  }
  strictJsonScanner(text, label);
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`${label}_NOT_CANONICAL_JSON_DOCUMENT`);
  }
}

export function assertExactKeys(object, expected, label) {
  if (!object || typeof object !== 'object' || Array.isArray(object)) {
    throw new Error(`${label}_OBJECT_REQUIRED`);
  }
  const actual = Object.keys(object).sort();
  const required = [...expected].sort();
  if (actual.length !== required.length
    || actual.some((key, index) => key !== required[index])) {
    throw new Error(`${label}_EXACT_SHAPE_INVALID`);
  }
}

function assertString(value, label) {
  if (typeof value !== 'string' || value.length === 0) {
    throw new Error(`${label}_NONEMPTY_STRING_REQUIRED`);
  }
}

function assertSha256(value, label) {
  if (typeof value !== 'string' || !/^[0-9a-f]{64}$/u.test(value)) {
    throw new Error(`${label}_SHA256_REQUIRED`);
  }
}

function assertExactArray(actual, expected, label) {
  if (!Array.isArray(actual)
    || actual.length !== expected.length
    || actual.some((value, index) => value !== expected[index])) {
    throw new Error(`${label}_EXACT_ARRAY_REQUIRED`);
  }
}

export const CONTRACT_DOCUMENT = Object.freeze({
  artifact:
    'MMR-0_TD2_R4_P6_PR41_Validator_Admission_Authority_Contract_R1',
  schema: CONTRACT_SCHEMA,
  domain: CONTRACT_DOMAIN,
  version: CONTRACT_VERSION,
  append_only: true,
  current_artifact_roles: ARTIFACT_ROLE,
  exact_document_schemas: {
    disposition: [
      'append_only', 'artifact_role', 'authority_mode', 'base_commit',
      'candidate_commit', 'candidate_tree', 'contract_sha256',
      'contract_version', 'evidence_file', 'evidence_sha256', 'findings',
      'predecessor_commit', 'schema', 'summary'
    ],
    evidence: [
      'append_only', 'artifact_role', 'attack_receipt_manifest',
      'authority_mode', 'base_commit', 'candidate_commit', 'candidate_tree',
      'canonical_compatibility', 'contract_sha256', 'contract_version',
      'findings', 'predecessor_commit', 'recovery_parity', 'regression',
      'schema', 'scope', 'validator_attacks'
    ],
    freeze: [
      'append_only', 'artifact_role', 'authority_mode', 'base_commit',
      'candidate_commit', 'candidate_tree', 'contract_sha256',
      'contract_version', 'disposition_file', 'disposition_sha256',
      'evidence_file', 'evidence_sha256', 'full_pr_surface',
      'predecessor_commit', 'repair_surface', 'schema'
    ]
  },
  finding_evidence_contracts: Object.fromEntries(FINDING_IDS.map((id) => [id, {
    evidence_type: EVIDENCE_TYPE[id],
    status: FINDING_STATUS[id]
  }])),
  semantic_binding_algorithm: {
    canonical_json: 'RECURSIVE_SORTED_OBJECT_KEYS_ARRAY_ORDER_PRESERVED_UTF8',
    domain: BINDING_DOMAIN,
    preimage_fields: [
      'domain', 'artifactRole', 'contractSha256', 'contractVersion',
      'candidateCommit', 'candidateTree', 'findingId', 'status',
      'evidenceType', 'evidence'
    ]
  },
  execution_receipt_contract: {
    supplied_receipt_trust_class: 'CLAIMED_EVIDENCE',
    replay_spec_authority: 'CONTRACT_AND_CANDIDATE_ONLY',
    derived_result: 'REPLAY_EXIT_NONZERO_AND_NO_OUTPUT_ARTIFACT',
    required_receipt_ids: REQUIRED_RECEIPT_IDS
  },
  receipt_replay_contract: RECEIPT_REPLAY_SPEC,
  authority_separation: {
    admission_result: 'PASS_V0_4_STRUCTURAL_SEMANTIC_ADMISSION',
    admission_execution_authority: false,
    admission_current_candidate_authority: false,
    full_result: 'PASS_CURRENT_V0_4_AUTHORITY_VALIDATION',
    full_execution_authority: true,
    full_replay_match_required: true
  },
  historical_reference_policy: {
    current_candidate_authority: false,
    historical_mode: 'HISTORICAL_REFERENCE_ONLY',
    readable_and_hash_verifiable: true
  }
});

export function contractBytes() {
  return jsonBytes(CONTRACT_DOCUMENT);
}

export function contractSha256() {
  return sha256(contractBytes());
}

export function validateContractBytes(bytes) {
  const value = parseStrictJsonBytes(bytes, 'CONTRACT');
  if (canonicalJson(value) !== canonicalJson(CONTRACT_DOCUMENT)
    || sha256(bytes) !== contractSha256()) {
    throw new Error('CONTRACT_EXACT_AUTHORITY_MISMATCH');
  }
  return value;
}

function validateRecoveryEvidence(evidence) {
  assertExactKeys(evidence, [
    'consolidated_closure_sha256', 'result', 'reviewer_report_sha256'
  ], 'RECOVERY_EVIDENCE');
  if (evidence.reviewer_report_sha256
      !== 'd28d56a53ead7c2a5a2ff3e14a97f5d2f8af76332b715d1c2a7ec19901fdd0f8'
    || evidence.consolidated_closure_sha256
      !== '0a90d9d46770010471634469211618b6f28382ccff864160fbcbd87cbb90c52a'
    || evidence.result !== 'INDEPENDENTLY_CLOSED') {
    throw new Error('RECOVERY_EVIDENCE_SEMANTIC_MISMATCH');
  }
}

function validateClippyEvidence(evidence) {
  assertExactKeys(evidence, [
    'comparator_sha256', 'consolidated_closure_sha256', 'result'
  ], 'CLIPPY_EVIDENCE');
  if (evidence.comparator_sha256
      !== 'fd2d933931b061f9cd2ca08d5832e81fc1f2ea3dcc77a1c6f8cb4d74717ae08e'
    || evidence.consolidated_closure_sha256
      !== '0a90d9d46770010471634469211618b6f28382ccff864160fbcbd87cbb90c52a'
    || evidence.result !== 'REMAINS_FROZEN_CLOSED') {
    throw new Error('CLIPPY_EVIDENCE_SEMANTIC_MISMATCH');
  }
}

function validateTypedContinuityEvidence(evidence, expectedManifestSha256) {
  assertExactKeys(evidence, [
    'attack_receipt_manifest_sha256', 'contract_sha256',
    'required_receipt_ids'
  ], 'VALIDATOR_REPAIR_EVIDENCE');
  if (evidence.contract_sha256 !== contractSha256()
    || evidence.attack_receipt_manifest_sha256 !== expectedManifestSha256) {
    throw new Error('VALIDATOR_REPAIR_EVIDENCE_SEMANTIC_MISMATCH');
  }
  assertExactArray(
    evidence.required_receipt_ids,
    REQUIRED_RECEIPT_IDS,
    'VALIDATOR_REPAIR_RECEIPT_IDS'
  );
}

function validateAdmissionAuthorityEvidence(evidence, expectedManifestSha256) {
  assertExactKeys(evidence, [
    'attack_receipt_manifest_sha256', 'contract_sha256',
    'execution_authority_model', 'receipt_replay_contract_sha256',
    'required_receipt_ids', 'single_blocker_closure_sha256'
  ], 'VALIDATOR_ADMISSION_AUTHORITY_EVIDENCE');
  if (evidence.contract_sha256 !== contractSha256()
    || evidence.attack_receipt_manifest_sha256 !== expectedManifestSha256
    || evidence.execution_authority_model !== 'V3_FULL_REPLAY_ONLY'
    || evidence.receipt_replay_contract_sha256
      !== canonicalSha256(RECEIPT_REPLAY_SPEC)
    || evidence.single_blocker_closure_sha256
      !== '03e5795615b304b0651ec79b6813cdab96a85f9b9eb28498470614e957b2be00') {
    throw new Error('VALIDATOR_ADMISSION_AUTHORITY_EVIDENCE_SEMANTIC_MISMATCH');
  }
  assertExactArray(
    evidence.required_receipt_ids,
    REQUIRED_RECEIPT_IDS,
    'VALIDATOR_ADMISSION_AUTHORITY_RECEIPT_IDS'
  );
}

export function findingEnvelope({
  candidateCommit,
  candidateTree,
  evidence,
  evidenceType,
  findingId,
  status
}) {
  return {
    domain: BINDING_DOMAIN,
    artifactRole: ARTIFACT_ROLE.evidence,
    contractSha256: contractSha256(),
    contractVersion: CONTRACT_VERSION,
    candidateCommit,
    candidateTree,
    findingId,
    status,
    evidenceType,
    evidence
  };
}

export function evidenceBinding(arguments_) {
  return canonicalSha256(findingEnvelope(arguments_));
}

function validateReceipt(receipt, id, actual) {
  assertExactKeys(receipt, [
    'candidate_commit', 'candidate_tree', 'derived_result', 'execution',
    'hostile_fixture_sha256', 'id', 'input_artifact_hashes', 'output',
    'expected_result', 'validator_executable_identity'
  ], `RECEIPT:${id}`);
  if (receipt.id !== id
    || receipt.candidate_commit !== actual.candidateCommit
    || receipt.candidate_tree !== actual.candidateTree
    || receipt.validator_executable_identity !== actual.validatorIdentity
    || receipt.expected_result !== 'REJECT') {
    throw new Error(`RECEIPT_IDENTITY_MISMATCH:${id}`);
  }
  assertSha256(receipt.hostile_fixture_sha256, `RECEIPT_FIXTURE:${id}`);
  assertExactKeys(receipt.input_artifact_hashes, [
    'contract', 'disposition', 'evidence', 'freeze'
  ], `RECEIPT_INPUT_HASHES:${id}`);
  for (const value of Object.values(receipt.input_artifact_hashes)) {
    assertSha256(value, `RECEIPT_INPUT_HASH:${id}`);
  }
  assertExactKeys(receipt.execution, [
    'command', 'exit_code', 'stderr_sha256', 'stdout_sha256'
  ], `RECEIPT_EXECUTION:${id}`);
  assertString(receipt.execution.command, `RECEIPT_COMMAND:${id}`);
  if (!Number.isInteger(receipt.execution.exit_code)) {
    throw new Error(`RECEIPT_EXIT_CODE_INVALID:${id}`);
  }
  assertSha256(receipt.execution.stdout_sha256, `RECEIPT_STDOUT:${id}`);
  assertSha256(receipt.execution.stderr_sha256, `RECEIPT_STDERR:${id}`);
  assertExactKeys(receipt.output, [
    'PASS_artifact_created', 'output_files', 'output_manifest_sha256'
  ], `RECEIPT_OUTPUT:${id}`);
  if (typeof receipt.output.PASS_artifact_created !== 'boolean'
    || !Array.isArray(receipt.output.output_files)
    || receipt.output.output_files.some((file) => typeof file !== 'string')) {
    throw new Error(`RECEIPT_OUTPUT_INVALID:${id}`);
  }
  assertSha256(receipt.output.output_manifest_sha256, `RECEIPT_OUTPUT_HASH:${id}`);
  const derived = receipt.execution.exit_code !== 0
    && receipt.output.PASS_artifact_created === false
    && receipt.output.output_files.length === 0
      ? 'PASS'
      : 'FAIL';
  if (receipt.derived_result !== derived || derived !== 'PASS') {
    throw new Error(`RECEIPT_DERIVATION_FAILED:${id}`);
  }
}

export function validateReceiptManifest(manifest, actual) {
  assertExactKeys(manifest, [
    'candidate_commit', 'candidate_tree', 'receipts', 'required_receipt_ids',
    'schema', 'validator_executable_identity'
  ], 'RECEIPT_MANIFEST');
  if (manifest.schema !== `${CONTRACT_SCHEMA}-EXECUTION-RECEIPTS`
    || manifest.candidate_commit !== actual.candidateCommit
    || manifest.candidate_tree !== actual.candidateTree
    || manifest.validator_executable_identity !== actual.validatorIdentity) {
    throw new Error('RECEIPT_MANIFEST_IDENTITY_MISMATCH');
  }
  assertExactArray(
    manifest.required_receipt_ids,
    REQUIRED_RECEIPT_IDS,
    'RECEIPT_MANIFEST_REQUIRED_IDS'
  );
  assertExactKeys(manifest.receipts, REQUIRED_RECEIPT_IDS, 'RECEIPT_SET');
  for (const id of REQUIRED_RECEIPT_IDS) validateReceipt(manifest.receipts[id], id, actual);
  return canonicalSha256(manifest);
}

export function compareReceiptReplay(claimedManifest, replayedManifest) {
  if (canonicalJson(claimedManifest) !== canonicalJson(replayedManifest)) {
    throw new Error('EXECUTION_RECEIPT_REPLAY_MISMATCH');
  }
  return Object.freeze({
    execution_authority: true,
    replay_match: true,
    replay_manifest_sha256: canonicalSha256(replayedManifest)
  });
}

function validateSurface(surface, expected, label) {
  assertExactKeys(surface, ['count', 'exact_paths', 'sha256'], label);
  if (!Number.isInteger(surface.count) || surface.count < 0) {
    throw new Error(`${label}_COUNT_INVALID`);
  }
  if (!Array.isArray(surface.exact_paths)
    || surface.exact_paths.some((item) => typeof item !== 'string')
    || surface.count !== surface.exact_paths.length
    || surface.sha256 !== canonicalSha256(surface.exact_paths)) {
    throw new Error(`${label}_SELF_IDENTITY_INVALID`);
  }
  if (surface.count !== expected.count
    || surface.sha256 !== expected.sha256
    || canonicalJson(surface.exact_paths) !== canonicalJson(expected.exactPaths)) {
    throw new Error(`${label}_GIT_IDENTITY_MISMATCH`);
  }
}

function validateCommon(document, role, actual, label) {
  if (document.schema !== CONTRACT_SCHEMA
    || document.contract_version !== CONTRACT_VERSION
    || document.contract_sha256 !== contractSha256()
    || document.artifact_role !== role
    || document.authority_mode !== actual.authorityMode
    || document.append_only !== true
    || document.base_commit !== BASE_COMMIT
    || document.predecessor_commit !== PREDECESSOR_COMMIT
    || document.candidate_commit !== actual.candidateCommit
    || document.candidate_tree !== actual.candidateTree) {
    throw new Error(`${label}_COMMON_AUTHORITY_MISMATCH`);
  }
}

export function validateAuthorityDocuments({
  contractBytes: suppliedContractBytes,
  dispositionBytes,
  evidenceBytes,
  freezeBytes,
  actual
}) {
  validateContractBytes(suppliedContractBytes);
  const disposition = parseStrictJsonBytes(dispositionBytes, 'DISPOSITION');
  const evidence = parseStrictJsonBytes(evidenceBytes, 'EVIDENCE');
  const freeze = parseStrictJsonBytes(freezeBytes, 'FREEZE');
  assertExactKeys(
    evidence,
    CONTRACT_DOCUMENT.exact_document_schemas.evidence,
    'EVIDENCE'
  );
  assertExactKeys(
    disposition,
    CONTRACT_DOCUMENT.exact_document_schemas.disposition,
    'DISPOSITION'
  );
  assertExactKeys(
    freeze,
    CONTRACT_DOCUMENT.exact_document_schemas.freeze,
    'FREEZE'
  );
  validateCommon(evidence, ARTIFACT_ROLE.evidence, actual, 'EVIDENCE');
  validateCommon(disposition, ARTIFACT_ROLE.disposition, actual, 'DISPOSITION');
  validateCommon(freeze, ARTIFACT_ROLE.freeze, actual, 'FREEZE');

  assertExactKeys(evidence.findings, FINDING_IDS, 'EVIDENCE_FINDINGS');
  const manifestSha256 = validateReceiptManifest(
    evidence.attack_receipt_manifest,
    actual
  );
  for (const id of FINDING_IDS) {
    const entry = evidence.findings[id];
    assertExactKeys(entry, [
      'envelope_sha256', 'evidence', 'evidence_type', 'finding_id', 'status'
    ], `EVIDENCE_FINDING:${id}`);
    if (entry.finding_id !== id
      || entry.status !== FINDING_STATUS[id]
      || entry.evidence_type !== EVIDENCE_TYPE[id]) {
      throw new Error(`EVIDENCE_FINDING_CONTRACT_MISMATCH:${id}`);
    }
    if (id === FINDING_IDS[0]) validateRecoveryEvidence(entry.evidence);
    if (id === FINDING_IDS[1]) validateClippyEvidence(entry.evidence);
    if (id === FINDING_IDS[2]) {
      validateTypedContinuityEvidence(entry.evidence, manifestSha256);
    }
    if (id === FINDING_IDS[3]) {
      validateAdmissionAuthorityEvidence(entry.evidence, manifestSha256);
    }
    const expectedBinding = evidenceBinding({
      candidateCommit: actual.candidateCommit,
      candidateTree: actual.candidateTree,
      evidence: entry.evidence,
      evidenceType: entry.evidence_type,
      findingId: id,
      status: entry.status
    });
    if (entry.envelope_sha256 !== expectedBinding) {
      throw new Error(`EVIDENCE_ENVELOPE_MISMATCH:${id}`);
    }
  }

  assertExactKeys(evidence.recovery_parity, [
    'consolidated_closure_sha256', 'reviewer_A_sha256', 'status'
  ], 'RECOVERY_PARITY');
  if (evidence.recovery_parity.consolidated_closure_sha256
      !== '0a90d9d46770010471634469211618b6f28382ccff864160fbcbd87cbb90c52a'
    || evidence.recovery_parity.reviewer_A_sha256
      !== 'd28d56a53ead7c2a5a2ff3e14a97f5d2f8af76332b715d1c2a7ec19901fdd0f8'
    || evidence.recovery_parity.status !== 'INDEPENDENTLY_CLOSED') {
    throw new Error('RECOVERY_PARITY_AUTHORITY_MISMATCH');
  }
  assertExactKeys(evidence.validator_attacks, [
    'receipt_manifest_sha256', 'required_receipt_ids'
  ], 'VALIDATOR_ATTACKS');
  if (evidence.validator_attacks.receipt_manifest_sha256 !== manifestSha256) {
    throw new Error('VALIDATOR_ATTACKS_MANIFEST_MISMATCH');
  }
  assertExactArray(
    evidence.validator_attacks.required_receipt_ids,
    REQUIRED_RECEIPT_IDS,
    'VALIDATOR_ATTACKS_IDS'
  );
  assertExactKeys(evidence.canonical_compatibility, [
    'current_candidate_authority', 'historical_mode',
    'historical_readable_and_hash_verifiable'
  ], 'CANONICAL_COMPATIBILITY');
  if (evidence.canonical_compatibility.historical_mode
      !== 'HISTORICAL_REFERENCE_ONLY'
    || evidence.canonical_compatibility.historical_readable_and_hash_verifiable
      !== true
    || evidence.canonical_compatibility.current_candidate_authority !== false) {
    throw new Error('CANONICAL_COMPATIBILITY_POLICY_MISMATCH');
  }
  assertExactKeys(evidence.regression, [
    'derived_by_candidate_validator', 'required'
  ], 'REGRESSION');
  if (evidence.regression.derived_by_candidate_validator !== true
    || evidence.regression.required !== true) {
    throw new Error('REGRESSION_CONTRACT_MISMATCH');
  }
  assertExactKeys(evidence.scope, [
    'clippy_comparator_changed', 'production_runtime_semantics_changed',
    'recovery_authority_changed', 'validation_authority_only'
  ], 'SCOPE');
  if (evidence.scope.clippy_comparator_changed !== false
    || evidence.scope.production_runtime_semantics_changed !== false
    || evidence.scope.recovery_authority_changed !== false
    || evidence.scope.validation_authority_only !== true) {
    throw new Error('SCOPE_CONTRACT_MISMATCH');
  }

  assertExactKeys(disposition.findings, FINDING_IDS, 'DISPOSITION_FINDINGS');
  for (const id of FINDING_IDS) {
    const entry = disposition.findings[id];
    assertExactKeys(entry, [
      'evidence_type', 'modification_policy', 'resolution', 'status'
    ], `DISPOSITION_FINDING:${id}`);
    if (entry.status !== FINDING_STATUS[id]
      || entry.modification_policy !== MODIFICATION_POLICY[id]
      || entry.evidence_type !== EVIDENCE_TYPE[id]) {
      throw new Error(`DISPOSITION_FINDING_CONTRACT_MISMATCH:${id}`);
    }
    assertString(entry.resolution, `DISPOSITION_RESOLUTION:${id}`);
  }
  assertExactKeys(disposition.summary, [
    'remaining_merge_blockers', 'repair_authority'
  ], 'DISPOSITION_SUMMARY');
  if (disposition.summary.remaining_merge_blockers !== 2
    || disposition.summary.repair_authority
      !== 'VALIDATOR_ADMISSION_AUTHORITY_ONLY') {
    throw new Error('DISPOSITION_SUMMARY_MISMATCH');
  }
  if (disposition.evidence_file !== CANONICAL_FILE_NAMES.evidence
    || disposition.evidence_sha256 !== sha256(evidenceBytes)) {
    throw new Error('DISPOSITION_EVIDENCE_BINDING_MISMATCH');
  }

  if (freeze.evidence_file !== CANONICAL_FILE_NAMES.evidence
    || freeze.evidence_sha256 !== sha256(evidenceBytes)
    || freeze.disposition_file !== CANONICAL_FILE_NAMES.disposition
    || freeze.disposition_sha256 !== sha256(dispositionBytes)) {
    throw new Error('FREEZE_DOCUMENT_BINDING_MISMATCH');
  }
  validateSurface(freeze.full_pr_surface, actual.fullPrSurface, 'FULL_PR_SURFACE');
  validateSurface(freeze.repair_surface, actual.repairSurface, 'REPAIR_SURFACE');
  return Object.freeze({ disposition, evidence, freeze, manifestSha256 });
}
