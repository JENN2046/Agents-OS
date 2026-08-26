#!/usr/bin/env node

import { createHash } from 'node:crypto';
import {
  chmodSync,
  mkdirSync,
  readFileSync,
  writeFileSync
} from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const {
  MODEL_PROFILE,
  RESPONSE_CONTRACT,
  cognitiveObservationMessage,
  resolveCognitiveContext
} = require('../companion/cognitive-context');

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
  'OBS-TRANSCRIPT-SCAN'
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

const inputRoot = argument('--input');
const outputRoot = argument('--output');
mkdirSync(outputRoot, { recursive: true, mode: 0o700 });
chmodSync(outputRoot, 0o700);

const projectionResult = readJson(inputRoot, 'rust_cognitive_projection.json');
const transcriptArtifact = readJson(inputRoot, 'fresh_session_transcript.json');
const oracle = readJson(inputRoot, 'p6b_fixture_oracle.json');
const stateSet = readJson(inputRoot, 'p6b_state_set.json');
const stale = readJson(inputRoot, 'stale_projection_rejection.json');
const transcript = transcriptArtifact.messages[0].content;
const positive = oracle.positive;
const negative = oracle.negative;
const config = {
  expectedProjectionGeneration: null,
  freshSessionId: transcriptArtifact.freshSessionId,
  modelProfileId: MODEL_PROFILE.identity,
  projectionPlan: {
    items: [
      { rank: 1, stateId: positive.stateId, visible: true },
      { rank: 2, stateId: negative.stateId, visible: true }
    ],
    retrieved: []
  },
  responseContract: RESPONSE_CONTRACT,
  scenario: positive.scenario
};
const resolved = resolveCognitiveContext(
  projectionResult,
  config,
  transcript
);
const observation = cognitiveObservationMessage(resolved);

const item = resolved.projection.effectiveProjection[0];
const staticInputs = [
  'companion/adapter.js',
  'companion/discovery.js',
  'companion/cognitive-context.js',
  'plugin-manifest.json.block'
];
const staticMaterial = staticInputs
  .map((name) => readFileSync(path.join(PACKAGE_ROOT, name), 'utf8'))
  .join('\n');
const answerValues = [
  positive.actionToken,
  negative.scenario,
  negative.actionToken,
  item.sourceType,
  item.lifecycleState,
  item.epistemicState
];
const transcriptLeakCount = answerValues
  .filter((value) => transcript.includes(value)).length;
const staticLeakCount = [
  positive.scenario,
  positive.actionToken,
  negative.scenario,
  negative.actionToken
].filter((value) => staticMaterial.includes(value)).length;

assert(transcriptArtifact.inheritedMessageCount === 0, 'FRESH_TRANSCRIPT_NOT_EMPTY');
assert(transcriptLeakCount === 0, 'COGNITIVE_SECRET_LEAKED_OUTSIDE_MEMORY_PATH');
assert(staticLeakCount === 0, 'COGNITIVE_SECRET_LEAKED_OUTSIDE_MEMORY_PATH');
assert(resolved.projection.effectiveProjection.length === 1,
  'CURRENT_STATE_NOT_COGNITIVELY_AVAILABLE');
assert(item.actionToken === positive.actionToken, 'CURRENT_STATE_NOT_COGNITIVELY_AVAILABLE');
assert(item.scenario === positive.scenario, 'CURRENT_STATE_NOT_COGNITIVELY_AVAILABLE');
assert(resolved.projection.excludedStateIds.includes(negative.stateId),
  'NEGATIVE_CONTROL_PROJECTED');
assert(resolved.structuredResponse.actionToken === positive.actionToken,
  'CURRENT_STATE_NOT_COGNITIVELY_AVAILABLE');
assert(resolved.structuredResponse.sourceType === item.sourceType
  && resolved.structuredResponse.lifecycleState === item.lifecycleState
  && resolved.structuredResponse.epistemicState === item.epistemicState,
  'COGNITIVE_SOURCE_STATUS_MISATTRIBUTED');
assert(resolved.structuredResponse.effectiveContextDigest
  === resolved.effectiveContextDigest, 'EFFECTIVE_CONTEXT_EVIDENCE_MISSING');
assert(stale.accepted === false
  && stale.resultCode === 'STALE_PROJECTION_FAIL_CLOSED'
  && !Object.hasOwn(stale, 'projection'), 'STALE_PROJECTION_ACCEPTED');
assert(projectionResult.durableTransitionCount
  === projectionResult.projectionGeneration, 'PROJECTION_GENERATION_UNBOUND');

