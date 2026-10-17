// Actual public signatures + unsigned preauth, never a production Human/key ceremony.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {generateKeyPairSync,createHash} from 'node:crypto';
import {digest,exportPublicKey,verified,ROLES} from '../src/lease-core.mjs';
import {SOURCE19_BASELINE,HISTORICAL_R15_BASELINE,sourceBaselineId,inspectSourceRelease,inspectSourcePublicConfiguration,inspectSourceOwnerConfiguration} from '../authority/source-baseline.mjs';
import {STAGE_CONSTRAINTS,validateStageAuthorization} from '../authority/stage-authorization.mjs';
import {inspectHumanProposalSource} from '../release/human-proposal-inputs.mjs';
import {deriveExactR17Release} from '../release/first-trust-release-builder.mjs';
import {verifiedR15CrownVerifier} from '../release/publisher-once.mjs';
import {EXACT_R17_MIGRATION_SCOPE,EXACT_SOURCE19_R17_MIGRATION_SCOPE,inspectRecoveryMigrationEvidence} from '../migration/r17-one-time-recovery-admission.mjs';
import {REVIEWED_SOURCE_FILES} from '../release/publisher-bootstrap.mjs';
import {HUMAN_PROPOSAL_REQUIRED_FILES} from '../release/human-proposal-bootstrap.mjs';
import {APPROVAL_REQUIRED_FILES} from '../human/approval-bootstrap.mjs';
const pub=JSON.parse(fs.readFileSync(new URL('./fixtures/SOURCE19_PUBLIC_CONFIG.json',import.meta.url)));
const delivery=JSON.parse(fs.readFileSync(new URL('./fixtures/SOURCE19_DELIVERY_ENVELOPE.json',import.meta.url)));
const now=pub.release.body.issuedAt+2000,clone=x=>structuredClone(x),key=()=>exportPublicKey(generateKeyPairSync('ed25519').privateKey);
function preauth(){
 const g=pub.grant.body;
 const roots={schema:'mht.trust-roots.v1',grantId:g.id,issuerPublicKey:pub.issuerPublicKey,releasePublicKey:pub.releasePublicKey,enrollmentAuthorityPublicKey:key(),releaseHash:digest(pub.release),handoffHash:digest('ISOLATED_NOT_ISSUED_HANDOFF'),installationProfile:'production'};
 const policy={schema:'mht.human-pending-policy-template.v1',grantId:g.id,grantHash:digest(pub.grant),grantVersion:g.version,releaseHash:digest(pub.release),releaseId:pub.release.body.id,humanPublicKey:key(),workspaceId:g.workspace.id,workspaceRoot:g.workspace.root,workspaceDev:g.workspace.dev,workspaceIno:g.workspace.ino,installationProfile:'production'};
 const stage={schema:'mht.first-trust-stage-authorization.v2',phase:'STAGE_ONLY',sourceReleaseId:pub.release.body.id,targetReleaseId:'r16-daily-20261012-r17',grantId:g.id,grantHash:digest(pub.grant),grantVersion:g.version,r15PublicConfigDigest:digest(pub),reviewedManifestHash:digest('ISOLATED_REVIEW'),recoveryEvidenceDigest:digest('ISOLATED_NO_PRODUCTION_PROOF'),sourceFreezeDigest:digest('ISOLATED_FREEZE'),installerHash:digest('ISOLATED_INSTALLER'),issuerSnapshotHash:digest('ISOLATED_SNAPSHOT'),trustRootsDigest:digest(roots),stopEpoch:'00000000-0000-4000-8000-000000000000',handoffEpoch:1,issuedAt:now-1000,expiresAt:now+60000,constraints:{...STAGE_CONSTRAINTS}};
 const request={schema:'mht.human-proposal-request.v1',issuerStateFileHash:digest('ISOLATED_WHOLE_WRAPPER'),policyTemplate:policy,body:{schema:'mht.human-proposal.v1',action:'enroll_human',grantId:g.id,expectedVersion:g.version,expectedGrantHash:digest(pub.grant),releaseId:pub.release.body.id,releaseHash:digest(pub.release),nonce:'source19_isolated_nonce',issuedAt:stage.issuedAt,expiresAt:stage.expiresAt,target:{humanUid:1000,humanSubject:'local-human:1000',humanPublicKey:policy.humanPublicKey,enrollmentExpiresAt:now+86400000,targetReleaseId:stage.targetReleaseId,reviewedManifestHash:stage.reviewedManifestHash,stageAuthorizationHash:digest(stage),stageAuthorization:stage}}};
 return {request,roots,pub,workspaceIdentity:{dev:g.workspace.dev,ino:g.workspace.ino},now,stage};
}
test('actual signed source19 public config is exact, same original Grant, with repaired App+Native',()=>{
 assert.equal(digest(pub),SOURCE19_BASELINE.publicConfigDigest);assert.equal(digest(pub.release),SOURCE19_BASELINE.releaseHash);
 assert.equal(inspectSourcePublicConfiguration(pub),SOURCE19_BASELINE);
 assert.equal(verified(pub.grant,pub.issuerPublicKey,'r16.workspace.v1').id,'r16-projects-daily');
 assert.deepEqual(verified(pub.release,pub.releasePublicKey,'r16.release.v1').versions,SOURCE19_BASELINE.versions);
 assert.equal(sourceBaselineId(HISTORICAL_R15_BASELINE.releaseId),HISTORICAL_R15_BASELINE);
});
function ownerConfiguration(){return {kind:'r16.owner.configuration.v1',connectionNonce:7,delivery:{hash:digest({publicConfig:pub,control:delivery.body.control,connectionNonce:7}),revision:19,envelope:clone(delivery)}};}
test('actual independently signed accepted19 envelope and exact Owner cache are required as well as public config',()=>{
 const c=ownerConfiguration(),r=inspectSourceOwnerConfiguration(pub,c,now);
 assert.equal(digest(delivery),SOURCE19_BASELINE.acceptedDeliveryHash);assert.equal(r.revision,19);
 assert.equal(verified(delivery,pub.issuerPublicKey,'r16.configuration-delivery.v1').revision,19);
});
test('same public config with different cache revision, envelope, signature or connection binding is refused',()=>{
 for(const mutate of [c=>{c.delivery.revision=20;},c=>{c.delivery.revision=18;},c=>{c.delivery.envelope.body.revision=20;},c=>{c.delivery.envelope.signature='A'.repeat(86);},c=>{c.delivery.hash='f'.repeat(64);},c=>{c.connectionNonce++;}]){const c=ownerConfiguration();mutate(c);assert.throws(()=>inspectSourceOwnerConfiguration(pub,c,now));}
 assert.throws(()=>inspectSourceOwnerConfiguration(pub,ownerConfiguration(),delivery.body.issuedAt-1),{code:'SOURCE19_ACCEPTED_DELIVERY_SCOPE_DRIFT'});
});
test('new release ID cannot admit arbitrary public roots, signed bytes, version maps or caller overrides',()=>{
 for(const change of [{extra:'foreign'},{issuerPublicKey:key()},{releasePublicKey:key()},{grant:{...pub.grant,signature:'A'.repeat(86)}},{versions:{...pub.versions,app:HISTORICAL_R15_BASELINE.versions.app}}])assert.throws(()=>inspectSourcePublicConfiguration({...clone(pub),...change}));
 for(const role of ROLES){const changed=clone(pub);changed.release.body.versions[role]='a'.repeat(64);assert.throws(()=>inspectSourcePublicConfiguration(changed),{code:'SOURCE19_VERSIONS_NOT_PINNED'});}
 assert.throws(()=>sourceBaselineId('r16-daily-any-caller'),{code:'SOURCE_RELEASE_NOT_PINNED'});
});
test('source19 Crown loader selects the new signed App tree and refuses an unverified manifest before import',async()=>{
 const reads=[];
 await assert.rejects(verifiedR15CrownVerifier({pub,readProtected:file=>{reads.push(file);return Buffer.from(JSON.stringify({schema:'r16.runtime-code.v1',role:'app',entry:'app/upstream/src/project-forge-crown-transport.mjs',files:{'app/upstream/src/project-forge-crown-transport.mjs':'a'.repeat(64)}}));},importModule:()=>assert.fail('unverified Crown code imported')}),{code:'PUBLISHER_OLD_APP_MANIFEST'});
 assert.deepEqual(reads,[SOURCE19_BASELINE.directory+'/app-manifest.json']);
 await assert.rejects(verifiedR15CrownVerifier({pub:{...pub,channel:'foreign'},readProtected:()=>assert.fail('untrusted root read'),importModule:()=>assert.fail('untrusted root import')}),{code:'SOURCE19_PUBLIC_NOT_PINNED'});
});
test('unsigned first enrollment target can bind actual source19 without forging Human approval or signing',()=>{
 const f=preauth(),r=inspectHumanProposalSource(f);assert.equal(r.source.id,SOURCE19_BASELINE.releaseId);assert.equal(r.checked.body.action,'enroll_human');assert.deepEqual(r.grant,pub.grant.body);
 assert.equal(validateStageAuthorization(f.stage,{now}),f.stage);assert.equal(f.stage.constraints.mayInstall,false);assert.equal(f.stage.constraints.mayHandoffIssuer,false);
});
test('source19 pending target rejects wrong public digest, source hash, versions and inherited confirmation time',()=>{
 const f=preauth();
 for(const patch of [{releaseHash:'b'.repeat(64)},{releaseId:HISTORICAL_R15_BASELINE.releaseId}]){const changed=clone(f);Object.assign(changed.request.body,patch);assert.throws(()=>inspectHumanProposalSource(changed));}
 const wrong=clone(f.stage);wrong.r15PublicConfigDigest=HISTORICAL_R15_BASELINE.publicConfigDigest;assert.throws(()=>validateStageAuthorization(wrong,{now}));
 assert.throws(()=>inspectHumanProposalSource({...f,now:f.request.body.expiresAt}));
 assert.throws(()=>validateStageAuthorization(f.stage,{now:f.stage.expiresAt}));
});
test('exact source19 body derives only complete reviewed R17 bindings and cannot inherit old clocks',()=>{
 const bytes=Buffer.from('isolated source19 target bytes; no installer'),sha=createHash('sha256').update(bytes).digest('hex'),artifacts={},localFiles=[];
 for(const role of ROLES){const name=role+'/isolated.mjs';artifacts[role]={schema:'r16.runtime-code.v1',role,entry:name,files:{[name]:sha}};localFiles.push({role,artifactPath:name,path:'/opt/r16/releases/r16-daily-20261012-r17/'+name,sha256:sha});}
 const reviewManifest={schema:'r16.reviewed-installation.v1',releaseId:'r16-daily-20261012-r17',issuedAt:now-1000,notAfter:now+86400000,artifacts,localFiles};
 const arg={sourceRelease:pub.release.body,reviewManifest,reviewedManifestHash:digest(reviewManifest),now,readFile:()=>bytes};
 const body=deriveExactR17Release(arg);assert.equal(body.id,'r16-daily-20261012-r17');assert.deepEqual(body.actions,pub.release.body.actions);assert.equal(body.permissionVersion,pub.release.body.permissionVersion);
 assert.throws(()=>deriveExactR17Release({...arg,now:reviewManifest.issuedAt+300001}),{code:'FIRST_TRUST_RELEASE_WINDOW'});
 const bad=clone(reviewManifest);bad.issuedAt=pub.release.body.issuedAt-1;assert.throws(()=>deriveExactR17Release({...arg,reviewManifest:bad,reviewedManifestHash:digest(bad)}));
 assert.throws(()=>inspectSourceRelease({...pub.release.body,versions:HISTORICAL_R15_BASELINE.versions}),{code:'SOURCE19_VERSIONS_NOT_PINNED'});
});
test('source19 migration keeps byte-exact original two UNKNOWN pins and rejects old versions or substitutes',()=>{
 const old=EXACT_R17_MIGRATION_SCOPE,newer=EXACT_SOURCE19_R17_MIGRATION_SCOPE;
 assert.deepEqual(newer.projects,old.projects);assert.equal(newer.projects,old.projects);assert.deepEqual(newer.sourceVersions,SOURCE19_BASELINE.versions);
 for(const patch of [{sourceVersions:old.sourceVersions},{projects:[{...old.projects[0],operationId:'substitute'},old.projects[1]]},{projects:[old.projects[0],{...old.projects[1],operationHash:'f'.repeat(64)}]}])assert.throws(()=>inspectRecoveryMigrationEvidence({}, {...newer,reviewDigest:'c'.repeat(64),...patch},()=>assert.fail('Crown called before pin rejection')),{code:'R17_SCOPE_NOT_PINNED'});
});
test('all privileged first-trust closures require the new fixed-source validator before any signing import',()=>{
 for(const files of [REVIEWED_SOURCE_FILES,HUMAN_PROPOSAL_REQUIRED_FILES,APPROVAL_REQUIRED_FILES])assert.equal(files.filter(n=>n==='authority/source-baseline.mjs').length,1);
});
