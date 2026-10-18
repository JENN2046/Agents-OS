// Read-only public projection; no Store, signer, credentials, selector or effects.
// Canonical/Ed25519 wire is the existing lease-core R16-SIGNED format.
import {createHash,createPublicKey,verify} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const need=(v,c)=>{if(!v)throw Object.assign(Error(c),{code:c});};
export function canonical(v){
 if(v===null||typeof v==='boolean'||typeof v==='string')return JSON.stringify(v);
 if(typeof v==='number'){need(Number.isSafeInteger(v),'NONCANONICAL_JSON');return String(v);}
 if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
 need(v&&Object.getPrototypeOf(v)===Object.prototype,'NONCANONICAL_JSON');
 const keys=Object.keys(v).sort();need(keys.every(k=>!['__proto__','constructor','prototype'].includes(k)),'NONCANONICAL_JSON');
 return '{'+keys.map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
}
export const digest=v=>createHash('sha256').update(canonical(v)).digest('hex');
const same=(a,b)=>canonical(a)===canonical(b),hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const GRANT='00ac437d66143e627132975555d06396d69ff69616f630d19e3622627e15c5e6';
const PUBLIC='56e1df18a54950ea346a51654e61df60afe33cb9928ae77293b2cf336fd8a5ec';
const OLD={app:'235a5b919c65ac1d73290732d2b2014c24a338cc4b6795a5064e804803ec1e7a',bridge:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',native:'76319c50acaec649967986c1f12e6923ba4f664ac3230596ed2703fce3470ae6'};
const PINS={p2vox:{id:'c434da49-055a-43dc-a3e3-695cce137909',generation:30,hash:'fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f'},pmog2:{id:'d0364f8b-3a68-4ca2-a396-7953b29cee4c',generation:38,hash:'38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'}};
function signed(e,key,schema){
 need(e&&same(Object.keys(e).sort(),['body','signature'])&&e.body?.schema===schema&&typeof e.signature==='string'&&/^[A-Za-z0-9_-]{86}$/.test(e.signature),'SIGNED_ENVELOPE_INVALID');
 const der=Buffer.from(key,'base64url');need(der.toString('base64url')===key,'BAD_SIGNATURE');
 const k=createPublicKey({key:der,format:'der',type:'spki'});need(k.asymmetricKeyType==='ed25519'&&verify(null,Buffer.from('R16-SIGNED\0'+canonical(e.body)),k,Buffer.from(e.signature,'base64url')),'BAD_SIGNATURE');return e.body;
}
function source(pub,now){
 need(digest(pub)===PUBLIC&&digest(pub.grant)===GRANT,'SOURCE19_PUBLIC_DRIFT');
 const g=signed(pub.grant,pub.issuerPublicKey,'r16.workspace.v1'),r=signed(pub.release,pub.releasePublicKey,'r16.release.v1');
 need(g.id==='r16-projects-daily'&&g.version===1&&g.channel==='main'&&same(r.versions,pub.versions)&&same(g.peers,pub.peers)&&Number.isSafeInteger(now)&&r.issuedAt<=now&&now<r.notAfter,'SOURCE19_RELEASE_INVALID');return g;
}
function wrapper(v,kind){need(v&&same(Object.keys(v).sort(),['schema','revision','maxNow','data'].sort())&&v.schema===1&&Number.isSafeInteger(v.revision)&&v.revision>=0&&Number.isSafeInteger(v.maxNow)&&v.maxNow>=0&&v.data?.kind===kind,'STORE_WRAPPER_INVALID');return v.data;}
function checkedOperations(operations,pub,g){
 need(Array.isArray(operations)&&operations.length===2,'ORIGINAL_SIGNED_OPERATIONS_REQUIRED');
 return Object.entries(PINS).map(([projectId,p])=>{
  const found=operations.filter(e=>e?.body?.id===p.id);need(found.length===1&&digest(found[0])===p.hash,'ORIGINAL_OPERATION_HASH');
  const o=signed(found[0],g.peers.app.publicKey,'r16.operation.v1');
  need(same(Object.keys(o).sort(),['schema','id','grantId','projectId','generation','leaseHash','channel','action','payloadHash'].sort())&&o.grantId===g.id&&o.projectId===projectId&&o.generation===p.generation&&o.channel===g.channel&&o.action==='find_symbol'&&hash(o.leaseHash)&&hash(o.payloadHash),'ORIGINAL_OPERATION_SCOPE');return found[0];
 });
}
// Input is already held in trusted root memory, never an arbitrary filesystem path.
export function collectHistoricalOperations({appHostState,publicConfig:pub,planHash,now=Date.now()}){
 need(hash(planHash),'PLAN_HASH');const g=source(pub,now),s=wrapper(appHostState,'r16.app-workspace.v1');
 // The Source19 App persists grant-free appHostInitialState(); startup config,
 // the fixed public pins and the signed original operations bind its grant.
 need(['projects','allocations','operations'].every(k=>Array.isArray(s[k])),'APP_HOST_STATE_SHAPE');
 if(Object.hasOwn(s,'grant'))need(same(s.grant,pub.grant),'APP_GRANT_DRIFT');
 collections(s);
 for(const row of s.operations)if(row.status==='UNKNOWN')need(PINS[row.projectId]?.id===row.id,'NEW_UNKNOWN_OPERATION');
 const ops=Object.entries(PINS).map(([projectId,p])=>{const rows=s.operations.filter(r=>r.id===p.id);need(rows.length===1&&rows[0].projectId===projectId&&rows[0].status==='UNKNOWN','APP_ORIGINAL_UNKNOWN_DRIFT');return rows[0].operation;});
 return {schema:'r16.source19-native-transition.public-history.v1',planHash,sourcePublicConfigHash:PUBLIC,historicalOperations:checkedOperations(ops,pub,g)};
}
function embedded(v,pub,g,hint='native'){
 if(Array.isArray(v)){for(const x of v)embedded(x,pub,g,hint);return;}
 if(!v||typeof v!=='object')return;
 if(v.body&&typeof v.body==='object'&&(typeof v.body.schema==='string'||same(Object.keys(v).sort(),['body','signature']))){
  const b=v.body,sc=b?.schema;let key;
  if(['r16.workspace.v1','r16.lease.v1','r16.activation.v1','r16.closed.v1','r16.fresh.v1','r16.prepare-status.v1','r16.revocation-status.v1'].includes(sc))key=pub.issuerPublicKey;
  else if(sc==='r16.release.v1')key=pub.releasePublicKey;
  else if(['r16.operation.v1','r16.workspace-control.v1','r16.workspace-route.v1'].includes(sc))key=g.peers.app.publicKey;
  else if(sc==='r16.workspace-control-result.v1')key=g.peers.native.publicKey;
  else if(['r16.close.v1','r16.stopped.v1','r16.result.v1','r16.fresh-request.v1','r16.revocation-ack.v1'].includes(sc)){need(['app','bridge','native'].includes(b.role),'SIGNED_ROLE_INVALID');key=g.peers[b.role].publicKey;}
  else if(sc==='r16.prepare.v1'){need(['app','bridge','native'].includes(hint),'SIGNED_ROLE_INVALID');key=g.peers[hint].publicKey;}
  else need(false,'UNREVIEWED_SIGNED_SCHEMA');
  const body=signed(v,key,sc);if(Object.hasOwn(body,'grantId'))need(body.grantId===g.id,'SIGNED_GRANT_DRIFT');
 }
 for(const [k,x]of Object.entries(v))embedded(x,pub,g,['app','bridge','native'].includes(k)?k:hint);
}
function collections(s,{controls=false}={}){
 for(const key of ['operations','allocations','controls'])if(Object.hasOwn(s,key)){
  need(Array.isArray(s[key]),'COLLECTION_SHAPE');const seen=new Set();for(const r of s[key]){need(r&&typeof r==='object'&&typeof r.id==='string'&&!seen.has(r.id),'COLLECTION_SHAPE');seen.add(r.id);
   const allowed=key==='operations'?['KNOWN','UNKNOWN']:key==='controls'&&controls?['KNOWN','NOT_EXECUTED','UNKNOWN']:['KNOWN','NOT_EXECUTED','CLOSED'];need(allowed.includes(r.status),'CURRENT_WORK_UNRESOLVED');}
 }
}
function validateNative({files,publicConfig:pub,history,planHash,now=Date.now()},preflight){
 const g=source(pub,now);
 if(preflight)need(history?.schema==='r16.source19-native-transition.public-history-preflight.v1'&&history.authority===false&&history.atomicStoppedCheckpoint===false&&history.sourcePublicConfigHash===PUBLIC,'AUTHENTICATED_HISTORY_SCOPE');
 else need(hash(planHash)&&history?.schema==='r16.source19-native-transition.public-history.v1'&&history.planHash===planHash&&history.sourcePublicConfigHash===PUBLIC,'AUTHENTICATED_HISTORY_SCOPE');
 const operations=checkedOperations(history.historicalOperations,pub,g),state=wrapper(files['dispatcher/state.json'],'r16.native-dispatch.v1');
 need(Array.isArray(state.projects)&&new Set(state.projects).size===state.projects.length&&state.projects.every(p=>typeof p==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(p)),'PROJECT_GRAPH_INVALID');
 collections(state,{controls:true});need(Array.isArray(state.controls)&&Array.isArray(state.pending)&&state.pending.every(p=>p.status==='CREATED'),'CURRENT_WORK_UNRESOLVED');
 const controls=state.controls.filter(r=>r.status==='UNKNOWN').map(r=>{need(same(Object.keys(r).sort(),['hash','id','status'])&&hash(r.hash),'CONTROL_ROW_INVALID');return r;}).sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
 const unknown={},bindings={},retained=[];
 for(const projectId of state.projects){
  const s=wrapper(files['dispatcher/project-'+projectId+'/state.json'],'r16.participant.v1');need(s.role==='native'&&same(s.grant,pub.grant)&&Array.isArray(s.operations),'PARTICIPANT_BINDING');collections(s);embedded(s,pub,g);
  for(const row of s.operations){if(row.status==='KNOWN')continue;const p=PINS[projectId];need(p&&row.id===p.id&&row.hash===p.hash&&row.generation===p.generation&&row.projectId===projectId&&row.outcome===null&&row.resultHash===null,'NEW_UNKNOWN_OPERATION');
   const op=operations.find(o=>o.body.id===p.id).body,lease=s.active?.lease;need(lease&&!s.pending&&(!s.closing||same(s.closing,lease))&&digest(lease)===op.leaseHash,'ORIGINAL_LEASE_BINDING');
   const l=signed(lease,pub.issuerPublicKey,'r16.lease.v1');need(l.phase==='PREPARED'&&l.grantId===g.id&&l.grantHash===GRANT&&l.grantVersion===g.version&&l.project.id===projectId&&l.project.workspaceId===g.workspace.id&&l.generation===p.generation&&l.previousGeneration===l.generation-1&&l.channel===g.channel&&same(l.versions,OLD)&&Array.isArray(l.actions)&&l.actions.includes('find_symbol')&&l.actions.every(a=>g.actions.includes(a))&&Number.isSafeInteger(l.issuedAt)&&l.expiresAt===l.issuedAt+3600000&&l.renewAt===l.expiresAt-900000,'ORIGINAL_LEASE_BINDING');
   unknown[projectId]=p;retained.push(projectId);
  }
  bindings[projectId]={active:s.active?.lease?digest(s.active.lease):null,closing:s.closing?digest(s.closing):null,rows:s.operations};
  for(const [name,value]of Object.entries(files))if(name.startsWith('dispatcher/project-'+projectId+'/archive-operation-'))need(value&&name==='dispatcher/project-'+projectId+'/archive-operation-'+digest(value.id)+'.json'&&value.projectId===projectId&&value.status==='KNOWN'&&hash(value.hash)&&hash(value.resultHash)&&['COMPLETED','REJECTED','NOT_EXECUTED'].includes(value.outcome),'ARCHIVE_OPERATION_INVALID');
  const visited=new Set();let head=s.archiveHead;while(head){need(head&&hash(head.hash)&&typeof head.name==='string'&&!visited.has(head.name),'ARCHIVE_CHAIN_INVALID');visited.add(head.name);const a=files['dispatcher/project-'+projectId+'/archive-'+head.name+'.json'];need(a?.schema==='r16.generation-archive.v1'&&digest(a)===head.hash&&head.name==='generation-'+a.generation+'-'+head.hash&&Array.isArray(a.records),'ARCHIVE_CHAIN_INVALID');for(const r of a.records){const item=files['dispatcher/project-'+projectId+'/archive-operation-'+digest(r.id)+'.json'];need(item&&digest(item)===r.hash&&item.id===r.id&&item.status==='KNOWN','ARCHIVE_OPERATION_INVALID');}head=a.previous;}
 }
 need(retained.length===2&&Object.keys(PINS).every(p=>retained.filter(x=>x===p).length===1),'ORIGINAL_UNKNOWN_MISSING');
 for(const [name,value]of Object.entries(files))if(name.endsWith('.json')){
  if(name.startsWith('dispatcher/results/control-')){const b=signed(value,g.peers.native.publicKey,'r16.workspace-control-result.v1');need(same(Object.keys(b).sort(),['schema','id','operation','ok','result'].sort())&&typeof b.id==='string'&&typeof b.operation==='string'&&/^[A-Za-z0-9_-]{1,128}$/.test(b.operation)&&b.ok===true,'CONTROL_RESULT_SHAPE');need(name==='dispatcher/results/control-'+b.id+'.json','CONTROL_RESULT_NAME_DRIFT');}
  if(name.startsWith('dispatcher/results/operation-')){need(value&&same(Object.keys(value).sort(),['nativeResult','operation','outcome'])&&['COMPLETED','REJECTED','NOT_EXECUTED'].includes(value.outcome),'OPERATION_RESULT_SHAPE');const b=signed(value.operation,g.peers.app.publicKey,'r16.operation.v1');need(same(Object.keys(b).sort(),['schema','id','grantId','projectId','generation','leaseHash','channel','action','payloadHash'].sort())&&typeof b.id==='string'&&typeof b.projectId==='string'&&Number.isSafeInteger(b.generation)&&b.generation>0&&hash(b.leaseHash)&&hash(b.payloadHash)&&name==='dispatcher/results/operation-'+b.id+'.json'&&b.grantId===g.id&&b.channel===g.channel&&g.actions.includes(b.action),'OPERATION_RESULT_BINDING');}
  embedded(value,pub,g);
 }
 return {originalUnknown:unknown,originalSignaturesAndLeasesVerified:true,originalLeaseBindingsHash:digest(bindings),controlUnknownRows:controls,controlUnknownHash:digest(controls),controlUnknownCount:controls.length,newUnknown:[],inflight:[],historicalOperations:operations};
}
export const validateNativePublic=input=>validateNative(input,false);
export const validateNativePreflight=input=>validateNative(input,true);
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 try{const chunks=[];let bytes=0;for await(const b of process.stdin){bytes+=b.length;need(bytes<=64*1024*1024,'INPUT_CAPACITY');chunks.push(b);}const input=JSON.parse(Buffer.concat(chunks).toString('utf8'));const result=input.operation==='collect-app'?collectHistoricalOperations(input):input.operation==='validate-native-preflight'?validateNativePreflight(input):validateNativePublic(input);process.stdout.write(JSON.stringify(result));}
 catch(e){process.stderr.write(JSON.stringify({code:/^[A-Z][A-Z0-9_]{1,63}$/.test(e.code??'')?e.code:'PUBLIC_CHECKPOINT_REFUSED'})+'\n');process.exitCode=78;}
}
