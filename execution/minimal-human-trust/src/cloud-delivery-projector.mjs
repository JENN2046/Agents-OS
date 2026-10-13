// Owner-less, on-demand signed public configuration publication.
// Source candidate only. Real cloud receiver and root state never touched here.
import {ProtectedStore,verified,verifyRelease,exportPublicKey,
  digest,signed,canonical,ROLES,ACTIONS} from './lease-core.mjs';

const deny=c=>{throw Object.assign(new Error(c),{code:c});};
const assert=(x,c='CLOUD_DELIVERY_REJECTED')=>{if(!x)deny(c);};
const equal=(a,b)=>canonical(a)===canonical(b);
const initial=prior=>({kind:'mht.cloud-delivery.v1',last:prior,lastBinding:null});
export const cloudDeliveryInitialState=initial;

// Stop/revocation only: validate the exact already-trusted historical release
// at its signed issuance time, while refusing future-dated or replaced history.
// This does not grant runtime/business activation authority.
export function verifyHistoricalRecoveryRelease(release,key,{versions,actions,now,priorRelease}){
  assert(priorRelease&&equal(release,priorRelease),'RECOVERY_RELEASE_NOT_PINNED');
  const body=verified(release,key,'r16.release.v1');
  assert(Number.isSafeInteger(now)&&Number.isSafeInteger(body.issuedAt)&&body.issuedAt<=now,
    'RECOVERY_RELEASE_FUTURE');
  return verifyRelease(release,key,{versions,actions,now:body.issuedAt});
}

// Seed only with an *existing* signed Owner delivery from a trusted state
// migration. The constructor refuses to start at revision 1 on an old grant.
export function createCloudDeliveryProjector({
  deliveryStore,issuerStore,issuerSigningKey,issuerPublicKey,
  releasePublicKey,release,mode='recovery_only',now=Date.now,
}){
  assert(deliveryStore instanceof ProtectedStore&&
    deliveryStore.snapshot().kind==='mht.cloud-delivery.v1'&&
    issuerStore instanceof ProtectedStore&&issuerStore.snapshot().kind==='r16.issuer.v1',
    'CLOUD_LEDGER_IDENTITY');
  assert(mode==='recovery_only','RECOVERY_ONLY');
  assert(exportPublicKey(issuerSigningKey)===issuerPublicKey,'ISSUER_KEY_MISMATCH');
  const signedRelease=verified(release,releasePublicKey,'r16.release.v1');
  const ledger=issuerStore.snapshot().grants;
  assert(ledger.length===1,'GRANT_COUNT');
  const gentry=ledger[0];
  const grant=gentry.grant,g=verified(grant,issuerPublicKey,'r16.workspace.v1');
  assert(Number.isSafeInteger(gentry.version)&&gentry.version>=g.version&&['ACTIVE','REVOKED'].includes(gentry.status)&&
    equal(g.actions,ACTIONS),'GRANT_BINDING');
  const old=deliveryStore.snapshot().last;
  assert(old&&old.body,'CLOUD_PRIOR_REQUIRED');
  const oldBody=verified(old,issuerPublicKey,'r16.configuration-delivery.v1');
  assert(Number.isSafeInteger(oldBody.revision)&&oldBody.revision>=1&&
    oldBody.control?.grantId===g.id&&
    oldBody.publicConfig?.issuerPublicKey===issuerPublicKey&&
    oldBody.publicConfig?.releasePublicKey===releasePublicKey&&
    equal(oldBody.publicConfig.grant,grant)&&
    Number.isSafeInteger(oldBody.control.grantVersion)&&oldBody.control.grantVersion<=gentry.version&&
    ['ACTIVE','REVOKED'].includes(oldBody.control.status)&&
    !(oldBody.control.status==='REVOKED'&&gentry.status!=='REVOKED'),'CLOUD_PRIOR_UNTRUSTED');
  verifyHistoricalRecoveryRelease(release,releasePublicKey,{versions:signedRelease.versions,
    actions:g.actions,now:now(),priorRelease:oldBody.publicConfig.release});
  const publicConfig={schema:'r16.runtime-configuration.v1',
    issuerPublicKey,releasePublicKey,release,grant,peers:g.peers,
    versions:signedRelease.versions,channel:g.channel};
  const control={grantId:g.id,grantVersion:gentry.version,
    status:gentry.status,connectRequested:false};
  return Object.freeze({
    publish(){
      // Recovery publication does not assert Owner is READY or allow new
      // business calls. It is a signed delivery, NOT an execution permit.
      const current=issuerStore.snapshot().grants[0];
      assert(equal(current.grant,grant)&&current.version===gentry.version&&
        current.status===gentry.status,'GRANT_DRIFT');
      verifyHistoricalRecoveryRelease(release,releasePublicKey,{versions:signedRelease.versions,
        actions:g.actions,now:now(),priorRelease:oldBody.publicConfig.release});
      return deliveryStore.transact((state,time)=>{
        const prior=verified(state.last,issuerPublicKey,'r16.configuration-delivery.v1');
        assert(Number.isSafeInteger(prior.revision)&&prior.revision>=oldBody.revision&&
          prior.control.grantId===g.id&&prior.control.grantVersion<=current.version&&
          prior.publicConfig?.issuerPublicKey===issuerPublicKey&&
          prior.publicConfig?.releasePublicKey===releasePublicKey&&
          equal(prior.publicConfig?.grant,grant)&&equal(prior.publicConfig?.release,release)&&
          !(prior.control.status==='REVOKED'&&current.status!=='REVOKED'),
          'CLOUD_DELIVERY_ROLLBACK');
        const nextDigest=digest({publicConfig,control});
        // Idempotently return the identical signed proof after a lost ACK.
        if(state.lastBinding===nextDigest){
          assert(equal(prior.publicConfig,publicConfig)&&equal(prior.control,control),
            'CLOUD_BINDING_CORRUPT');
          return state.last;
        }
        assert(prior.revision<Number.MAX_SAFE_INTEGER,'CLOUD_REVISION_OVERFLOW');
        const response=signed({schema:'r16.configuration-delivery.v1',
          revision:prior.revision+1,issuedAt:time,publicConfig,control},
          issuerSigningKey);
        state.last=response;state.lastBinding=nextDigest;
        return response;
      });
    },
    snapshot(){const s=deliveryStore.snapshot();return Object.freeze({
      grantId:g.id,mode,revision:s.last.body.revision,
      lastPublishedRecovery:s.lastBinding!==null,mayStartBusiness:false});
    },
  });
}
