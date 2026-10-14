// Synthetic Ed25519 authorities and real user-owned temporary journal bytes.
// Fixed production path names are mapped only into this isolated fixture.
// No production proof, real Human/polkit ceremony, root key or service is used.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {generateKeyPairSync,randomUUID,createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {digest,signed,exportPublicKey,ROLES} from '../../src/lease-core.mjs';
import {runtimeVersion} from '../../authority/runtime-manifest.mjs';
import {REVIEWED_SOURCE_FILES} from '../../release/publisher-bootstrap.mjs';
import {inspectPublishedFirstTrustStage} from '../../release/staged-r17-handoff-admission.mjs';
import {validateHumanProposal,firstTrustReviewedIntent} from '../../human/approval-policy.mjs';
import {firstCutoverApprovalBody} from '../../authority/first-cutover-authorization.mjs';
import {deriveFirstCutoverTarget} from '../../human/first-cutover-admission.mjs';
import {stagedRecoveryFixture} from './staged-recovery-fixture.mjs';

const sha=b=>createHash('sha256').update(b).digest('hex');
export const FIRST_CUTOVER_PENDING='/etc/minimal-human-trust/first-cutover-human-pending.json';
export const FIRST_CUTOVER_POLICY='/etc/minimal-human-trust/first-cutover-human-policy.json';
export const STAGE_PLAN='/etc/minimal-human-trust/first-trust-publication.json';
export const STAGE_TX='/var/lib/minimal-human-trust/first-trust-publication';
export const SOURCE_FREEZE='/etc/minimal-human-trust/first-trust-code.json';
export const INSTALLER='/etc/minimal-human-trust/stage-installer-reviewed.mjs';
export const OLD_SNAPSHOT='/var/lib/r16-owner/issuer/state.json';

