// G1 source candidate. This is a narrow issuer adapter, NOT a privileged
// service. A real root-owned, credential-bound activation entrypoint is still
// required before this may replace the R16 Owner daemon.
import {
  ProtectedStore, createIssuer, issuerInitialState, exportPublicKey,
  canonical, digest, verified, verifyRelease, ROLES
} from './lease-core.mjs';
import {verifyRecoveryHandoff,inspectRecoveryIssuerSnapshot}
  from '../authority/recovery-handoff.mjs';

const MAX_INPUT_BYTES=262144;
const nonceRE=/^[A-Za-z0-9_-]{16,128}$/;
const fail=(code)=>{throw Object.assign(new Error(code),{code});};
const ensure=(ok,code='TRUST_REFUSED')=>{if(!ok)fail(code);};
const equal=(a,b)=>canonical(a)===canonical(b);
const exact=(a,keys)=>ensure(a!==null&&typeof a==='object'&&!Array.isArray(a)&&
  equal(Object.keys(a).sort(),keys.slice().sort()),'TRUST_INPUT_SHAPE');
const trustedActionNames=Object.freeze([
  'fresh','prepare','prepareStatus','activate','closeLease',
  'acknowledgeRevocation','grant','heartbeat','nonceStatus'
]);
const cleanupActions=new Set([
  'grant','fresh','prepareStatus','closeLease','acknowledgeRevocation','heartbeat','nonceStatus'
]);
export const replayInitialState=()=>({kind:'mht.issuer-replay.v2',used:[],handoff:null});
const readOnlyActions=new Set(['grant','fresh','prepareStatus','heartbeat','nonceStatus','revoke_status']);
function replayEntries(store){
  ensure(store instanceof ProtectedStore,'TRUST_REPLAY_STORE');
  const s=store.snapshot();
  ensure(s.kind==='mht.issuer-replay.v2'&&Array.isArray(s.used)&&s.used.length<=4096,'REPLAY_LEDGER_INVALID');
  for(const e of s.used)ensure(typeof e.id==='string'&&['INTENT','RESULT'].includes(e.phase)&&
    /^[a-f0-9]{64}$/.test(e.requestHash)&&/^[a-f0-9]{64}$/.test(e.effectHash)&&
    Number.isSafeInteger(e.at)&&typeof e.kind==='string'&&
    (e.phase!=='RESULT'||digest(e.result)===e.resultHash),'REPLAY_LEDGER_INVALID');
  ensure(new Set(s.used.map(e=>e.id)).size===s.used.length,'REPLAY_LEDGER_INVALID');
  return s.used;
}
function fencedEffect(store,identity,nonce,now,kind,request,effect,fault){
  ensure(typeof identity==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(identity)&&
    typeof nonce==='string'&&nonceRE.test(nonce),'REPLAY_ID');
  const id=identity+':'+nonce,requestHash=digest(request),effectHash=digest({kind,payload:request.body?.payload??request.body});
  const entries=replayEntries(store);
  ensure(!entries.some(e=>e.id===id),'REPLAY_REJECTED');
  // Unknown effects never age out or become permission to repeat a write.
  ensure(readOnlyActions.has(kind)||!entries.some(e=>e.phase==='INTENT'&&!readOnlyActions.has(e.kind)&&
    (kind!=='revoke_grant'||e.kind==='revoke_grant')),
    'ISSUER_RECOVERY_REQUIRED');
  store.transact(s=>{
    s.used=s.used.filter(e=>e.phase==='INTENT'||e.at>=now-180000);
    ensure(s.used.length<4096,'REPLAY_RATE_LIMITED');
    s.used.push({id,at:now,kind,requestHash,effectHash,phase:'INTENT'});
  });
  fault('after_intent');
  const result=effect();
  fault('after_effect');
  store.transact(s=>{
    const entry=s.used.find(e=>e.id===id);
    ensure(entry?.phase==='INTENT'&&entry.requestHash===requestHash,'REPLAY_LEDGER_INVALID');
    Object.assign(entry,{phase:'RESULT',result,resultHash:digest(result)});
  });
  fault('after_result');
  return result;
}
export function createMinimalTrustIssuer({
  issuerStore,replayStore,issuerPrivateKey,releasePublicKey,
  issuerPublicKey,grantId,release,resolveProject,
  humanAuthorityPublicKey,expectedGrantHash=null,mode='active',now=Date.now,fault=()=>{},
}){
  ensure(issuerStore instanceof ProtectedStore &&
    issuerStore.snapshot().kind==='r16.issuer.v1','ISSUER_STORE_INVALID');
  ensure(typeof resolveProject==='function'&&typeof now==='function'&&typeof fault==='function','TRUST_RUNTIME_INVALID');
  replayEntries(replayStore);
  ensure(['active','recovery_only','halted'].includes(mode),'TRUST_MODE_INVALID');
  ensure(exportPublicKey(issuerPrivateKey)===issuerPublicKey,'ISSUER_KEY_MISMATCH');
  const trustedRelease=verified(release,releasePublicKey,'r16.release.v1');
  const state=issuerStore.snapshot();
  ensure(Array.isArray(state.grants)&&state.grants.length===1,'TRUST_GRANT_CARDINALITY');
  const entry=state.grants[0];
  const grant=entry.grant;
  if(expectedGrantHash!==null)ensure(digest(grant)===expectedGrantHash,'GRANT_HASH_BINDING');
  const g=verified(grant,issuerPublicKey,'r16.workspace.v1');
  ensure(g.id===grantId&&entry.version>=g.version&&
    ['ACTIVE','REVOKED'].includes(entry.status),'GRANT_BINDING');
  // Recovery authenticates the exact pinned historical release without
  // extending its business validity. New lease issuance stays denied.
  ensure(trustedRelease.issuedAt<=now(),'RELEASE_NOT_YET_VALID');
  verifyRelease(release,releasePublicKey,{versions:trustedRelease.versions,actions:g.actions,
    now:mode==='active'?now():trustedRelease.issuedAt});
  ensure(trustedRelease.permissionVersion===1,'RELEASE_PERMISSION_VERSION');
  const secretApproval=Object.freeze({});
  const issuer=createIssuer({
    store:issuerStore,signingKey:issuerPrivateKey,releaseKey:releasePublicKey,
    resolveProject,
    authorizeOwner:({approval,action,target})=>
      approval===secretApproval&&action==='revoke_grant'&&target.grantId===g.id,
  });
  // A role cannot manufacture new grants or administrative confirmation.
  function issue(envelope) {
    ensure(mode!=='halted','TRUST_HALTED');
    ensure(Buffer.byteLength(canonical(envelope))<=MAX_INPUT_BYTES,'REQUEST_TOO_LARGE');
    const claimed=envelope?.body;
    ensure(ROLES.includes(claimed?.role),'PAIRING_FAILED');
    const b=verified(envelope,g.peers[claimed.role].publicKey,'r16.issuer-call.v1');
    exact(b,['schema','role','peerId','issuedAt','nonce','action','payload']);
    const t=now();
    ensure(Number.isSafeInteger(b.issuedAt)&&b.issuedAt<=t&&t-b.issuedAt<=30000,'STALE_REQUEST');
    ensure(b.peerId===g.peers[b.role].id&&nonceRE.test(b.nonce),'PAIRING_FAILED');
    ensure(trustedActionNames.includes(b.action),'ISSUER_ACTION');
    ensure(mode==='active'||cleanupActions.has(b.action),'RECOVERY_ONLY');
    const fresh=issuerStore.snapshot().grants[0];
    ensure(equal(fresh.grant,grant)&&fresh.version>=g.version,'GRANT_DRIFT');
    if(['prepare','activate'].includes(b.action))
      ensure(fresh.status==='ACTIVE'&&mode==='active','TRUST_NOT_ACTIVE');
    // Native transports signed App/Bridge proofs over the local socket. It
    // may relay them, but never supplies the inner role's authority itself.
    function innerProof(envelope,schema){
      const role=envelope?.body?.role;
      ensure(ROLES.includes(role),'ROLE_BINDING');
      ensure(b.role==='native'||role===b.role,'ROLE_BINDING');
      const proof=verified(envelope,g.peers[role].publicKey,schema);
      ensure(proof.peerId===g.peers[role].id,'ROLE_BINDING');
      return proof;
    }
    if(b.action==='fresh')innerProof(b.payload?.request,'r16.fresh-request.v1');
    if(b.action==='acknowledgeRevocation')innerProof(b.payload?.proof,'r16.revocation-ack.v1');
    const shapes={grant:[],fresh:['request'],prepare:['grantId','request','proofs','release'],
      prepareStatus:['grantId','request','proofs','release','queryId','queryIssuedAt'],
      activate:['grantId','projectId','evidence'],closeLease:['grantId','projectId','lease','evidence'],
      acknowledgeRevocation:['proof'],heartbeat:['report'],nonceStatus:['nonce','requestHash']};
    exact(b.payload,shapes[b.action]);
    // Reject readily decidable malformed input before reserving a durable
    // intent. Unexpected faults after reservation remain UNKNOWN.
    if(['prepare','prepareStatus','activate','closeLease'].includes(b.action)){
      ensure(b.payload.grantId===g.id,'GRANT_BINDING');
      if('projectId' in b.payload)ensure(typeof b.payload.projectId==='string'&&
        /^[A-Za-z0-9_-]{1,128}$/.test(b.payload.projectId),'PROJECT_BINDING');
      if(b.action==='closeLease'){
        const lease=verified(b.payload.lease,issuerPublicKey,'r16.lease.v1');
        ensure(lease.grantId===g.id&&lease.project?.id===b.payload.projectId,'LEASE_BINDING');
        exact(b.payload.evidence,ROLES);
        for(const role of ROLES){
          const proof=verified(b.payload.evidence[role],g.peers[role].publicKey,'r16.stopped.v1');
          ensure(proof.role===role&&proof.peerId===g.peers[role].id,'ROLE_BINDING');
        }
      }
    }
    // Human revocation remains possible even when a different action is
    // uncertain. A second uncertain revocation itself is never reissued.
    return fencedEffect(replayStore,b.role,b.nonce,t,b.action,envelope,()=>{
    if(b.action==='nonceStatus'){
      exact(b.payload,['nonce','requestHash']);
      ensure(nonceRE.test(b.payload.nonce)&&/^[a-f0-9]{64}$/.test(b.payload.requestHash),'REPLAY_ID');
      const entry=replayEntries(replayStore).find(e=>e.id===b.role+':'+b.payload.nonce);
      if(!entry)return {status:'NOT_FOUND',retryPermitted:false};
      ensure(entry.requestHash===b.payload.requestHash,'REPLAY_REQUEST_MISMATCH');
      return entry.phase==='RESULT'?{status:'RESULT',result:entry.result,resultHash:entry.resultHash,retryPermitted:false}:
        {status:'UNKNOWN',retryPermitted:false};
    }
    if(b.action==='grant')return grant;
    if(b.action==='heartbeat'){
      exact(b.payload,['report']);
      const h=innerProof(b.payload.report,'r16.participant-heartbeat.v1');
      exact(h,['schema','role','peerId','grantId','grantVersion','issuedAt',
        'expiresAt','ready','credentialValid','unresolved','projects']);
      ensure(h.peerId===g.peers[h.role].id&&h.grantId===g.id&&
        Number.isSafeInteger(h.grantVersion)&&h.grantVersion>=g.version&&
        h.grantVersion<=fresh.version&&Number.isSafeInteger(h.issuedAt)&&
        Number.isSafeInteger(h.expiresAt)&&h.issuedAt<=t&&t<h.expiresAt&&
        h.expiresAt-h.issuedAt<=30000&&typeof h.ready==='boolean'&&
        typeof h.credentialValid==='boolean'&&typeof h.unresolved==='boolean'&&
        Array.isArray(h.projects)&&h.projects.length<=4096,'HEARTBEAT_INVALID');
      const names=new Set();
      for(const p of h.projects){
        exact(p,['projectId','generation','leaseHash','phase']);
        ensure(typeof p.projectId==='string'&&
          /^[A-Za-z0-9_-]{1,128}$/.test(p.projectId)&&!names.has(p.projectId)&&
          Number.isSafeInteger(p.generation)&&p.generation>=0&&
          typeof p.leaseHash==='string'&&(p.leaseHash===''||/^[a-f0-9]{64}$/.test(p.leaseHash))&&
          ['ACTIVE','DRAINING','CLOSED'].includes(p.phase),'HEARTBEAT_INVALID');
        names.add(p.projectId);
      }
      const closeComplete=fresh.projects.every(p=>p.active===null&&p.pending===null);
      return {connectRequested:mode==='active'&&fresh.status==='ACTIVE',
        grantVersion:fresh.version,revoked:fresh.status==='REVOKED',
        revocationComplete:fresh.status==='REVOKED'&&fresh.revocationAcks.length===3,
        closeComplete:mode!=='active'&&closeComplete};
    }
    // A dead process does not create permission. All issuer functions operate
    // on durable, signature-verified R16 state.
    ensure(typeof issuer[b.action]==='function','ISSUER_ACTION');
    return issuer[b.action](b.payload);
    },fault);
  }
  function revokeByHuman({approval}){
    ensure(approval&&typeof approval==='object','HUMAN_PROOF_REQUIRED');
    const intent=verified(approval,humanAuthorityPublicKey,'mht.human-authorization.v1');
    const status=intent.action==='revoke_status';
    exact(intent,['schema','action','grantId','expectedVersion','expectedGrantHash','releaseId','issuedAt','nonce',
      ...(status?['targetNonce','requestHash']:[])]);
    const t=now();
    ensure((intent.action==='revoke_grant'||status)&&intent.grantId===g.id&&
      intent.expectedGrantHash===digest(grant)&&intent.releaseId===trustedRelease.id&&
      Number.isSafeInteger(intent.expectedVersion)&&
      (status?issuerStore.snapshot().grants[0].version>=intent.expectedVersion:
      issuerStore.snapshot().grants[0].version===intent.expectedVersion),'OWNER_TARGET_CHANGED');
    ensure(Number.isSafeInteger(intent.issuedAt)&&intent.issuedAt<=t&&t-intent.issuedAt<=30000,
      'HUMAN_PROOF_EXPIRED');
    if(status)return fencedEffect(replayStore,'human',intent.nonce,t,'revoke_status',approval,()=>{
      ensure(nonceRE.test(intent.targetNonce)&&/^[a-f0-9]{64}$/.test(intent.requestHash),'REPLAY_ID');
      const entry=replayEntries(replayStore).find(e=>e.id==='human:'+intent.targetNonce);
      if(!entry)return {status:'NOT_FOUND',retryPermitted:false};
      ensure(entry.requestHash===intent.requestHash&&entry.kind==='revoke_grant','REPLAY_REQUEST_MISMATCH');
      return entry.phase==='RESULT'?{status:'RESULT',result:entry.result,resultHash:entry.resultHash,retryPermitted:false}:
        {status:'UNKNOWN',retryPermitted:false};
    },fault);
    return fencedEffect(replayStore,'human',intent.nonce,t,'revoke_grant',approval,
      ()=>issuer.revoke({approval:secretApproval,grantId:g.id}),fault);
  }
  return Object.freeze({issue,revokeByHuman,
    inspect:()=>({grantId:g.id,releaseId:trustedRelease.id,mode,
      signingIssuerPublicKey:issuerPublicKey,
      grantStatus:issuerStore.snapshot().grants[0].status,
      grantVersion:issuerStore.snapshot().grants[0].version,
      lastReplayCount:replayStore.snapshot().used.length})});
}

