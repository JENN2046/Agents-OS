// Synthetic cryptographic receiver fixture only. Production operation hashes
// are immutable contract labels here; these test keys do NOT re-sign or prove
// either original production operation, nor establish a real Human identity.
import {generateKeyPairSync,randomUUID} from 'node:crypto';
import {signed,exportPublicKey,digest,ACTIONS,ROLES,LEASE_MS,RENEW_BEFORE_MS}
 from '../../src/lease-core.mjs';
import {EXACT_R17_MIGRATION_SCOPE} from '../../migration/r17-one-time-recovery-admission.mjs';
const pair=()=>generateKeyPairSync('ed25519').privateKey;
const pin=EXACT_R17_MIGRATION_SCOPE;

export function sealRecoveryHandoff(f){
 f.admission.issuerSnapshotHash=digest(f.wrapper.data);
 f.admission.issuerStateFileHash=digest(f.wrapper);
 f.handoff=signed({...f.handoff.body,issuerSnapshotHash:f.admission.issuerSnapshotHash,
  recoveryAdmission:f.admission},f.keys.enrollment);
 f.config.handoff=f.handoff;f.roots.handoffHash=digest(f.handoff);
 return f;
}
export function recoveryHandoffFixture({now=1792400000000}={}){
 const keys={issuer:pair(),release:pair(),enrollment:pair(),human:pair()};
 const signers=Object.fromEntries(ROLES.map(role=>[role,pair()]));
 const peers=Object.fromEntries(ROLES.map(role=>[role,{id:'peer-'+role,publicKey:exportPublicKey(signers[role])}]));
 const workspace={id:'ws-synthetic-recovery',root:'/home/jenn/AGENTS_OS_Workspace/projects',dev:1,ino:2};
 const grant=signed({schema:'r16.workspace.v1',id:pin.grantId,version:1,createdAt:now-2*86400000,
  workspace,channel:'main',actions:ACTIONS,peers},keys.issuer);
 const r15=signed({schema:'r16.release.v1',id:pin.sourceRelease,issuedAt:now-86400000,
  notAfter:now+7*86400000,formats:['r16.workspace.v1'],versions:pin.sourceVersions,
  actions:ACTIONS,permissionVersion:1},keys.release);
 const r17=signed({...r15.body,id:pin.targetRelease,issuedAt:now-10000,notAfter:now+86400000,
  versions:Object.fromEntries(ROLES.map(role=>[role,digest('synthetic-r17-'+role)]))},keys.release);
 const makeProject=({projectId,generation})=>{
  const project={id:projectId,workspaceId:workspace.id,root:workspace.root+'/'+projectId};
  const issuedAt=now-LEASE_MS-1000,requestId='synthetic-prepare-'+projectId;
  const request={schema:'r16.prepare.v1',requestId,grantId:grant.body.id,grantVersion:1,
   project,channel:'main',versions:pin.sourceVersions,actions:['find_symbol'],issuedAt};
  const lease=signed({schema:'r16.lease.v1',phase:'PREPARED',grantId:grant.body.id,
   grantVersion:1,grantHash:digest(grant),project,channel:'main',versions:pin.sourceVersions,
   actions:['find_symbol'],generation,previousGeneration:generation-1,issuedAt,
   expiresAt:issuedAt+LEASE_MS,renewAt:issuedAt+LEASE_MS-RENEW_BEFORE_MS,
   requestId,releaseHash:digest(r15)},keys.issuer);
  const evidence=Object.fromEntries(ROLES.map(role=>[role,signed({schema:'r16.close.v1',role,
   peerId:peers[role].id,grantId:grant.body.id,grantVersion:1,projectId,
   oldGeneration:generation-1,newGeneration:generation,leaseHash:digest(lease),requestId,
   durableClosed:true,pending:0,resultsHash:digest('historical-results-'+projectId)},signers[role])]));
  const activation=signed({schema:'r16.activation.v1',grantId:grant.body.id,grantVersion:1,
   projectId,generation,leaseHash:digest(lease),evidenceHash:digest(evidence),activatedAt:issuedAt+100},keys.issuer);
  const active={request,lease,release:r15,activation,evidence};
  return {projectId,generation,active,pending:null,history:[structuredClone(active)]};
 };
 const projects=pin.projects.map(makeProject);
 const wrapper={schema:1,revision:71,maxNow:now-LEASE_MS+100,
  data:{kind:'r16.issuer.v1',grants:[{grant,version:1,status:'ACTIVE',projects,revocationAcks:[]}]}};
 const admission={schema:'mht.r17-recovery-handoff-admission.v1',sourceReleaseId:pin.sourceRelease,
  sourceReleaseHash:digest(r15),targetReleaseId:pin.targetRelease,
  stageAuthorizationHash:digest('synthetic-stage-core'),reviewedManifestHash:digest('synthetic-r17-review'),
  recoveryEvidenceDigest:digest('synthetic-source-evidence'),issuerSnapshotHash:digest(wrapper.data),
  issuerStateFileHash:digest(wrapper),observedAt:now-1000,
  operations:pin.projects.map((row,index)=>({projectId:row.projectId,operationId:row.operationId,
   operationHash:row.operationHash,generation:row.generation,leaseHash:digest(projects[index].active.lease),
   action:'find_symbol',outcome:'UNRESOLVED',originalResultAvailable:false,replayAllowed:false}))};
 const handoff=signed({schema:'mht.issuer-handoff.v2',grantId:grant.body.id,grantHash:digest(grant),
  releaseHash:digest(r17),issuerSnapshotHash:admission.issuerSnapshotHash,installationProfile:'isolated',
  epoch:1234,mode:'recovery_only',oldWriterClosed:true,
  participantClosureHashes:Object.fromEntries(ROLES.map(role=>[role,digest('synthetic-stop-'+role)])),
  issuedAt:now-500,expiresAt:now+20000,recoveryAdmission:admission},keys.enrollment);
 const enrollment=signed({schema:'mht.human-enrollment.v1',enrolledAt:now-9000,
  expiresAt:now+86400000,grantId:grant.body.id,grantHash:digest(grant),
  humanPublicKey:exportPublicKey(keys.human),humanUid:1000,humanSubject:'local-human:1000',
  releaseHash:digest(r17),releaseId:r17.body.id},keys.enrollment);
 const roots={schema:'mht.trust-roots.v1',grantId:grant.body.id,
  issuerPublicKey:exportPublicKey(keys.issuer),releasePublicKey:exportPublicKey(keys.release),
  enrollmentAuthorityPublicKey:exportPublicKey(keys.enrollment),releaseHash:digest(r17),
  handoffHash:digest(handoff),installationProfile:'isolated'};
 const config={schema:'mht.installed-issuer.v1',trustCutoverPhase:'RECOVERY_SHADOW',mode:'recovery_only',
  grantId:grant.body.id,issuerPublicKey:roots.issuerPublicKey,releasePublicKey:roots.releasePublicKey,
  enrollmentAuthorityPublicKey:roots.enrollmentAuthorityPublicKey,humanAuthorityPublicKey:exportPublicKey(keys.human),
  release:r17,enrollment,handoff};
 const unknownProjection=pin.projects.map(row=>({...row,status:'UNKNOWN',replayAllowed:false}));
 const f={now,keys,grant,r15,r17,wrapper,admission,handoff,enrollment,config,roots,signers,peers,workspace,
  projects,makeProject,unknownProjection,productionEvidenceVerified:false};
 f.envelope=(action,payload={},role='native')=>signed({schema:'r16.issuer-call.v1',role,
  peerId:peers[role].id,issuedAt:f.now,nonce:randomUUID(),action,payload},signers[role]);
 f.binding=()=>({handoffHash:digest(f.handoff),issuerSnapshotHash:f.handoff.body.issuerSnapshotHash,
  epoch:f.handoff.body.epoch,admissionExpiresAt:f.handoff.body.expiresAt,recoveryHandoff:f.handoff});
 f.closedProject=(projectId='synthetic-closed-project')=>{
  const project=makeProject({projectId,generation:1}),lease=project.active.lease;
  const stopEvidence=Object.fromEntries(ROLES.map(role=>[role,signed({schema:'r16.stopped.v1',role,
   peerId:peers[role].id,grantId:grant.body.id,grantVersion:1,projectId,generation:1,
   leaseHash:digest(lease),requestId:lease.body.requestId,durableClosed:true,pending:0,
   resultsHash:digest('closed-results-'+projectId)},signers[role])]));
  const closed=signed({schema:'r16.closed.v1',grantId:grant.body.id,projectId,generation:1,
   leaseHash:digest(lease),evidenceHash:digest(stopEvidence),closedAt:now-5000},keys.issuer);
  project.history.push({...structuredClone(project.active),closed,stopEvidence});project.active=null;
  return project;
 };
 return f;
}