export function firstCutoverFixture(t){
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'mht-first-cutover-synthetic-'));
  fs.chmodSync(directory,0o700);
  t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
  const base=fileURLToPath(new URL('../../',import.meta.url));
  const sourceBytes=new Map(REVIEWED_SOURCE_FILES.map(name=>[name,fs.readFileSync(path.join(base,name))]));
  const installerBytes=fs.readFileSync(path.join(base,'release/stage-installer-reviewed.mjs'));
  const f=stagedRecoveryFixture({installerHash:sha(installerBytes)});
  const humanKey=generateKeyPairSync('ed25519').privateKey;
  const humanPublicKey=exportPublicKey(humanKey);
  const sourceFreeze={schema:'mht.first-trust-code-freeze.v1',sourceCommit:'a'.repeat(40),
    files:Object.fromEntries([...sourceBytes].map(([name,bytes])=>[name,sha(bytes)]))};
  // The sourceCommit is deliberately synthetic. The bytes and complete freeze
  // list are real current source bytes; this fixture claims no committed release.
  const reviewManifest=f.args.reviewManifest;
  for(const [name,bytes] of sourceBytes){
    reviewManifest.artifacts.native.files[name]=sha(bytes);
    f.physicalFiles.set('/opt/r16/releases/r16-daily-20261012-r17/'+name,bytes);
  }
  reviewManifest.localFiles=ROLES.flatMap(role=>Object.entries(reviewManifest.artifacts[role].files)
    .map(([artifactPath,sha256])=>({role,artifactPath,sha256,
      path:'/opt/r16/releases/r16-daily-20261012-r17/'+artifactPath})));
  const versions=Object.fromEntries(ROLES.map(role=>[role,runtimeVersion(reviewManifest.artifacts[role],role)]));
  f.r17=signed({...f.r17.body,versions},f.releaseKey);
  Object.assign(f.authorization,{reviewedManifestHash:digest(reviewManifest),
    sourceFreezeDigest:digest(sourceFreeze),installerHash:sha(installerBytes)});
  const stageBody=structuredClone(f.proposal.body);
  Object.assign(stageBody.target,{humanPublicKey,reviewedManifestHash:digest(reviewManifest),
    stageAuthorization:structuredClone(f.authorization),stageAuthorizationHash:digest(f.authorization)});
  f.proposal=signed(stageBody,f.releaseKey);
  f.policy.humanPublicKey=humanPublicKey;f.policy.proposalHash=digest(f.proposal);
  f.plan.humanProposalHash=digest(f.proposal);
  const oldJournal=f.journalBase;
  f.files.delete(oldJournal+'.intent.json');f.files.delete(oldJournal+'.result.json');
  f.journalBase='/var/lib/minimal-human-trust/human-approval/'+digest(f.proposal);
  f.osIntent={...f.osIntent,proposalHash:digest(f.proposal)};
  f.osResult={...f.osResult,proposalHash:digest(f.proposal),
    reviewedIntent:firstTrustReviewedIntent(validateHumanProposal({proposal:f.proposal,
      policy:f.policy,roots:f.args.roots,now:f.intent.approvedAt}))};
  Object.assign(f.intent,{planHash:digest(f.plan),stageAuthorizationHash:digest(f.authorization),
    reviewedManifestHash:digest(reviewManifest),sourceFreezeDigest:digest(sourceFreeze),
    installerHash:sha(installerBytes),humanApprovalReceiptHash:digest({osIntent:f.osIntent,osResult:f.osResult})});
  const enrollment=signed({...f.result.signedArtifacts.enrollment.body,humanPublicKey,
    releaseHash:digest(f.r17)},f.enroller);
  Object.assign(f.result.signedArtifacts,{release:f.r17,enrollment,
    stageAuthorizationHash:digest(f.authorization),reviewedManifestHash:digest(reviewManifest),
    osApprovalReceiptHash:f.intent.humanApprovalReceiptHash});
  f.result.intentHash=digest(f.intent);
  const publicConfig={...f.args.priorPublicConfig,release:f.r17,versions};
  f.args.delivery=signed({...f.args.delivery.body,publicConfig},f.issuer);
  for(const role of ROLES)f.args.receipts[role]=signed({...f.args.receipts[role].body,
    releaseHash:digest(f.r17),runtimeVersion:versions[role],reviewDigest:digest(reviewManifest)},f.signers[role]);
  Object.assign(f.admission,{stageAuthorizationHash:digest(f.authorization),
    reviewedManifestHash:digest(reviewManifest)});
  f.args.handoff=signed({...f.args.handoff.body,releaseHash:digest(f.r17),
    recoveryAdmission:f.admission,
    participantClosureHashes:Object.fromEntries(ROLES.map(role=>[role,digest(f.args.receipts[role])]))},f.enroller);
  f.files.set(STAGE_PLAN,f.plan);f.files.set(STAGE_TX+'/intent.json',f.intent);
  f.files.set(STAGE_TX+'/result.json',f.result);
  f.files.set('/etc/minimal-human-trust/human-pending.json',f.proposal);
  f.files.set('/etc/minimal-human-trust/human-policy.json',f.policy);
  f.files.set(f.journalBase+'.intent.json',f.osIntent);f.files.set(f.journalBase+'.result.json',f.osResult);

  const protectedFiles=new Map(),reads=[];
  const writeBytes=(logical,bytes)=>{
    assert.equal(path.posix.normalize(logical),logical);
    assert.ok(logical.startsWith('/'));
    const physical=path.join(directory,'protected',logical.slice(1));
    assert.ok(physical.startsWith(directory+'/protected/'));
    fs.mkdirSync(path.dirname(physical),{recursive:true,mode:0o700});
    const fd=fs.openSync(physical,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_TRUNC|fs.constants.O_NOFOLLOW,0o600);
    try{fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
    const parent=fs.openSync(path.dirname(physical),fs.constants.O_RDONLY|fs.constants.O_DIRECTORY);
    try{fs.fsyncSync(parent);}finally{fs.closeSync(parent);}
    protectedFiles.set(logical,physical);return physical;
  };
  const writeJson=(logical,value)=>writeBytes(logical,Buffer.from(JSON.stringify(value)));
  const readProtected=logical=>{
    assert.ok(protectedFiles.has(logical),'only explicit fixture logical paths may be read: '+logical);
    reads.push(logical);
    const physical=protectedFiles.get(logical),st=fs.lstatSync(physical);
    assert.ok(st.isFile()&&!st.isSymbolicLink()&&st.nlink===1&&(st.mode&0o022)===0);
    const fd=fs.openSync(physical,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
    try{return fs.readFileSync(fd);}finally{fs.closeSync(fd);}
  };
  const readJson=logical=>JSON.parse(readProtected(logical));
  for(const [logical,value] of f.files)writeJson(logical,value);
  for(const [logical,bytes] of f.physicalFiles)writeBytes(logical,bytes);
  for(const [name,bytes] of sourceBytes)writeBytes('/usr/lib/minimal-human-trust/'+name,bytes);
  writeJson(SOURCE_FREEZE,sourceFreeze);writeBytes(INSTALLER,installerBytes);
  f.args.readProtected=readProtected;
  let time=f.args.now;
  const stageArgs={priorPublicConfig:f.args.priorPublicConfig,roots:f.args.roots,reviewManifest,
    readProtected,euid:0,now:time};
  const stage=inspectPublishedFirstTrustStage(stageArgs);
  const target=deriveFirstCutoverTarget({stage,roots:f.args.roots,wrapper:f.snapshot,sourceFreeze});
  const body={schema:'mht.human-proposal.v1',action:'first_cutover_handoff',grantId:f.args.priorPublicConfig.grant.body.id,
    expectedVersion:1,expectedGrantHash:digest(f.args.priorPublicConfig.grant),
    releaseId:f.r15.body.id,releaseHash:digest(f.r15),nonce:randomUUID(),
    issuedAt:time-3000,expiresAt:time+60000,target};
  let proposal=signed(body,f.releaseKey);
  const policy={...f.policy,proposalHash:digest(proposal)};
  const approvedAt=time-2000;
  let journalBase,osIntent,osResult,approval;
  const journalize=()=>{
    policy.proposalHash=digest(proposal);
    writeJson(FIRST_CUTOVER_PENDING,proposal);writeJson(FIRST_CUTOVER_POLICY,policy);
    const checked=validateHumanProposal({proposal,policy,roots:f.args.roots,now:approvedAt});
    approval=signed(firstCutoverApprovalBody(checked,{now:approvedAt}),humanKey);
    journalBase='/var/lib/minimal-human-trust/human-approval/'+digest(proposal);
    osIntent={schema:'mht.human-os-intent.v1',proposalHash:digest(proposal),peerUid:1000,
      processStart:765,confirmedAt:approvedAt-1,challengeHash:digest('synthetic-cutover-challenge')};
    osResult={ok:true,status:'APPROVED_NOT_APPLIED',proposalHash:digest(proposal),approval};
    writeJson(journalBase+'.intent.json',osIntent);writeJson(journalBase+'.result.json',osResult);
  };
  journalize();
  const humanArgs=()=>({proposal,policy,roots:f.args.roots,priorPublicConfig:f.args.priorPublicConfig,
    reviewManifest,readProtected,now:time,euid:0});
  const resignProposal=patch=>{
    proposal=signed({...proposal.body,...patch},f.releaseKey);
    policy.proposalHash=digest(proposal);
    writeJson(FIRST_CUTOVER_PENDING,proposal);writeJson(FIRST_CUTOVER_POLICY,policy);
    return proposal;
  };
  return {f,directory,sourceFreeze,stage,target,humanKey,humanPublicKey,approvedAt,
    readProtected,readJson,writeJson,writeBytes,protectedFiles,reads,humanArgs,
    now:()=>time,setNow:value=>{time=value;},resignProposal,journalize,
    get proposal(){return proposal;},policy,get journalBase(){return journalBase;},
    get osIntent(){return osIntent;},get osResult(){return osResult;},get approval(){return approval;},
    finalRoots:()=>({...proposal.body.target.newRootTemplate,handoffHash:digest(f.args.handoff)}),
  };
}