// A single invocation may open and close both journals; the service
// supervisor, not arbitrary role input, supplies all sensitive parameters.
export function runMinimalTrustOnce({
  issuerDirectory,replayDirectory,issuerPrivateKey,releasePublicKey,
  issuerPublicKey,grantId,release,resolveProject,humanAuthorityPublicKey,
  expectedGrantHash=null,mode='active',now=Date.now,fault=()=>{},
  envelope=null,ownerApproval=null,handoffBinding=null,
  enrollmentAuthorityPublicKey=null,
}){
  ensure(typeof issuerDirectory==='string'&&typeof replayDirectory==='string'&&
    issuerDirectory!==replayDirectory,'TRUST_DIRECTORIES');
  const issuerStore=new ProtectedStore({directory:issuerDirectory,create:false,now});
  let replayStore;
  try {
    replayStore=new ProtectedStore({directory:replayDirectory,create:false,now});
    if(handoffBinding!==null){
      const recovery=Object.hasOwn(handoffBinding,'recoveryHandoff');
      exact(handoffBinding,['handoffHash','issuerSnapshotHash','epoch','admissionExpiresAt',
        ...(recovery?['recoveryHandoff']:[])]);
      // An unsigned exception supplied by a role is never an admission. The
      // installed policy must carry the actual independently signed v2 handoff.
      const recoveryBody=recovery?verifyRecoveryHandoff(handoffBinding.recoveryHandoff,
        enrollmentAuthorityPublicKey,{grantId,release,mode,issuerPublicKey}):null;
      if(recovery)ensure(digest(handoffBinding.recoveryHandoff)===handoffBinding.handoffHash&&
        recoveryBody.issuerSnapshotHash===handoffBinding.issuerSnapshotHash&&
        recoveryBody.epoch===handoffBinding.epoch&&
        recoveryBody.expiresAt===handoffBinding.admissionExpiresAt&&
        digest(issuerStore.snapshot().grants[0]?.grant)===recoveryBody.grantHash,
        'HANDOFF_BINDING');
      const previous=replayStore.snapshot().handoff;
      if(previous!==null)ensure(equal(previous,handoffBinding),'HANDOFF_BINDING');
      else{
        const snapshot=issuerStore.snapshot();
        const t=now();
        ensure(t<handoffBinding.admissionExpiresAt&&digest(snapshot)===handoffBinding.issuerSnapshotHash&&snapshot.grants.length===1&&
          (recovery||snapshot.grants[0].projects.every(p=>p.active===null&&p.pending===null))&&
          replayEntries(replayStore).length===0,'HANDOFF_SNAPSHOT');
        if(recovery){
          ensure(recoveryBody.issuedAt<=t&&t-recoveryBody.issuedAt<=30000,'HANDOFF_SNAPSHOT');
          inspectRecoveryIssuerSnapshot({snapshot,wrapper:issuerStore.state,
            admission:recoveryBody.recoveryAdmission,grantId,issuerPublicKey,releasePublicKey,now:t});
        }
        replayStore.transact(s=>{s.handoff=handoffBinding;});
      }
    }
    const issuer=createMinimalTrustIssuer({
      issuerStore,replayStore,issuerPrivateKey,releasePublicKey,issuerPublicKey,
      grantId,release,resolveProject,humanAuthorityPublicKey,expectedGrantHash,mode,now,fault,
    });
    // Never accept both paths, even if user-input routing attempts it.
    ensure((envelope!==null)!==(ownerApproval!==null),'TRUST_ONE_OPERATION');
    return envelope!==null?issuer.issue(envelope):issuer.revokeByHuman({approval:ownerApproval});
  } finally {
    try{replayStore?.close();}finally{issuerStore.close();}
  }
}
