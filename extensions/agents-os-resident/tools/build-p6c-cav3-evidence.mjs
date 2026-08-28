#!/usr/bin/env node

import { createHash } from 'node:crypto';
import {
  chmodSync,
  mkdirSync,
  readFileSync,
  writeFileSync
} from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const TOOL_PATH = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = path.resolve(path.dirname(TOOL_PATH), '..');
const REQUIRED_OBSERVABLES = Object.freeze([
  'OBS-CUTPOINT-MAP',
  'OBS-FIXTURE',
  'OBS-MODEL-PROFILE',
  'OBS-ORACLE-EVALUATOR',
  'OBS-PROJECTION',
  'OBS-RESPONSE',
  'OBS-STATE-SET',
  'OBS-TRANSCRIPT-SCAN',
  'OBS-TRANSITIONS'
]);

function argument(name) {
  const index = process.argv.indexOf(name);
  if (index === -1 || index + 1 >= process.argv.length) {
    throw new Error(`MISSING_ARGUMENT:${name}`);
  }
  return path.resolve(process.argv[index + 1]);
}

function readJson(root, name) {
  return JSON.parse(readFileSync(path.join(root, name), 'utf8'));
}

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value === null || typeof value !== 'object') return value;
  return Object.fromEntries(
    Object.keys(value).sort().map((key) => [key, canonical(value[key])])
  );
}

function canonicalJson(value) {
  return JSON.stringify(canonical(value));
}

function writeJson(root, name, value) {
  const target = path.join(root, name);
  const bytes = `${JSON.stringify(canonical(value), null, 2)}\n`;
  writeFileSync(target, bytes, { encoding: 'utf8', mode: 0o600 });
  chmodSync(target, 0o600);
  return {
    bytes: Buffer.byteLength(bytes, 'utf8'),
    name,
    sha256: sha256(bytes)
  };
}

function assert(condition, token) {
  if (!condition) throw new Error(token);
}

function occurrences(haystack, needle) {
  if (needle.length === 0) return 0;
  return haystack.split(needle).length - 1;
}

const inputRoot = argument('--input');
const outputRoot = argument('--output');
mkdirSync(outputRoot, { recursive: true, mode: 0o700 });
chmodSync(outputRoot, 0o700);

const fixture = readJson(inputRoot, 'p6c_fixture_oracle.json');
const stateBefore = readJson(inputRoot, 'p6c_state_set.json');
const stateAfter = readJson(inputRoot, 'p6c_durable_after_cognition.json');
const positiveProjection = readJson(inputRoot, 'p6c_positive_projection.json');
const negativeProjection = readJson(inputRoot, 'p6c_negative_projection.json');
const transcript = readJson(inputRoot, 'p6c_fresh_session_transcript.json');
const runtimeInputs = readJson(inputRoot, 'p6c_runtime_inputs.json');
const rustScan = readJson(inputRoot, 'p6c_transcript_static_scan.json');
const stale = readJson(inputRoot, 'p6c_stale_projection_rejection.json');
const positiveObservation = readJson(
  inputRoot,
  'p6c_companion_positive_observation.json'
);
const negativeObservation = readJson(
  inputRoot,
  'p6c_companion_negative_observation.json'
);
const companionScan = readJson(
  inputRoot,
  'p6c_companion_runtime_input_scan.json'
);
const companionStale = readJson(
  inputRoot,
  'p6c_companion_stale_rejection.json'
);
const positive = fixture.positive;
const negative = fixture.negative;
const negativeMapping = canonicalJson({
  actionToken: negative.actionToken,
  scenario: negative.scenario
});
const positiveMapping = canonicalJson({
  actionToken: positive.actionToken,
  scenario: positive.scenario
});

const staticInputs = [
  'companion/adapter.js',
  'companion/discovery.js',
  'companion/cognitive-context.js',
  'plugin-manifest.json.block'
];
const staticMaterial = staticInputs
  .map((name) => readFileSync(path.join(PACKAGE_ROOT, name), 'utf8'))
  .join('\n');
const transcriptBytes = canonicalJson(transcript);
const runtimeInputBytes = canonicalJson(runtimeInputs);
const stateBeforeBytes = canonicalJson(stateBefore);
const negativeProjectionBytes = canonicalJson(negativeProjection.projection);
const negativeEffectiveContextBytes = canonicalJson(
  negativeObservation.effectiveContext
);
const negativeResponseBytes = canonicalJson(
  negativeObservation.structuredResponse
);

const plaintextRuntimeLeakCount = [
  runtimeInputBytes,
  transcriptBytes,
  staticMaterial,
  negativeProjectionBytes,
  negativeEffectiveContextBytes
].reduce((count, bytes) => count
  + occurrences(bytes, negative.actionToken)
  + occurrences(bytes, negativeMapping), 0);
const responseNegativeReproductionCount =
  occurrences(negativeResponseBytes, negative.actionToken)
  + occurrences(negativeResponseBytes, negativeMapping);

