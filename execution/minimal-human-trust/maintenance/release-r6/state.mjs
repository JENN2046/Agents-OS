import {json,protectedBytes,digest,same,need} from './io.mjs';
import {verified} from './legacy/lease-core.mjs';
import {originalUnknownPins,FIXED} from './maintenance-release-base.mjs';

export const NATIVE='/var/lib/r16-native/grants/r16-projects-daily/dispatcher';
export const PATHS=Object.freeze({proposal:'/etc/r16-owner/release-proposal.json',reviewed:'/etc/r16-owner/reviewed-installation.json',native:'/etc/r16/native-host.json',localCutover:'/etc/r16/cutover.json',configuration:'/var/lib/r16-owner/configuration',issuer:'/var/lib/r16-owner/issuer/state.json',public:'/run/r16-owner/public-config.json'});
export function wrapper(value){need(value?.schema===1&&Number.isSafeInteger(value.revision)&&Number.isSafeInteger(value.maxNow)&&value.data&&typeof value.data==='object','STATE_WRAPPER_INVALID');return value.data;}
export function trustScope(p){const g=p.grant.body,r=p.release.body;return {workspace:g.workspace.root,workspaceId:g.workspace.id,channel:p.channel,peers:p.peers,issuerPublicKey:p.issuerPublicKey,permissionVersion:r.permissionVersion,actions:r.actions};}
export function validateOriginals({publicConfig:p,issuer,configuration,projects}){
  need(issuer.kind==='r16.issuer.v1'&&configuration.kind==='r16.owner.configuration.v1','OWNER_STATE_KIND_INVALID');
  const grants=issuer.grants.filter(g=>digest(g.grant)===digest(p.grant));need(grants.length===1,'ORIGINAL_GRANT_MISSING');
  const g=grants[0];need(g.status==='ACTIVE'&&g.version===1&&configuration.connected===true&&configuration.activeGrantId===p.grant.body.id&&configuration.replacement===null,'ORIGINAL_GRANT_NOT_ACTIVE');
  need(configuration.trust?.releasePublicKey===p.releasePublicKey&&configuration.trust.scopeHash===digest(trustScope(p)),'ORIGINAL_TRUST_SCOPE_DRIFT');
  const result={};
  for(const pin of originalUnknownPins()){
    const s=projects[pin.projectId],ops=s?.operations?.filter(o=>o.id===pin.operationId);
    need(ops?.length===1,'ORIGINAL_OPERATION_MISSING');const o=ops[0];
    need(o.hash===pin.operationHash&&o.generation===pin.generation&&o.projectId===pin.projectId&&o.status==='UNKNOWN'&&o.resultHash===null,'ORIGINAL_UNKNOWN_CHANGED');
    const lease=s.active?.lease,b=verified(lease,p.issuerPublicKey,'r16.lease.v1');
    need(same(lease,s.closing)&&!s.pending&&digest(s.grant)===digest(p.grant),'ORIGINAL_LEASE_PHASE_CHANGED');
    need(b.grantHash===digest(p.grant)&&b.releaseHash===digest(p.release)&&b.generation===pin.generation&&b.project.id===pin.projectId&&b.grantId===p.grant.body.id&&same(b.versions,p.versions),'ORIGINAL_LEASE_BINDING_CHANGED');
    const entries=g.projects.filter(x=>x.projectId===pin.projectId);need(entries.length===1,'ISSUER_PROJECT_MISSING');
    const leases=[entries[0].active,entries[0].pending,...(entries[0].history||[])].filter(Boolean).map(x=>x.lease).filter(Boolean);
    need(leases.some(x=>digest(x)===digest(lease)),'ISSUER_ORIGINAL_LEASE_CHANGED');
    result[pin.projectId]={operation:o,leaseHash:digest(lease),participantGrantHash:digest(s.grant)};
  }
  return result;
}
export function captureLocal(sourcePublicConfig,read=protectedBytes){
  const parse=(p,uid=process.geteuid())=>JSON.parse(read(p,{uid}));
  const issuer=wrapper(parse(PATHS.issuer)),configuration=wrapper(parse(PATHS.configuration+'/state.json'));
  const projects=Object.fromEntries(originalUnknownPins().map(p=>[p.projectId,wrapper(parse(NATIVE+'/project-'+p.projectId+'/state.json',1000))]));
  const originalUnknown=validateOriginals({publicConfig:sourcePublicConfig,issuer,configuration,projects});
  return {issuer,configuration,projects,originalUnknown,issuerDataHash:digest(issuer),configurationInvariantHash:digest(withoutDelivery(configuration)),projectBusinessHashes:Object.fromEntries(Object.entries(projects).map(([k,v])=>[k,digest(v.operations)]))};
}
export function withoutDelivery(config){const copy=structuredClone(config);delete copy.delivery;return copy;}
export function assertPreserved(before,after){
  need(before.issuerDataHash===after.issuerDataHash,'ISSUER_BUSINESS_STATE_CHANGED');
  need(before.configurationInvariantHash===after.configurationInvariantHash,'OWNER_AUTHORITY_STATE_CHANGED');
  need(same(before.originalUnknown,after.originalUnknown),'ORIGINAL_UNKNOWN_CHANGED');
  // Participant startup may turn historical INFLIGHT controls into UNKNOWN.
  // Original business operations, hashes, outcomes and results stay exact.
  need(same(before.projectBusinessHashes,after.projectBusinessHashes),'PROJECT_BUSINESS_OPERATIONS_CHANGED');
}
export function verifySourceDelivery(p,config){
  const d=config.delivery,b=verified(d?.envelope,p.issuerPublicKey,'r16.configuration-delivery.v1');
  need(d.revision===16&&b.revision===16&&digest(d.envelope)==='5ee11707da0d3a524550db92f8c0a5a80b7a8dac8c97f5a907b47fc956c6ec44','SOURCE_DELIVERY_DRIFT');
  need(same(b.publicConfig,p)&&same(b.control,{grantId:p.grant.body.id,grantVersion:1,status:'ACTIVE',connectRequested:true}),'SOURCE_DELIVERY_SCOPE_CHANGED');
  need(d.hash===digest({publicConfig:p,control:b.control,connectionNonce:config.connectionNonce||0}),'OWNER_DELIVERY_HASH_CHANGED');return d.envelope;
}
