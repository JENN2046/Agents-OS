// Fixed source identities only. No caller-selected roots, versions or hash override.
import {canonical,digest,verified} from '../src/lease-core.mjs';
const need=(v,c='SOURCE_BASELINE_REJECTED')=>{if(!v)throw Object.assign(Error(c),{code:c});};
const same=(a,b)=>canonical(a)===canonical(b);
const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
export const HISTORICAL_R15_BASELINE=freeze({
 releaseId:'r16-daily-20261012-r15',directory:'/opt/r16/releases/r16-daily-20261012-r15',
 publicConfigDigest:'be3ff2b5125f8212206d2848bb32889c3c6b50a8ca56aa3b1a4bc4359591bbdb',
 versions:{app:'235a5b919c65ac1d73290732d2b2014c24a338cc4b6795a5064e804803ec1e7a',bridge:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',native:'76319c50acaec649967986c1f12e6923ba4f664ac3230596ed2703fce3470ae6'},
});
export const SOURCE19_BASELINE=freeze({
 revision:19,acceptedDeliveryHash:'b8645f6fe206e84dd07c2c6c166bfe4016d1deefca28bf9545dcfa1560f013e9',
 releaseId:'r16-daily-20261015-r15-app-recovery-r6',directory:'/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6',
 publicConfigDigest:'56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec',
 releaseHash:'70e76c7e563c0fda544f3e55ab2b2c98a4889912f3a5c45e39019738bc1fdffb',
 grantHash:'00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6',
 versions:{app:'34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500',bridge:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',native:'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4'},
});
export function sourceBaselineId(id){
 need(id===HISTORICAL_R15_BASELINE.releaseId||id===SOURCE19_BASELINE.releaseId,'SOURCE_RELEASE_NOT_PINNED');
 return id===SOURCE19_BASELINE.releaseId?SOURCE19_BASELINE:HISTORICAL_R15_BASELINE;
}
export function inspectSourceRelease(release){
 need(release?.schema==='r16.release.v1','SOURCE_RELEASE_NOT_PINNED');
 const spec=sourceBaselineId(release.id);
 // Historical fixture callers retain their original protocol. New source19
 // always requires the three exact reviewed runtime versions.
 if(spec===SOURCE19_BASELINE)need(same(release.versions,spec.versions),'SOURCE19_VERSIONS_NOT_PINNED');
 return spec;
}
export function inspectSourcePublicConfiguration(pub){
 const spec=inspectSourceRelease(pub?.release?.body);
 if(spec===SOURCE19_BASELINE){
  need(digest(pub)===spec.publicConfigDigest&&digest(pub.release)===spec.releaseHash&&digest(pub.grant)===spec.grantHash,'SOURCE19_PUBLIC_NOT_PINNED');
  need(same(pub.versions,spec.versions),'SOURCE19_VERSIONS_NOT_PINNED');
  const r=verified(pub.release,pub.releasePublicKey,'r16.release.v1'),g=verified(pub.grant,pub.issuerPublicKey,'r16.workspace.v1');
  need(r.id===spec.releaseId&&same(r.versions,spec.versions)&&g.id==='r16-projects-daily'&&g.version===1,'SOURCE19_SIGNED_SCOPE_DRIFT');
 }
 return spec;
}
export function inspectSourceOwnerConfiguration(pub,configuration,now=Date.now()){
 const spec=inspectSourcePublicConfiguration(pub);
 if(spec!==SOURCE19_BASELINE)return null; // Historical fixtures retain original requirements.
 need(configuration?.kind==='r16.owner.configuration.v1'&&Number.isSafeInteger(now)&&now>0,'SOURCE19_OWNER_CONFIGURATION_REQUIRED');
 const d=configuration.delivery;
 need(d?.revision===spec.revision&&digest(d.envelope)===spec.acceptedDeliveryHash,'SOURCE19_ACCEPTED_DELIVERY_NOT_PINNED');
 const b=verified(d.envelope,pub.issuerPublicKey,'r16.configuration-delivery.v1');
 need(same(Object.keys(b).sort(),['control','issuedAt','publicConfig','revision','schema'])&&b.revision===spec.revision&&
  Number.isSafeInteger(b.issuedAt)&&b.issuedAt>=pub.release.body.issuedAt&&b.issuedAt<=now&&same(b.publicConfig,pub)&&
  same(b.control,{grantId:'r16-projects-daily',grantVersion:1,status:'ACTIVE',connectRequested:true}),'SOURCE19_ACCEPTED_DELIVERY_SCOPE_DRIFT');
 need(d.hash===digest({publicConfig:pub,control:b.control,connectionNonce:configuration.connectionNonce||0}),'SOURCE19_OWNER_DELIVERY_CACHE_DRIFT');
 return Object.freeze({revision:spec.revision,deliveryHash:digest(d.envelope),publicConfigDigest:spec.publicConfigDigest});
}
