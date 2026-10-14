// Synthetic keys and virtual fixed-path reads only; no production authority.
import assert from 'node:assert/strict';
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {signed,exportPublicKey,digest,ROLES,ACTIONS} from '../../src/lease-core.mjs';
import {runtimeVersion} from '../../authority/runtime-manifest.mjs';
import {STAGE_CONSTRAINTS} from '../../authority/stage-authorization.mjs';
import {EXACT_R17_MIGRATION_SCOPE} from '../../migration/r17-one-time-recovery-admission.mjs';
import {inspectStagedR17HandoffAdmission} from '../../release/staged-r17-handoff-admission.mjs';
import {validateHumanProposal,firstTrustReviewedIntent} from '../../human/approval-policy.mjs';

const pair=()=>generateKeyPairSync('ed25519').privateKey;
const PLAN='/etc/minimal-human-trust/first-trust-publication.json';
const TX='/var/lib/minimal-human-trust/first-trust-publication';
const OLD='/var/lib/r16-owner/issuer/state.json';
const NEXT='/var/lib/minimal-human-trust/issuer/state.json';
export function stagedHandoffFixture({profile='production',physical=false,installerHash=digest('reviewed-installer')}={}){
 const now=1792200000000,approvedAt=now-360000;
 const issuer=pair(),releaseKey=pair(),enroller=pair(),human=pair();
 const signers=Object.fromEntries(ROLES.map(role=>[role,pair()]));
 const peers=Object.fromEntries(ROLES.map(role=>[role,{id:'peer-'+role,publicKey:exportPublicKey(signers[role])}]));
 const grant=signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,
  createdAt:now-86400000,workspace:{id:'synthetic-workspace',
   root:'/home/jenn/AGENTS_OS_Workspace/projects',dev:1,ino:2},channel:'main',actions:ACTIONS,peers},issuer);
 const r15=signed({schema:'r16.release.v1',id:'r16-daily-20261012-r15',issuedAt:now-86400000,
  notAfter:now+86400000,formats:['r16.workspace.v1'],versions:EXACT_R17_MIGRATION_SCOPE.sourceVersions,
  actions:ACTIONS,permissionVersion:1},releaseKey);
 const priorPublicConfig={schema:'r16.runtime-configuration.v1',
  issuerPublicKey:exportPublicKey(issuer),releasePublicKey:exportPublicKey(releaseKey),
  grant,release:r15,peers,versions:r15.body.versions,channel:'main'};
 const roots={schema:'mht.trust-roots.v1',grantId:grant.body.id,
  issuerPublicKey:exportPublicKey(issuer),releasePublicKey:exportPublicKey(releaseKey),
  enrollmentAuthorityPublicKey:exportPublicKey(enroller),releaseHash:digest(r15),
  handoffHash:digest('initial-bootstrap-pin'),installationProfile:profile};
 const physicalFiles=new Map();
 const nativeNames=['src/minimal-trust-issuer-once.mjs','src/systemd-issuer-credential.mjs',
  'src/minimal-trust-issuer.mjs','src/lease-core.mjs','src/control-clock.mjs',
  'authority/recovery-handoff.mjs','migration/r17-one-time-recovery-admission.mjs'];
 const artifacts=Object.fromEntries(ROLES.map(role=>{
  const names=physical&&role==='native'?nativeNames:[role+'/main.mjs'];
  const files=Object.fromEntries(names.map(name=>{
   const text='synthetic-byte-'+role+'-'+name;
   physicalFiles.set('/opt/r16/releases/r16-daily-20261012-r17/'+name,
    Buffer.from(JSON.stringify(text)));
   return [name,digest(text)];
  }));
  return [role,{schema:'r16.runtime-code.v1',role,entry:names[0],files}];
 }));
 const versions=Object.fromEntries(ROLES.map(role=>[role,runtimeVersion(artifacts[role],role)]));
 const reviewManifest={schema:'r16.reviewed-installation.v1',releaseId:'r16-daily-20261012-r17',
  issuedAt:approvedAt-1000,notAfter:approvedAt+86400000,artifacts,
  localFiles:ROLES.flatMap(role=>Object.entries(artifacts[role].files).map(([artifactPath,sha256])=>
   ({role,artifactPath,path:'/opt/r16/releases/r16-daily-20261012-r17/'+artifactPath,sha256})))};
 const r17=signed({schema:'r16.release.v1',id:reviewManifest.releaseId,
  issuedAt:reviewManifest.issuedAt,notAfter:reviewManifest.notAfter,formats:['r16.workspace.v1'],
  versions,actions:ACTIONS,permissionVersion:1},releaseKey);
 const projects=EXACT_R17_MIGRATION_SCOPE.projects.map(row=>{
  const project={id:row.projectId,workspaceId:grant.body.workspace.id,
   root:grant.body.workspace.root+'/'+row.projectId};
  const request={schema:'r16.prepare.v1',requestId:randomUUID(),grantId:grant.body.id,
   grantVersion:1,project,channel:'main',versions:r15.body.versions,
   actions:['find_symbol'],issuedAt:now-7200000};
  const lease=signed({schema:'r16.lease.v1',phase:'PREPARED',grantId:grant.body.id,
   grantVersion:1,grantHash:digest(grant),project,channel:'main',versions:r15.body.versions,
   actions:['find_symbol'],generation:row.generation,previousGeneration:row.generation-1,
   issuedAt:request.issuedAt,expiresAt:request.issuedAt+3600000,
   renewAt:request.issuedAt+2700000,requestId:request.requestId,releaseHash:digest(r15)},issuer);
  const evidence=Object.fromEntries(ROLES.map(role=>[role,signed({schema:'r16.close.v1',role,
   peerId:peers[role].id,grantId:grant.body.id,grantVersion:1,projectId:row.projectId,
   oldGeneration:row.generation-1,newGeneration:row.generation,leaseHash:digest(lease),
   requestId:request.requestId,durableClosed:true,pending:0,resultsHash:digest('prior-generation-results')},signers[role])]));
  const activation=signed({schema:'r16.activation.v1',grantId:grant.body.id,grantVersion:1,
   projectId:row.projectId,generation:row.generation,leaseHash:digest(lease),
   evidenceHash:digest(evidence),activatedAt:request.issuedAt+1000},issuer);
  const active={request,lease,release:r15,activation,evidence};
  return {projectId:row.projectId,generation:row.generation,active,pending:null,
   history:[structuredClone(active)]};
 });
 const snapshot={schema:1,revision:4,maxNow:now-1000,data:{kind:'r16.issuer.v1',
  grants:[{grant,version:1,status:'ACTIVE',projects,revocationAcks:[]}]}};
 const authorization={schema:'mht.first-trust-stage-authorization.v2',phase:'STAGE_ONLY',
  sourceReleaseId:r15.body.id,targetReleaseId:r17.body.id,grantId:grant.body.id,
  grantHash:digest(grant),grantVersion:1,r15PublicConfigDigest:digest(priorPublicConfig),
  reviewedManifestHash:digest(reviewManifest),recoveryEvidenceDigest:digest('historical-proof'),
  sourceFreezeDigest:digest('reviewed-source'),installerHash,
  issuerSnapshotHash:digest(snapshot.data),trustRootsDigest:digest(roots),
  stopEpoch:randomUUID(),handoffEpoch:1234,issuedAt:approvedAt-20000,expiresAt:approvedAt+60000,
  constraints:{...STAGE_CONSTRAINTS}};
 const plan={schema:'mht.first-trust-publisher-stage-plan.v2',authorization,humanProposalHash:digest('native-proposal')};
 const proposal=signed({schema:'mht.human-proposal.v1',action:'enroll_human',grantId:grant.body.id,
  expectedVersion:grant.body.version,expectedGrantHash:digest(grant),releaseId:r15.body.id,
  releaseHash:digest(r15),nonce:randomUUID(),issuedAt:authorization.issuedAt,expiresAt:authorization.expiresAt,
  target:{humanUid:1000,humanSubject:'local-human:1000',humanPublicKey:exportPublicKey(human),
   enrollmentExpiresAt:approvedAt+86400000,targetReleaseId:r17.body.id,reviewedManifestHash:digest(reviewManifest),
   stageAuthorizationHash:digest(authorization),stageAuthorization:authorization}},releaseKey);
 plan.humanProposalHash=digest(proposal);
 const policy={schema:'mht.human-pending-policy.v1',proposalHash:digest(proposal),grantId:grant.body.id,
  grantHash:digest(grant),grantVersion:1,releaseHash:digest(r15),releaseId:r15.body.id,
  humanPublicKey:exportPublicKey(human),workspaceId:grant.body.workspace.id,
  workspaceRoot:grant.body.workspace.root,workspaceDev:1,workspaceIno:2,installationProfile:profile};
 const checked=validateHumanProposal({proposal,policy,roots,now:approvedAt});
 const osIntent={schema:'mht.human-os-intent.v1',proposalHash:plan.humanProposalHash,
  peerUid:1000,processStart:321,confirmedAt:approvedAt-1000,challengeHash:digest('fresh-native-challenge')};
 const osResult={ok:true,status:'APPROVED_NOT_APPLIED',firstTrustOsConfirmationOnly:true,
  proposalHash:plan.humanProposalHash,reviewedIntent:firstTrustReviewedIntent(checked),approval:null};
 const journalBase='/var/lib/minimal-human-trust/human-approval/'+plan.humanProposalHash;
 const intent={schema:'mht.first-trust-signer-intent.v1',approvedAt,planHash:digest(plan),
  stageAuthorizationHash:digest(authorization),phase:'STAGE_ONLY',
  reviewedManifestHash:authorization.reviewedManifestHash,sourceFreezeDigest:authorization.sourceFreezeDigest,
  installerHash:authorization.installerHash,r15PublicConfigDigest:authorization.r15PublicConfigDigest,
  recoveryEvidenceDigest:authorization.recoveryEvidenceDigest,humanApprovalReceiptHash:digest({osIntent,osResult}),
  stopEpoch:authorization.stopEpoch,handoffEpoch:authorization.handoffEpoch,stopProofs:null,
  stopRequiredBeforeHandoff:true,grantId:grant.body.id,
  twoReadOperationIds:EXACT_R17_MIGRATION_SCOPE.projects.map(row=>row.operationId),
  sourceReleaseId:r15.body.id,targetReleaseId:r17.body.id};
 const enrollment=signed({schema:'mht.human-enrollment.v1',enrolledAt:approvedAt,
  expiresAt:approvedAt+86400000,grantId:grant.body.id,grantHash:digest(grant),
  humanPublicKey:exportPublicKey(human),humanUid:1000,humanSubject:'local-human:1000',
  releaseId:r17.body.id,releaseHash:digest(r17)},enroller);
 const signedArtifacts={schema:'mht.first-trust-staged-signatures.v2',status:'SIGNED_STAGED_NOT_INSTALLED',
  oldReleaseId:r15.body.id,reviewedManifestHash:digest(reviewManifest),
  osApprovalReceiptHash:intent.humanApprovalReceiptHash,firstTrustAdmissionDigest:digest('native-stage-admission'),
  stageAuthorizationHash:digest(authorization),release:r17,enrollment,grantUnchanged:true,
  mayInstall:false,mayActivateBusiness:false,mayHandoffIssuer:false,maySettleUnknown:false};
 const result={schema:'mht.first-trust-publisher-result.v1',intentHash:digest(intent),signedArtifacts};
 const publicConfig={...priorPublicConfig,release:r17,versions};
 const revision=88;
 const delivery=signed({schema:'r16.configuration-delivery.v1',revision,issuedAt:now-1000,
  publicConfig,control:{grantId:grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:false}},issuer);
 const expectedResultsHashes=Object.fromEntries(ROLES.map(role=>[role,digest('role-results-'+role)]));
 const receipts=Object.fromEntries(ROLES.map(role=>[role,signed({schema:'mht.business-stopped.v2',role,
  peerId:peers[role].id,grantId:grant.body.id,releaseId:r17.body.id,revision,
  reviewDigest:authorization.reviewedManifestHash,stopEpoch:authorization.stopEpoch,
  issuedAt:now-1000,expiresAt:now+12000,stopped:true,inflight:0,
  unresolved:EXACT_R17_MIGRATION_SCOPE.projects.map(row=>row.operationId),grantVersion:1,
  releaseHash:digest(r17),runtimeVersion:versions[role],resultsHash:expectedResultsHashes[role]},signers[role])]));
 const handoff=signed({schema:'mht.issuer-handoff.v1',grantId:grant.body.id,grantHash:digest(grant),
  releaseHash:digest(r17),issuerSnapshotHash:authorization.issuerSnapshotHash,
  installationProfile:profile,epoch:authorization.handoffEpoch,mode:'recovery_only',oldWriterClosed:true,
  participantClosureHashes:Object.fromEntries(ROLES.map(role=>[role,digest(receipts[role])])),
  issuedAt:now-1000,expiresAt:now+20000},enroller);
 const files=new Map([[PLAN,plan],[TX+'/intent.json',intent],[TX+'/result.json',result],
  ['/etc/minimal-human-trust/human-pending.json',proposal],
  ['/etc/minimal-human-trust/human-policy.json',policy],
  [journalBase+'.intent.json',osIntent],[journalBase+'.result.json',osResult],
  [OLD,snapshot],[NEXT,structuredClone(snapshot)]]);
 const reads=[];
 const readProtected=file=>{
  reads.push(file);if(physicalFiles.has(file))return physicalFiles.get(file);assert.ok(files.has(file),'only explicit fixed root paths are read: '+file);
  return Buffer.from(JSON.stringify(files.get(file)));
 };
 const args={priorPublicConfig,roots,reviewManifest,delivery,receipts,expectedRevision:revision,
  expectedResultsHashes,handoff,readProtected,
  readUnit:()=>({ActiveState:'inactive',SubState:'dead',MainPID:'0',UnitFileState:'masked'}),
  lockExists:()=>false,now,euid:0};
 return {args,files,reads,issuer,releaseKey,enroller,signers,authorization,plan,intent,result,r15,r17,snapshot,
  proposal,policy,osIntent,osResult,journalBase,physicalFiles};
}