assert(fixture.structuralProfileMatch === true, 'STRUCTURAL_PROFILE_MISMATCH');
assert(positive.scenario.length === negative.scenario.length
  && positive.actionToken.length === negative.actionToken.length,
'STRUCTURAL_PROFILE_MISMATCH');
assert(positiveMapping.length === negativeMapping.length,
  'STRUCTURAL_PROFILE_MISMATCH');
assert(transcript.inheritedMessageCount === 0, 'FRESH_TRANSCRIPT_NOT_EMPTY');
assert(plaintextRuntimeLeakCount === 0, 'COGNITIVE_CONTROL_CONTAMINATED');
assert(responseNegativeReproductionCount === 0,
  'NEGATIVE_CONTROL_HALLUCINATED_RULE');
for (const absent of [
  negative.stateId,
  negative.scenario,
  negative.actionToken
]) {
  assert(!stateBeforeBytes.includes(absent), 'NEGATIVE_RULE_DURABLE');
  assert(!negativeProjectionBytes.includes(absent),
    'NEGATIVE_RULE_APPEARED_IN_PROJECTION');
  assert(!negativeEffectiveContextBytes.includes(absent),
    'NEGATIVE_RULE_APPEARED_IN_EFFECTIVE_CONTEXT');
}
assert(canonicalJson(stateAfter) === stateBeforeBytes,
  'SILENT_DURABLE_MUTATION');
assert(positiveProjection.projection.effectiveProjection.length === 1,
  'POSITIVE_CONTROL_MISSING');
assert(positiveProjection.projection.effectiveProjection[0].actionToken
  === positive.actionToken, 'POSITIVE_CONTROL_MISSING');
assert(positiveObservation.structuredResponse.actionToken
  === positive.actionToken, 'POSITIVE_RESPONSE_BINDING_FAILED');
assert(negativeProjection.resultCode === 'MMR_COGNITIVE_PROJECTION_EMPTY_OK'
  && negativeProjection.projection.effectiveProjection.length === 0,
'NEGATIVE_RULE_APPEARED_IN_PROJECTION');
assert(negativeObservation.effectiveContext.admittedMappingCount === 0
  && negativeObservation.effectiveContext.rule === null,
'NEGATIVE_RULE_APPEARED_IN_EFFECTIVE_CONTEXT');
assert(negativeObservation.structuredResponse.answer === 'UNKNOWN'
  && negativeObservation.structuredResponse.reasonCode
    === 'NO_ADMITTED_MAPPING',
'NEGATIVE_RESPONSE_PROTOCOL_FAILED');
assert(negativeObservation.structuredResponse.effectiveContextDigest
  === negativeObservation.effectiveContextDigest,
'EFFECTIVE_CONTEXT_EVIDENCE_MISSING');
for (const staleResult of [stale, companionStale]) {
  assert(staleResult.accepted === false
    && staleResult.resultCode === 'STALE_PROJECTION_FAIL_CLOSED'
    && !Object.hasOwn(staleResult, 'projection'),
  'STALE_PROJECTION_ACCEPTED');
}
assert(rustScan.plaintextRuntimeLeakCount === 0
  && companionScan.plaintextRuntimeLeakCount === 0,
'COGNITIVE_CONTROL_CONTAMINATED');

const artifacts = [];
artifacts.push(writeJson(outputRoot, 'negative_fixture.json', {
  negative,
  negativeRuleDigest: `sha256:${sha256(negativeMapping)}`,
  positive,
  positiveRuleDigest: `sha256:${sha256(positiveMapping)}`,
  runSeedHex: fixture.runSeedHex,
  seedSha256: fixture.seedSha256,
  structuralProfileMatch: true
}));
artifacts.push(writeJson(outputRoot, 'fresh_session_transcript.json', transcript));
artifacts.push(writeJson(outputRoot, 'effective_projection.json', {
  negative: {
    effectiveContext: negativeObservation.effectiveContext,
    effectiveContextDigest: negativeObservation.effectiveContextDigest,
    projection: negativeProjection.projection,
    projectionIdentity: negativeProjection.projectionIdentity
  },
  positive: {
    effectiveContext: positiveObservation.effectiveContext,
    effectiveContextDigest: positiveObservation.effectiveContextDigest,
    projection: positiveProjection.projection,
    projectionIdentity: positiveProjection.projectionIdentity
  }
}));
artifacts.push(writeJson(outputRoot, 'structured_response.json', {
  negative: negativeObservation.structuredResponse,
  positive: positiveObservation.structuredResponse,
  responseNegativeReproductionCount
}));
artifacts.push(writeJson(outputRoot, 'full_secret_scan.json', {
  negativeActionOccurrenceCount: 0,
  negativeMappingOccurrenceCount: 0,
  plaintextRuntimeLeakCount,
  responseNegativeReproductionCount,
  runtimeInputs: [
    ...staticInputs,
    'fresh_session_transcript.json',
    'p6c_runtime_inputs.json',
    'effective_projection.json'
  ]
}));
artifacts.push(writeJson(outputRoot, 'invalid_run_classification.json', {
  classification: 'VALID_NEGATIVE_CONTROL',
  responseOnlyNegativeTokenObserved: false,
  rerunRequired: false
}));
artifacts.push(writeJson(outputRoot, 'state_set.json', stateBefore));
artifacts.push(writeJson(outputRoot, 'transitions.json', {
  durableStateSnapshot: stateBefore,
  negativeRuleStateCount: 0,
  negativeRuleTransitionCount: 0
}));
artifacts.push(writeJson(outputRoot, 'stale_projection_rejection.json', stale));
artifacts.push(writeJson(outputRoot, 'model_runtime_fingerprint.json', {
  decoding: {
    sampling: negativeObservation.modelProfile.sampling,
    temperature: negativeObservation.modelProfile.temperature
  },
  effectiveContextDigest: negativeObservation.effectiveContextDigest,
  externalModelInvoked: false,
  freshSessionId: negativeObservation.effectiveContext.freshSessionId,
  modelProfile: negativeObservation.modelProfile,
  providerInvoked: false
}));