const artifacts = [];
artifacts.push(writeJson(outputRoot, 'model_runtime_fingerprint.json', {
  controlledProofClaimed: false,
  decoding: {
    sampling: resolved.modelProfile.sampling,
    temperature: resolved.modelProfile.temperature
  },
  effectiveContextDigest: resolved.effectiveContextDigest,
  externalModelInvoked: false,
  freshSessionId: config.freshSessionId,
  modelProfile: resolved.modelProfile,
  providerInvoked: false
}));
artifacts.push(writeJson(outputRoot, 'fresh_session_transcript.json', transcriptArtifact));
artifacts.push(writeJson(outputRoot, 'effective_projection.json', {
  effectiveContext: resolved.effectiveContext,
  effectiveContextDigest: resolved.effectiveContextDigest,
  projection: resolved.projection,
  projectionIdentity: resolved.projectionIdentity
}));
artifacts.push(writeJson(outputRoot, 'structured_response.json', {
  cognitiveObservationMessageDigest: `sha256:${sha256(observation.content)}`,
  structuredResponse: resolved.structuredResponse
}));
artifacts.push(writeJson(outputRoot, 'secret_scan.json', {
  inputs: [...staticInputs, 'fresh_session_transcript.json'],
  staticOpaqueRuleOccurrenceCount: staticLeakCount,
  transcriptAnswerOccurrenceCount: transcriptLeakCount
}));
artifacts.push(writeJson(outputRoot, 'stale_projection_rejection.json', stale));
artifacts.push(writeJson(outputRoot, 'state_set.json', stateSet));

const targetedEvidence = {
  authority: {
    exactContractSource: 'MMR-0_TD1_Proof_Catalog_v0.2.yaml',
    proofId: 'CAV2',
    requiredObservables: REQUIRED_OBSERVABLES,
    vectorIds: ['CAV2-V1', 'CAV2-V2']
  },
  controlledProofClaimed: false,
  cutpointMap: {
    'COGNITIVE-FRESH': {
      effectiveContextDigest: resolved.effectiveContextDigest,
      freshSessionId: config.freshSessionId,
      inheritedMessageCount: 0,
      projectionGeneration: projectionResult.projectionGeneration,
      projectionIdentity: projectionResult.projectionIdentity
    }
  },
  durableMutationFromCognition: 0,
  evidenceClass: 'TARGETED_DEVELOPMENT_PROOF_NOT_CONTROLLED_PROOF',
  modelRuntime: {
    effectiveContextBindingKnown: true,
    freshSessionBindingKnown: true,
    identity: resolved.modelProfile.identity,
    profileFingerprint: resolved.modelProfile.fingerprint,
    providerInvoked: false
  },
  negativeControl: {
    actionProjected: false,
    stateId: negative.stateId,
    stateProjected: false
  },
  projectionProvenance: {
    admittedStateIdentity: item.admittedStateIdentity,
    projectionGeneration: projectionResult.projectionGeneration,
    projectionIdentity: projectionResult.projectionIdentity,
    sourceStatus: resolved.effectiveContext.sourceStatus
  },
  result: 'PASS_MMR_0_TD2_R4_P6_B_CAV2_TARGETED',
  staleProjectionRejection: stale,
  vectors: {
    'CAV2-V1': {
      actionTokenExact: resolved.structuredResponse.actionToken
        === positive.actionToken,
      observables: REQUIRED_OBSERVABLES,
      result: 'PASS'
    },
    'CAV2-V2': {
      epistemicStateExact: resolved.structuredResponse.epistemicState
        === item.epistemicState,
      lifecycleStateExact: resolved.structuredResponse.lifecycleState
        === item.lifecycleState,
      observables: REQUIRED_OBSERVABLES,
      result: 'PASS',
      sourceTypeExact: resolved.structuredResponse.sourceType === item.sourceType
    }
  }
};
const targeted = writeJson(
  outputRoot,
  'MMR-0_TD2_R4_P6_B_CAV2_Targeted_Proof_Evidence.json',
  targetedEvidence
);
artifacts.push(targeted);

writeJson(outputRoot, 'builder_result.json', {
  artifacts,
  controlledProofClaimed: false,
  result: 'PASS_P6_B_CAV2_EVIDENCE_BUILD',
  runtimeSelfReportIsProofAuthority: false,
  targetedEvidenceSha256: targeted.sha256
});

process.stdout.write(`${JSON.stringify({
  effectiveContextDigest: resolved.effectiveContextDigest,
  modelProfileFingerprint: resolved.modelProfile.fingerprint,
  result: 'PASS_P6_B_CAV2_EVIDENCE_BUILD',
  targetedEvidenceSha256: targeted.sha256
})}\n`);
