// Isolated cutover rehearsal, NOT a production installer or a credential loader.
// The first native Human cutover gate is not implemented yet. In particular,
// STAGE_ONLY consent cannot authorize installation or an enrollment-root handoff.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {canonical,digest,verified,ROLES} from '../src/lease-core.mjs';
import {replayInitialState} from '../src/minimal-trust-issuer.mjs';
import {validateInstalledTrustPolicy} from '../src/minimal-trust-issuer-once.mjs';
import {inspectReviewedTrustRuntime} from '../src/trusted-launcher.mjs';
import {verifyInstalledManifest} from '../authority/runtime-manifest.mjs';
import {deriveExactR17Release} from './first-trust-release-builder.mjs';
import {inspectStagedR17HandoffAdmission} from './staged-r17-handoff-admission.mjs';
import {runCutoverTransaction} from './cutover-transaction.mjs';
import {inspectFirstCutoverHandoffAdmission} from '../human/first-cutover-admission.mjs';

const need=(ok,code)=>{if(!ok)throw Object.assign(new Error(code),{code});};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const bytes=value=>Buffer.from(canonical(value)+'\n');
const copy=value=>JSON.parse(canonical(value));
export const productionCutoverGate=()=>Object.freeze({
  status:'PENDING_EXACT_NATIVE_HUMAN_CUTOVER_AUTHORIZATION',
  mayInstall:false,mayStartIssuer:false,mayActivateBusiness:false,maySettleUnknown:false,
});

export function isolatedCutoverLayout(directory){
  need(typeof directory==='string'&&path.isAbsolute(directory)&&path.normalize(directory)===directory&&
    directory.startsWith('/tmp/')&&fs.realpathSync(directory)===directory&&
    process.geteuid()!==0,'ISOLATED_REHEARSAL_DIRECTORY');
  const st=fs.lstatSync(directory);
  need(st.isDirectory()&&st.uid===process.geteuid()&&(st.mode&0o7777)===0o700,
    'ISOLATED_REHEARSAL_DIRECTORY');
  const installed=directory+'/installed';
  for(const child of ['transaction','installed','installed/issuer','installed/replay']){
    const name=directory+'/'+child;
    if(fs.existsSync(name)){
      const s=fs.lstatSync(name);
      need(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===process.geteuid()&&
        (s.mode&0o7777)===0o700,'ISOLATED_REHEARSAL_DIRECTORY');
    }
  }
  return Object.freeze({transaction:directory+'/transaction',installed,
    issuerState:installed+'/issuer/state.json',replayState:installed+'/replay/state.json',
    stageRootsArchive:installed+'/stage-trust-roots.json',roots:installed+'/trust-roots.json',
    issuerConfig:installed+'/issuer.json',receipt:installed+'/handoff-cutover.receipt.json',
    ...Object.fromEntries(ROLES.map(role=>[role+'Manifest',installed+'/'+role+'-manifest.json']))});
}

/** Signed inputs are supplied by a synthetic fixture or an independently
 * prepared isolated publisher. No signing occurs here. All file destinations
 * are derived beneath one private /tmp directory; no production file is opened
 * by this module. The mandatory read callbacks have no real-OS default.
 */