const targetedEvidence = {
  authority: {
    exactContractSource: 'MMR-0_TD1_Proof_Catalog_v0.2.yaml',
    proofId: 'CAV3',
    requiredObservables: REQUIRED_OBSERVABLES,
    vectorIds: ['CAV3-V1', 'CAV3-V2']
  },
  controlledProofClaimed: false,
  cutpointMap: {
    'COGNITIVE-FRESH': {
      effectiveContextDigest: negativeObservation.effectiveContextDigest,
      freshSessionId: negativeObservation.effectiveContext.freshSessionId,
      inheritedMessageCount: 0,
      projectionGeneration:
        negativeObservation.effectiveContext.projectionGeneration,
      projectionIdentity: negativeObservation.projectionIdentity
    }
  },
  durableMutationFromCognition: 0,
  evidenceClass: 'TARGETED_DEVELOPMENT_PROOF_NOT_CONTROLLED_PROOF',
  fixture: {
    negativeRuleDigest: `sha256:${sha256(negativeMapping)}`,
    plaintextRuntimeLeakCount,
    positiveRuleDigest: `sha256:${sha256(positiveMapping)}`,
    structuralProfileMatch: true
  },
  freshContext: {
    effectiveContextDigest: negativeObservation.effectiveContextDigest,
    freshSessionId: negativeObservation.effectiveContext.freshSessionId,
    modelProfileIdentity: negativeObservation.modelProfile.identity,
    projectionDigest: negativeObservation.projectionIdentity,
    projectionGeneration:
      negativeObservation.effectiveContext.projectionGeneration,
    responseBinding: negativeObservation.structuredResponse.responseBinding
  },
  modelRuntime: {
    externalModelInvoked: false,
    identity: negativeObservation.modelProfile.identity,
    profileFingerprint: negativeObservation.modelProfile.fingerprint,
    providerInvoked: false
  },
  negativeControl: {
    currentProjectionContainsNegativeRule: false,
    durableAdmitted: false,
    effectiveContextContainsNegativeRule: false,
    responseReproducesNegativeRule: false
  },
  positiveControl: {
    admitted: true,
    effectiveContextPresent: true,
    projected: true,
    responseBinding: 'PASS'
  },
  responseNegativeReproductionCount,
  result: 'PASS_MMR_0_TD2_R4_P6_C_CAV3_TARGETED',
  staleProjectionRejection: stale,
  vectors: {
    'CAV3-V1': {
      observables: REQUIRED_OBSERVABLES,
      projectionContainsNegativeMapping: false,
      response: 'UNKNOWN',
      responseContainsNegativeAction: false,
      result: 'PASS'
    },
    'CAV3-V2': {
      effectiveContextContainsNegativeMapping: false,
      observables: REQUIRED_OBSERVABLES,
      plaintextRuntimeLeakCount,
      responseNegativeReproductionCount,
      result: 'PASS'
    }
  }
};
const targeted = writeJson(
  outputRoot,
  'MMR-0_TD2_R4_P6_C_CAV3_Targeted_Proof_Evidence.json',
  targetedEvidence
);
artifacts.push(targeted);

writeJson(outputRoot, 'builder_result.json', {
  artifacts,
  controlledProofClaimed: false,
  result: 'PASS_P6_C_CAV3_EVIDENCE_BUILD',
  runtimeSelfReportIsProofAuthority: false,
  targetedEvidenceSha256: targeted.sha256
});

process.stdout.write(`${JSON.stringify({
  effectiveContextDigest: negativeObservation.effectiveContextDigest,
  plaintextRuntimeLeakCount,
  responseNegativeReproductionCount,
  result: 'PASS_P6_C_CAV3_EVIDENCE_BUILD',
  targetedEvidenceSha256: targeted.sha256
})}\n`);