export function rehearseRecoveryCutover({directory,handoffArgs,now=Date.now,fault=()=>{},firstCutoverHumanArgs=null}){
  const layout=isolatedCutoverLayout(directory);
  need(handoffArgs?.roots?.installationProfile==='isolated'&&
    handoffArgs.handoff?.body?.schema==='mht.issuer-handoff.v2'&&
    ['readProtected','readUnit','lockExists'].every(k=>typeof handoffArgs[k]==='function')&&
    typeof now==='function'&&typeof fault==='function','ISOLATED_REHEARSAL_ONLY');
  const roots=copy(handoffArgs.roots),review=copy(handoffArgs.reviewManifest);
  const sourceGrant=copy(handoffArgs.priorPublicConfig.grant),handoff=copy(handoffArgs.handoff);
  const intendedFinalRoots={...roots,releaseHash:handoff.body.releaseHash,handoffHash:digest(handoff)};
  let nativeHumanAdmission=null;
  const journal=layout.transaction+'/INTENT.json';
  let savedIdentity=null;
  if(fs.existsSync(journal)){
    const fd=fs.openSync(journal,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
    try{
      const st=fs.fstatSync(fd);
      need(st.isFile()&&st.nlink===1&&st.uid===process.geteuid()&&
        (st.mode&0o7777)===0o600&&st.size<=64*1024*1024,'ISOLATED_REHEARSAL_INTENT_DRIFT');
      savedIdentity=JSON.parse(fs.readFileSync(fd)).identity;
    }finally{fs.closeSync(fd);}
  }
  const recorded=fs.existsSync(layout.transaction+'/COMMIT.json');
  // Historical RESULT readback grants no authority and never restores a ledger
  // that has subsequently advanced. Live recovery continues to use now().
  const firstNow=recorded?savedIdentity?.issuedAt:now();
  const inspect=at=>{
    const value=inspectStagedR17HandoffAdmission({...handoffArgs,now:at});
    need(digest(handoffArgs.roots)===digest(roots)&&digest(handoffArgs.reviewManifest)===digest(review)&&
      digest(handoffArgs.handoff)===digest(handoff)&&
      digest(handoffArgs.priorPublicConfig.grant)===digest(sourceGrant),
      'ISOLATED_REHEARSAL_INPUT_DRIFT');
    if(firstCutoverHumanArgs){
      const fresh=inspectFirstCutoverHandoffAdmission({humanArgs:firstCutoverHumanArgs,
        finalRoots:intendedFinalRoots,handoffArgs,now:at});
      need(nativeHumanAdmission===null||digest(fresh)===digest(nativeHumanAdmission),
        'ISOLATED_REHEARSAL_HUMAN_DRIFT');
      nativeHumanAdmission=fresh;
    }
    return value;
  };
  // Physical file coverage and all signed stage/STOP/snapshot gates pass before
  // even creating the private target directories. This does not attest a real
  // OS stop or Human identity; the receipt states that limit explicitly.
  const inspection=inspect(firstNow);
  const read=handoffArgs.readProtected;
  const result=JSON.parse(read('/var/lib/minimal-human-trust/first-trust-publication/result.json'));
  const staged=result.signedArtifacts;
  const sourceRelease=verified(handoffArgs.priorPublicConfig.release,roots.releasePublicKey,'r16.release.v1');
  const derived=deriveExactR17Release({sourceRelease,reviewManifest:review,
    reviewedManifestHash:inspection.reviewedManifestHash,now:review.issuedAt,readFile:read});
  need(canonical(derived)===canonical(staged.release.body),'ISOLATED_REHEARSAL_RELEASE_DRIFT');
  const wrapper=JSON.parse(read('/var/lib/r16-owner/issuer/state.json'));
  const activeRoots={...roots,releaseHash:digest(staged.release),handoffHash:digest(handoff)};
  const config={schema:'mht.installed-issuer.v1',trustCutoverPhase:'RECOVERY_SHADOW',mode:'recovery_only',
    grantId:roots.grantId,issuerPublicKey:roots.issuerPublicKey,releasePublicKey:roots.releasePublicKey,
    enrollmentAuthorityPublicKey:roots.enrollmentAuthorityPublicKey,
    humanAuthorityPublicKey:staged.enrollment.body.humanPublicKey,
    release:staged.release,enrollment:staged.enrollment,handoff};
  validateInstalledTrustPolicy(config,{trustRoots:activeRoots,now:firstNow});
  const prospectiveRead=file=>file==='/etc/minimal-human-trust/issuer.json'?bytes(config):
    file==='/etc/minimal-human-trust/trust-roots.json'?bytes(activeRoots):
    file==='/opt/r16/releases/'+review.releaseId+'/native-manifest.json'?bytes(review.artifacts.native):read(file);
  inspectReviewedTrustRuntime({euid:0,now:()=>firstNow,readFile:prospectiveRead,
    verify:(m,dir,o)=>verifyInstalledManifest(m,dir,{...o,readFile:prospectiveRead})});
  const expiresAt=Math.min(handoff.body.expiresAt,nativeHumanAdmission?.expiresAt??Infinity,
    ...ROLES.map(role=>handoffArgs.receipts[role].body.expiresAt));
  const identity={schema:'mht.cutover-intent.v1',issuedAt:firstNow,expiresAt,
    profile:'ISOLATED_REHEARSAL_ONLY',handoffHash:digest(handoff),
    stageIntentHash:inspection.stageIntentHash,stageResultHash:inspection.stageResultHash,
    recoveryAdmissionHash:digest(handoff.body.recoveryAdmission),
    issuerStateFileHash:digest(wrapper),reviewedManifestHash:digest(review),
    ...(nativeHumanAdmission?{nativeHumanAdmission}: {})};
  // Stable preparation identity is recovered from the durable journal; its
  // window is never silently extended after a partial attempt.
  let originalIdentity=identity;
  if(savedIdentity){
    const expected={...identity,issuedAt:savedIdentity.issuedAt};
    need(canonical(savedIdentity)===canonical(expected),'ISOLATED_REHEARSAL_INTENT_DRIFT');
    originalIdentity=savedIdentity;
  }
  const receipt={schema:'mht.isolated-cutover-rehearsal-receipt.v1',
    status:'RECOVERY_SHADOW_REHEARSED_NOT_INSTALLED',handoffHash:digest(handoff),
    issuerSnapshotHash:digest(wrapper.data),issuerStateFileHash:digest(wrapper),
    stageIntentHash:inspection.stageIntentHash,stageResultHash:inspection.stageResultHash,
    realHumanEnrolled:false,realOsStopAttested:false,productionChanged:false,
    mayActivateBusiness:false,maySettleUnknown:false,mayReplayUnknown:false,
    ...(nativeHumanAdmission?{nativeHumanAdmission}: {})};
  const values={issuerState:wrapper,replayState:{schema:1,revision:0,maxNow:0,data:replayInitialState()},
    stageRootsArchive:roots,roots:activeRoots,issuerConfig:config,receipt,
    ...Object.fromEntries(ROLES.map(role=>[role+'Manifest',review.artifacts[role]]))};
  const plannedTargets=Object.keys(values).map(slot=>({slot,path:layout[slot],
    mode:slot.endsWith('Manifest')?0o644:0o600,
    beforeSha256:slot==='roots'?sha(bytes(roots)):null}));
  const artifacts={schema:'mht.cutover-artifacts.v1',files:plannedTargets.map(spec=>
    ({...spec,bytesBase64:bytes(values[spec.slot]).toString('base64')})),
    evidence:{handoff,inspection,receipt,...(nativeHumanAdmission?{nativeHumanAdmission}: {})}};
  const artifactHash=digest(artifacts);
  for(const dir of [layout.transaction,layout.installed,layout.installed+'/issuer',layout.installed+'/replay']){
    if(!fs.existsSync(dir))fs.mkdirSync(dir,{mode:0o700});
  }
  const checkArtifacts=candidate=>digest(candidate)===artifactHash;
  const transaction=runCutoverTransaction({directory:layout.transaction,identity:originalIdentity,
    plannedTargets,now,fault,
    preflight:context=>{if(context.phase!=='RECORDED')inspect(now());return true;},
    guard:()=>{inspect(now());return true;},
    produceArtifacts:()=>artifacts,validateArtifacts:checkArtifacts,
    verifyCommit:()=>{
      const cfg=JSON.parse(fs.readFileSync(layout.issuerConfig));
      const currentRoots=JSON.parse(fs.readFileSync(layout.roots));
      validateInstalledTrustPolicy(cfg,{trustRoots:currentRoots,now:now()});
      return sha(fs.readFileSync(layout.issuerState))===sha(bytes(wrapper));
    },
  });
  return Object.freeze({...receipt,transaction,layout,mayInstall:false,mayStartIssuer:false});
}

export function rehearseFirstNativeHumanCutover({humanArgs,...args}={}){
  need(humanArgs&&typeof humanArgs==='object','ISOLATED_REHEARSAL_HUMAN_REQUIRED');
  return rehearseRecoveryCutover({...args,firstCutoverHumanArgs:humanArgs});
}

if(process.argv[1]===fileURLToPath(import.meta.url)){
  process.stdout.write(JSON.stringify(productionCutoverGate())+'\n');
  process.exitCode=1;
}
