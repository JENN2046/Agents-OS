import {replyWindow} from './control-clock.mjs';
import fs from 'node:fs';
import path from 'node:path';
import {createHash, createPublicKey, sign as cryptoSign, verify as cryptoVerify, randomUUID} from 'node:crypto';

export const ROLES = Object.freeze(['app', 'bridge', 'native']);
export const ACTIONS = Object.freeze(['bind_project','session_status','session_close','list_workspaces','list_projects','get_project','read_code','outline','find_symbol','search_history','get_node_diff','create_project','update_todos','edit_code','create_file','submit_report','rollback']);
export const LEASE_MS = 3600000, RENEW_BEFORE_MS = 900000;
const ID = /^[A-Za-z0-9_-]{1,128}$/, HASH = /^[a-f0-9]{64}$/;
export function fail(code) { const e = new Error(code); e.code = code; throw e; }
const check = (x, code='INVALID_INPUT') => { if (!x) fail(code); };
const plain = x => x !== null && typeof x === 'object' && !Array.isArray(x) && Object.getPrototypeOf(x) === Object.prototype;
export function canonical(x) {
  if (x === null || typeof x === 'boolean' || typeof x === 'string') return JSON.stringify(x);
  if (typeof x === 'number') { check(Number.isSafeInteger(x)); return String(x); }
  if (Array.isArray(x)) return '[' + x.map(canonical).join(',') + ']';
  check(plain(x));
  check(Object.keys(x).every(k => !['__proto__','prototype','constructor'].includes(k)));
  return '{' + Object.keys(x).sort().map(k => JSON.stringify(k) + ':' + canonical(x[k])).join(',') + '}';
}
const copy = x => JSON.parse(canonical(x));
export const digest = x => createHash('sha256').update(canonical(x)).digest('hex');
const same = (a,b) => canonical(a) === canonical(b);
function keys(x, names) { check(plain(x) && same(Object.keys(x).sort(), names.slice().sort())); }
function integer(x, min=0) { check(Number.isSafeInteger(x) && x >= min); }
function id(x) { check(typeof x === 'string' && ID.test(x)); }
function hash(x) { check(typeof x === 'string' && HASH.test(x)); }
function absolute(x) { check(typeof x==='string' && x.length<=4096 && path.isAbsolute(x) && path.resolve(x)===x && !x.includes('\0')); }
export function publicKey(key) {
  const k = typeof key === 'string' ? createPublicKey({key:Buffer.from(key,'base64url'),format:'der',type:'spki'}) : key;
  check(k?.asymmetricKeyType === 'ed25519'); return k;
}
export function exportPublicKey(key) { return createPublicKey(key).export({format:'der',type:'spki'}).toString('base64url'); }
export function signed(body, key) {
  check(plain(body) && typeof body.schema === 'string');
  check(key?.type === 'private' && key.asymmetricKeyType === 'ed25519');
  return {body:copy(body), signature:cryptoSign(null,Buffer.from('R16-SIGNED\0'+canonical(body)),key).toString('base64url')};
}
export function verified(envelope, key, schema) {
  keys(envelope,['body','signature']);
  check(envelope.body?.schema===schema && typeof envelope.signature==='string' && /^[A-Za-z0-9_-]{86}$/.test(envelope.signature),'BAD_SIGNATURE');
  try { check(cryptoVerify(null,Buffer.from('R16-SIGNED\0'+canonical(envelope.body)),publicKey(key),Buffer.from(envelope.signature,'base64url')),'BAD_SIGNATURE'); }
  catch { fail('BAD_SIGNATURE'); }
  return copy(envelope.body);
}
function validateWorkspace(w) { keys(w,['id','root','dev','ino']); id(w.id); absolute(w.root); integer(w.dev); integer(w.ino,1); }
function validateProject(p) { keys(p,['id','workspaceId','root']); id(p.id); id(p.workspaceId); absolute(p.root); }
function validateActions(a) { check(Array.isArray(a)&&a.length>0&&new Set(a).size===a.length&&a.every(x=>ACTIONS.includes(x))); }
function validatePeers(peers) { keys(peers,ROLES); for(const role of ROLES) { keys(peers[role],['id','publicKey']); id(peers[role].id); publicKey(peers[role].publicKey); } check(new Set(ROLES.map(r=>peers[r].id)).size===3); }
function validateGrant(g) {
  keys(g,['schema','id','version','createdAt','workspace','actions','channel','peers']);
  check(g.schema==='r16.workspace.v1'); id(g.id); integer(g.version,1); integer(g.createdAt); validateWorkspace(g.workspace); validateActions(g.actions); id(g.channel); validatePeers(g.peers);
}
function validateVersions(v) { keys(v,ROLES); for(const role of ROLES) hash(v[role]); }
export function verifyRelease(envelope, key, {versions,actions,now}) {
  const r=verified(envelope,key,'r16.release.v1');
  keys(r,['schema','id','issuedAt','notAfter','formats','versions','actions','permissionVersion']);
  id(r.id); integer(r.issuedAt); integer(r.notAfter); integer(r.permissionVersion,1); validateVersions(r.versions); validateActions(r.actions);
  check(r.issuedAt<=now && now<r.notAfter,'RELEASE_EXPIRED');
  check(Array.isArray(r.formats) && r.formats.includes('r16.workspace.v1') && r.formats.every(x=>typeof x==='string'),'RELEASE_FORMAT');
  check(same(r.versions,versions) && actions.every(a=>r.actions.includes(a)),'RELEASE_NOT_APPROVED');
  return r;
}

// Local issuer/Native must use the authoritative registry; a caller-supplied root is never a registry.
export function resolveRegisteredProject(workspace, project, registryLookup) {
  validateWorkspace(workspace); validateProject(project); check(typeof registryLookup==='function');
  const record=registryLookup(project.id);
  check(record && record.workspaceId===workspace.id && record.root===project.root && project.workspaceId===workspace.id,'PROJECT_BINDING');
  check(project.root.startsWith(workspace.root+path.sep),'PATH_OUTSIDE_WORKSPACE');
  let cursor=path.parse(workspace.root).root;
  for(const component of project.root.slice(cursor.length).split(path.sep)) {
    cursor=path.join(cursor,component); const st=fs.lstatSync(cursor);
    check(st.isDirectory()&&!st.isSymbolicLink(),'PATH_SYMLINK');
    if(cursor===workspace.root) check(st.dev===workspace.dev&&st.ino===workspace.ino,'WORKSPACE_REPLACED');
  }
  check(fs.realpathSync(project.root)===project.root,'PATH_SYMLINK'); return copy(project);
}
export function resolveProjectFile(workspace, project, relative, registryLookup, {allowMissing=false}={}) {
  resolveRegisteredProject(workspace,project,registryLookup);
  check(typeof relative==='string'&&relative.length>0&&!path.isAbsolute(relative)&&!relative.includes('\0')&&!relative.includes('\\'),'PATH_INVALID');
  const parts=relative.split('/'); check(parts.every(x=>x&&x!=='.'&&x!=='..'),'PATH_INVALID');
  let cursor=project.root;
  for(let i=0;i<parts.length;i++) { cursor=path.join(cursor,parts[i]);
    let st; try { st=fs.lstatSync(cursor); } catch(e) { if(e.code==='ENOENT'&&allowMissing&&i===parts.length-1) return cursor; throw e; }
    check(!st.isSymbolicLink()&&(i===parts.length-1||st.isDirectory()),'PATH_SYMLINK');
    if(i===parts.length-1) check(st.isFile()&&st.nlink===1,'PATH_INVALID');
  }
  return cursor;
}
const fsyncDir = dir => { const fd=fs.openSync(dir,fs.constants.O_RDONLY|fs.constants.O_DIRECTORY|fs.constants.O_NOFOLLOW); try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);} };
function processStart(pid) { try { const s=fs.readFileSync('/proc/'+pid+'/stat','utf8'); return s.slice(s.lastIndexOf(')')+2).split(' ')[19]; } catch(e) {if(e.code==='ENOENT')return null; fail('STATE_BUSY');} }

// Single lifetime writer. Dead process locks can be recovered; ambiguous/corrupt locks fail closed.
export class ProtectedStore {
  // The comparison baseline is private; callers never receive its mutable graph.
  #state;
  #snapshotCanonical;
  get state() {return copy(this.#state);}
  constructor({directory,create=false,initial,now=Date.now,fault=()=>{}}) {
    absolute(directory); check(typeof now==='function'&&typeof fault==='function');
    let cursor=path.parse(directory).root;
    for(const p of directory.slice(cursor.length).split(path.sep).slice(0,-1)) {cursor=path.join(cursor,p);check(!fs.lstatSync(cursor).isSymbolicLink(),'STATE_PATH');}
    if(create) fs.mkdirSync(directory,{mode:0o700});
    this.dir=directory; this.now=now; this.fault=fault; this.uid=process.geteuid(); this.poisoned=false; this.closed=false;
    this.identity=this.directoryStat(); this.lock={schema:1,pid:process.pid,start:processStart(process.pid),nonce:randomUUID()};
    const guard=path.join(directory,'.reclaim');
    let guardFd;
    try { guardFd=fs.openSync(guard,fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600); }
    catch {fail('STATE_BUSY');}
    try {
      const lockPath=path.join(directory,'.lock');
      if(fs.existsSync(lockPath)) {
        const old=this.read('.lock'); keys(old,['schema','pid','start','nonce']); integer(old.pid,1);
        check(old.schema===1&&typeof old.start==='string'&&typeof old.nonce==='string','STATE_BUSY');
        const current=processStart(old.pid); check(current===null||current!==old.start,'STATE_BUSY');
        fs.unlinkSync(lockPath);
      }
      this.writeNew('.lock',this.lock); fsyncDir(directory);
    } finally {fs.closeSync(guardFd);fs.unlinkSync(guard);fsyncDir(directory);}
    try {
      if(create) {check(initial!==undefined); this.writeNew('state.json',{schema:1,revision:0,maxNow:0,data:copy(initial)});fsyncDir(directory);}
      this.#state=this.read('state.json'); this.validateState(this.#state); this.#snapshotCanonical=canonical(this.#state);
    } catch(e) {this.close();throw e;}
  }
  directoryStat() {const s=fs.lstatSync(this.dir);check(s.isDirectory()&&!s.isSymbolicLink()&&s.uid===this.uid&&(s.mode&0o7777)===0o700,'STATE_PATH');return s;}
  readText(name) {
    const fd=fs.openSync(path.join(this.dir,name),fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);
    try {const s=fs.fstatSync(fd);check(s.isFile()&&s.nlink===1&&s.uid===this.uid&&(s.mode&0o7777)===0o600&&s.size>0&&s.size<=16*1024*1024,'STATE_CORRUPT');return fs.readFileSync(fd,'utf8');}finally{fs.closeSync(fd);}
  }
  read(name) {const raw=this.readText(name);try{return JSON.parse(raw);}catch{fail('STATE_CORRUPT');}}
  writeNew(name,obj) {const bytes=canonical(obj);check(Buffer.byteLength(bytes)<=16*1024*1024,'STATE_CAPACITY');const fd=fs.openSync(path.join(this.dir,name),fs.constants.O_WRONLY|fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_NOFOLLOW,0o600);try {fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}return bytes;}
  validateState(s) {keys(s,['schema','revision','maxNow','data']);check(s.schema===1);integer(s.revision);integer(s.maxNow);canonical(s.data);}
  guard() {check(!this.closed&&!this.poisoned,'STATE_UNAVAILABLE');const d=this.directoryStat();check(d.dev===this.identity.dev&&d.ino===this.identity.ino,'STATE_PATH');check(same(this.read('.lock'),this.lock),'STATE_BUSY');}
  // Always reread and parse the entire checked file. Noncanonical formatting uses
  // the original semantic comparison; changed data never bypasses validation.
  snapshot() {this.guard();const raw=this.readText('state.json');let s;try{s=JSON.parse(raw);}catch{fail('STATE_CORRUPT');}check(raw===this.#snapshotCanonical||canonical(s)===this.#snapshotCanonical,'STATE_CHANGED');return s.data;}
  transact(fn) {
    this.guard();this.snapshot(); const time=this.now();integer(time);check(time>=this.#state.maxNow,'CLOCK_ROLLBACK');
    const data=copy(this.#state.data); const result=fn(data,time); const next={schema:1,revision:this.#state.revision+1,maxNow:time,data};
    const temp='.next-'+randomUUID();
    try {this.fault('before_write');const committed=this.writeNew(temp,next);this.fault('before_rename');fs.renameSync(path.join(this.dir,temp),path.join(this.dir,'state.json'));fsyncDir(this.dir);this.#state=JSON.parse(committed);this.#snapshotCanonical=committed;this.fault('after_commit');}
    catch {this.poisoned=true;fail('STATE_COMMIT_UNCERTAIN');}
    return result===undefined?undefined:copy(result);
  }
  archived(name) {id(name);this.guard();try{return this.read('archive-'+name+'.json');}catch(e){if(e.code==='ENOENT')return null;throw e;}}
  archive(name,data) {id(name);this.guard();const old=this.archived(name);if(old!==null){check(same(old,data),'ARCHIVE_CONFLICT');return digest(data);}this.writeNew('archive-'+name+'.json',data);fsyncDir(this.dir);return digest(data);}
  close() {if(this.closed)return;try {if(same(this.read('.lock'),this.lock)) {fs.unlinkSync(path.join(this.dir,'.lock'));fsyncDir(this.dir);}}finally{this.closed=true;}}
}

export const issuerInitialState = () => ({kind:'r16.issuer.v1',grants:[]});
export const participantInitialState = role => {check(ROLES.includes(role));return {kind:'r16.participant.v1',role,grant:null,version:0,fresh:null,challenge:null,active:null,pending:null,closing:null,lastGeneration:0,stopped:[],closed:[],operations:[],archiveHead:null};};
function findGrant(s,idValue) {const entry=s.grants.find(x=>x.grant.body.id===idValue);check(entry,'GRANT_UNKNOWN');return entry;}
function validateRequest(r) {keys(r,['schema','requestId','grantId','grantVersion','project','channel','versions','actions','issuedAt']);check(r.schema==='r16.prepare.v1');id(r.requestId);id(r.grantId);integer(r.grantVersion,1);validateProject(r.project);id(r.channel);validateVersions(r.versions);validateActions(r.actions);integer(r.issuedAt);}
function closeBody(e) {keys(e,['schema','role','peerId','grantId','grantVersion','projectId','oldGeneration','newGeneration','leaseHash','requestId','durableClosed','pending','resultsHash']);check(e.schema==='r16.close.v1'&&ROLES.includes(e.role)&&e.durableClosed===true&&e.pending===0,'CLOSE_EVIDENCE');for(const n of ['peerId','grantId','projectId','requestId'])id(e[n]);for(const n of ['grantVersion','newGeneration'])integer(e[n],1);integer(e.oldGeneration);hash(e.leaseHash);hash(e.resultsHash);}
function validateLease(l) {keys(l,['schema','phase','grantId','grantVersion','grantHash','project','channel','versions','actions','generation','previousGeneration','issuedAt','expiresAt','renewAt','requestId','releaseHash']);check(l.schema==='r16.lease.v1'&&l.phase==='PREPARED');id(l.grantId);integer(l.grantVersion,1);hash(l.grantHash);validateProject(l.project);id(l.channel);validateVersions(l.versions);validateActions(l.actions);integer(l.generation,1);integer(l.previousGeneration);check(l.generation===l.previousGeneration+1);integer(l.issuedAt);check(l.expiresAt===l.issuedAt+LEASE_MS&&l.renewAt===l.expiresAt-RENEW_BEFORE_MS);id(l.requestId);hash(l.releaseHash);}
export function createIssuer({store,signingKey,releaseKey,authorizeOwner,resolveProject}) {
  check(store instanceof ProtectedStore&&typeof authorizeOwner==='function'&&typeof resolveProject==='function');
  check(store.snapshot().kind==='r16.issuer.v1','STATE_KIND');
  const owner = (approval,action,target) => {const result=authorizeOwner({approval,action,target:copy(target)});check(result===true,'OWNER_REQUIRED');};
  return Object.freeze({
    createGrant({approval,grant}) {
      keys(grant,['id','workspace','actions','channel','peers']);id(grant.id);validateWorkspace(grant.workspace);validateActions(grant.actions);id(grant.channel);validatePeers(grant.peers);
      owner(approval,'create_grant',grant);
      return store.transact((s,now)=> {check(!s.grants.some(x=>x.grant.body.id===grant.id),'GRANT_EXISTS');const g={schema:'r16.workspace.v1',...copy(grant),version:1,createdAt:now};const envelope=signed(g,signingKey);s.grants.push({grant:envelope,version:1,status:'ACTIVE',projects:[],revocationAcks:[]});return envelope;});
    },
    revoke({approval,grantId}) {
      id(grantId);owner(approval,'revoke_grant',{grantId});
      return store.transact((s,now)=> {const e=findGrant(s,grantId);if(e.status!=='REVOKED'){e.version++;e.status='REVOKED';e.revokedAt=now;}return signed({schema:'r16.revocation.v1',grantId,version:e.version,revokedAt:e.revokedAt,awaiting:ROLES.filter(r=>!e.revocationAcks.includes(r))},signingKey);});
    },
    prepare({grantId,request,proofs,release}) {
      id(grantId);validateRequest(request);check(request.grantId===grantId);keys(proofs,ROLES);
      return store.transact((s,now)=> {
        const e=findGrant(s,grantId),g=e.grant.body;check(e.status==='ACTIVE'&&e.version===request.grantVersion,'GRANT_REVOKED');
        for(const role of ROLES) check(same(verified(proofs[role],g.peers[role].publicKey,'r16.prepare.v1'),request),'PAIRING_FAILED');
        check(request.channel===g.channel,'CHANNEL_MISMATCH');check(request.project.workspaceId===g.workspace.id,'WORKSPACE_MISMATCH');
        check(request.actions.every(a=>g.actions.includes(a)),'ACTION_SCOPE');if(request.project.id.startsWith('pending-'))check(same(request.actions,['create_project']),'PENDING_SCOPE');check(same(resolveProject(g.workspace,request.project,{actions:request.actions}),request.project),'PROJECT_BINDING');
        verifyRelease(release,releaseKey,{versions:request.versions,actions:g.actions,now});
        let p=e.projects.find(x=>x.projectId===request.project.id);
        if(!p){p={projectId:request.project.id,generation:0,active:null,pending:null,history:[]};e.projects.push(p);}
        const prior=[...p.history,...(p.pending?[p.pending]:[])].find(x=>x.lease.body.requestId===request.requestId)||store.archived('prepare-'+digest({grantId,projectId:request.project.id,requestId:request.requestId}));
        if(prior){check(same(prior.request,request)&&same(prior.release,release),'REQUEST_CONFLICT');if(prior.lease.body.generation>p.generation){check(!p.pending||same(p.pending.lease,prior.lease),'RENEWAL_PENDING');p.pending=copy(prior);}return prior.lease;}
        check(request.issuedAt<=now&&now-request.issuedAt<=60000,'STALE_REQUEST');check(!p.pending,'RENEWAL_PENDING');
        if(p.active) {check(now>=p.active.lease.body.renewAt,'RENEWAL_TOO_EARLY');check(same(p.active.lease.body.project,request.project),'PROJECT_BINDING');}
        const l={schema:'r16.lease.v1',phase:'PREPARED',grantId,grantVersion:e.version,grantHash:digest(e.grant),project:copy(request.project),channel:g.channel,versions:copy(request.versions),actions:copy(request.actions),generation:p.generation+1,previousGeneration:p.generation,issuedAt:now,expiresAt:now+LEASE_MS,renewAt:now+LEASE_MS-RENEW_BEFORE_MS,requestId:request.requestId,releaseHash:digest(release)};
        const lease=signed(l,signingKey);p.pending={request:copy(request),lease,release:copy(release),activation:null};store.archive('prepare-'+digest({grantId,projectId:request.project.id,requestId:request.requestId}),p.pending);return lease;
      });
    },
    prepareStatus({grantId,request,proofs,release,queryId,queryIssuedAt}) {
      id(grantId);validateRequest(request);check(request.grantId===grantId);keys(proofs,ROLES);id(queryId);integer(queryIssuedAt);
      // This authenticates an already prepared intent; it never creates a lease or a project.
      // An absent intent is terminal only after its original issuance window has closed.
      return store.transact((s,now)=>{
      check(queryIssuedAt<=now&&now-queryIssuedAt<=30000,'STALE_QUERY');
      const e=findGrant(s,grantId),g=e.grant.body;
      check(request.grantVersion===g.version,'GRANT_VERSION');
      for(const role of ROLES)check(same(verified(proofs[role],g.peers[role].publicKey,'r16.prepare.v1'),request),'PAIRING_FAILED');
      check(request.channel===g.channel,'CHANNEL_MISMATCH');check(request.project.workspaceId===g.workspace.id,'WORKSPACE_MISMATCH');
      check(request.actions.every(a=>g.actions.includes(a)),'ACTION_SCOPE');if(request.project.id.startsWith('pending-'))check(same(request.actions,['create_project']),'PENDING_SCOPE');
      verifyRelease(release,releaseKey,{versions:request.versions,actions:g.actions,now:request.issuedAt});
      const p=e.projects.find(x=>x.projectId===request.project.id);
      const prior=[...(p?.history||[]),...(p?.pending?[p.pending]:[]),...(p?.active?[p.active]:[])].find(x=>x.lease.body.requestId===request.requestId)||store.archived('prepare-'+digest({grantId,projectId:request.project.id,requestId:request.requestId}));
      if(prior)check(same(prior.request,request)&&same(prior.release,release),'REQUEST_CONFLICT');
      else{check(same(resolveProject(g.workspace,request.project,{actions:request.actions}),request.project),'PROJECT_BINDING');check(request.issuedAt<=now&&now-request.issuedAt>60000,'PREPARE_WINDOW_OPEN');}
      return signed({schema:'r16.prepare-status.v1',grantId,requestHash:digest(request),queryId,issuedAt:now,expiresAt:now+30000,state:prior?'PREPARED':'NOT_ISSUED',lease:prior?prior.lease:null},signingKey);
      });
    },
    activate({grantId,projectId,evidence}) {
      id(grantId);id(projectId);keys(evidence,ROLES);
      return store.transact((s,now)=> {
        const e=findGrant(s,grantId);check(e.status==='ACTIVE','GRANT_REVOKED');const p=e.projects.find(x=>x.projectId===projectId);check(p,'PROJECT_UNKNOWN');
        const entry=p.pending||p.active;check(entry,'LEASE_UNKNOWN');const l=entry.lease.body;
        check(e.version===l.grantVersion,'GRANT_REVOKED');
        for(const role of ROLES) {const c=verified(evidence[role],e.grant.body.peers[role].publicKey,'r16.close.v1');closeBody(c);check(c.role===role&&c.peerId===e.grant.body.peers[role].id&&c.grantId===grantId&&c.grantVersion===l.grantVersion&&c.projectId===projectId&&c.oldGeneration===l.previousGeneration&&c.newGeneration===l.generation&&c.leaseHash===digest(entry.lease)&&c.requestId===l.requestId,'CLOSE_EVIDENCE');}
        check(new Set(ROLES.map(role=>evidence[role].body.resultsHash)).size===1,'RESULTS_NOT_RECONCILED');
        if(entry.activation){check(same(entry.evidence,evidence),'CLOSE_EVIDENCE_CONFLICT');return entry.activation;}
        check(now<l.expiresAt,'LEASE_EXPIRED');
        const archived=store.archived('issue-'+digest({grantId,projectId,requestId:l.requestId}));if(archived)check(same(archived.lease,entry.lease)&&same(archived.evidence,evidence),'ARCHIVE_CONFLICT');
        const activation=archived?.activation||signed({schema:'r16.activation.v1',grantId,grantVersion:l.grantVersion,projectId,generation:l.generation,leaseHash:digest(entry.lease),evidenceHash:digest(evidence),activatedAt:now},signingKey);
        entry.activation=activation;entry.evidence=copy(evidence);p.generation=l.generation;p.active=entry;store.archive('issue-'+digest({grantId,projectId,requestId:l.requestId}),entry);p.history.push(copy(entry));if(p.history.length>4)p.history.shift();p.pending=null;return activation;
      });
    },
    closeLease({grantId,projectId,lease,evidence}) {
      id(grantId);id(projectId);keys(evidence,ROLES);const l=verified(lease,exportPublicKey(signingKey),'r16.lease.v1');validateLease(l);
      return store.transact((s,now)=> {const e=findGrant(s,grantId),p=e.projects.find(x=>x.projectId===projectId);check(p,'PROJECT_UNKNOWN');
        const prior=p.history.find(x=>x.closed&&same(x.lease,lease))||store.archived('closed-'+digest(lease));if(prior){check(same(prior.stopEvidence,evidence),'CLOSE_EVIDENCE_CONFLICT');if(p.generation<=l.generation&&(!p.pending||same(p.pending.lease,lease))&&(!p.active||same(p.active.lease,lease))){p.generation=l.generation;p.active=null;p.pending=null;}return prior.closed;}
        const entry=p.pending||p.active;check(entry&&same(entry.lease,lease)&&l.grantId===grantId&&l.project.id===projectId,'LEASE_UNKNOWN');
        for(const role of ROLES){const b=verified(evidence[role],e.grant.body.peers[role].publicKey,'r16.stopped.v1');keys(b,['schema','role','peerId','grantId','grantVersion','projectId','generation','leaseHash','requestId','durableClosed','pending','resultsHash']);check(b.role===role&&b.peerId===e.grant.body.peers[role].id&&b.grantId===grantId&&b.grantVersion===l.grantVersion&&b.projectId===projectId&&b.generation===l.generation&&b.leaseHash===digest(lease)&&b.requestId===l.requestId&&b.durableClosed===true&&b.pending===0,'CLOSE_EVIDENCE');hash(b.resultsHash);}
        check(new Set(ROLES.map(role=>evidence[role].body.resultsHash)).size===1,'RESULTS_NOT_RECONCILED');
        const closed=signed({schema:'r16.closed.v1',grantId,projectId,generation:l.generation,leaseHash:digest(lease),evidenceHash:digest(evidence),closedAt:now},signingKey);
        entry.closed=closed;entry.stopEvidence=copy(evidence);store.archive('closed-'+digest(lease),entry);p.history.push(copy(entry));if(p.history.length>4)p.history.shift();p.generation=l.generation;p.active=null;p.pending=null;return closed;
      });
    },
    fresh({request}) {
      return store.transact((s,now)=> {const b=request?.body;check(b?.schema==='r16.fresh-request.v1');keys(b,['schema','grantId','role','peerId','challenge','issuedAt']);id(b.grantId);check(ROLES.includes(b.role));id(b.peerId);id(b.challenge);integer(b.issuedAt);const e=findGrant(s,b.grantId),peer=e.grant.body.peers[b.role];verified(request,peer.publicKey,b.schema);check(b.peerId===peer.id&&b.issuedAt<=now&&now-b.issuedAt<=30000,'PAIRING_FAILED');return signed({schema:'r16.fresh.v1',grantId:b.grantId,version:e.version,status:e.status,role:b.role,peerId:b.peerId,challenge:b.challenge,issuedAt:now,expiresAt:now+30000},signingKey);});
    },
    acknowledgeRevocation({proof}) {return store.transact(s=>{const b=proof?.body;keys(b,['schema','grantId','version','role','peerId','newOperationsStopped']);check(b.schema==='r16.revocation-ack.v1'&&ROLES.includes(b.role)&&b.newOperationsStopped===true);const e=findGrant(s,b.grantId);verified(proof,e.grant.body.peers[b.role].publicKey,b.schema);check(e.status==='REVOKED'&&b.version===e.version&&b.peerId===e.grant.body.peers[b.role].id,'REVOCATION_ACK');if(!e.revocationAcks.includes(b.role))e.revocationAcks.push(b.role);return {status:e.revocationAcks.length===3?'REVOKED':'WAITING_OFFLINE_ACK'};});},
    snapshot:()=>store.snapshot()
  });
}

export function createParticipant({store,role,signingKey,issuerKey,releaseKey,resolveProject}) {
  check(store instanceof ProtectedStore&&ROLES.includes(role)&&typeof resolveProject==='function');
  check(store.snapshot().kind==='r16.participant.v1'&&store.snapshot().role===role,'STATE_KIND');
  // Every process restart requires a challenge against the live issuer. Pending work remains UNKNOWN.
  store.transact(s=>{s.fresh=null;s.challenge=null;for(const o of s.operations)if(o.status==='INFLIGHT')o.status='UNKNOWN';});
  const grantBody = envelope => {const g=verified(envelope,issuerKey,'r16.workspace.v1');validateGrant(g);check(exportPublicKey(signingKey)===g.peers[role].publicKey,'PAIRING_FAILED');return g;};
  const connected = s => {check(s.fresh?.status==='ACTIVE'&&s.fresh.version===s.version,'RECONNECT_REQUIRED');};
  const current = (s,now) => {connected(s);check(s.active&&!s.pending&&!s.closing,'NOT_ACTIVE');check(!s.operations.some(o=>o.status==='UNKNOWN'),'RECOVERY_UNRESOLVED');const l=s.active.lease.body;check(l.grantVersion===s.version&&now>=l.issuedAt&&now<l.expiresAt,'LEASE_EXPIRED');return l;};
  const resultReceipt = (s,o) => signed({schema:'r16.result.v1',role,peerId:s.grant.body.peers[role].id,grantId:s.grant.body.id,projectId:o.projectId,operationId:o.id,operationHash:o.hash,generation:o.generation,outcome:o.outcome,resultHash:o.resultHash},signingKey);
  const lookupOperation=(s,operationId)=>s.operations.find(x=>x.id===operationId)||store.archived('operation-'+digest(operationId));
  const archiveOperations=s=>{
    if(!s.operations.length)return;
    check(s.operations.every(o=>o.status==='KNOWN'),'RECOVERY_UNRESOLVED');
    const records=s.operations.map(o=>{store.archive('operation-'+digest(o.id),o);return {id:o.id,hash:digest(o)};});
    const record={schema:'r16.generation-archive.v1',generation:s.lastGeneration,previous:s.archiveHead,records};
    const name='generation-'+s.lastGeneration+'-'+digest(record);store.archive(name,record);s.archiveHead={name,hash:digest(record)};s.operations=[];
  };
  return Object.freeze({
    freshRequest(grantId) {id(grantId);return store.transact((s,now)=> {check(!s.grant||s.grant.body.id===grantId,'GRANT_BINDING');const challenge=randomUUID();s.challenge={grantId,challenge,issuedAt:now};s.fresh=null;return signed({schema:'r16.fresh-request.v1',grantId,role,peerId:s.grant?.body.peers[role].id||'unpaired',challenge,issuedAt:now},signingKey);});},
    // Initial pairing installs only the signed grant; it grants no business capability.
    pair({grant}) {const g=grantBody(grant);return store.transact(s=>{check(!s.grant||same(s.grant,grant),'PAIRING_REPLACEMENT_REQUIRES_OWNER');s.grant=copy(grant);s.version=Math.max(s.version,g.version);return {paired:true};});},
    acceptFresh({response,grant}) {
      const g=grantBody(grant),b=verified(response,issuerKey,'r16.fresh.v1');keys(b,['schema','grantId','version','status','role','peerId','challenge','issuedAt','expiresAt']);integer(b.version,1);integer(b.issuedAt);integer(b.expiresAt);
      return store.transact((s,now)=>{check(same(s.grant,grant),'GRANT_BINDING');check(s.challenge&&b.challenge===s.challenge.challenge&&b.grantId===g.id&&b.role===role&&b.peerId===g.peers[role].id&&replyWindow(b,s.challenge.issuedAt,now),'STALE_CHALLENGE');check(b.version>=s.version&&['ACTIVE','REVOKED'].includes(b.status),'GRANT_VERSION');s.version=b.version;s.fresh=copy(b);s.challenge=null;if(b.status==='REVOKED'||b.version!==g.version){s.fresh.status='REVOKED';return {status:'REVOKED'};}return {status:'CONNECTED'};});
    },
    disconnect() {return store.transact(s=>{s.fresh=null;s.challenge=null;return {status:'OFFLINE'};});},
    prepare({lease,grant,release}) {
      const g=grantBody(grant),l=verified(lease,issuerKey,'r16.lease.v1');validateLease(l);
      return store.transact((s,now)=>{connected(s);check(same(s.grant,grant)&&l.grantId===g.id&&l.grantVersion===s.version&&l.grantHash===digest(grant)&&l.channel===g.channel&&l.actions.every(a=>g.actions.includes(a)),'GRANT_BINDING');check(!s.stopped.some(x=>x.body.leaseHash===digest(lease)),'LEASE_CLOSED');check(l.issuedAt<=now&&now<l.expiresAt,'LEASE_EXPIRED');check(digest(release)===l.releaseHash,'RELEASE_NOT_APPROVED');verifyRelease(release,releaseKey,{versions:l.versions,actions:l.actions,now});check(same(resolveProject(g.workspace,l.project,{actions:l.actions}),l.project),'PROJECT_BINDING');
        check(!s.closing,'CLOSE_PENDING');if(s.pending){check(same(s.pending.lease,lease),'RENEWAL_PENDING');return {status:s.pending.closed?'CLOSED':'DRAINING'};}
        if(s.active&&same(s.active.lease,lease))return {status:'ACTIVE'};
        const generation=s.lastGeneration;check(l.previousGeneration===generation,'GENERATION_MISMATCH');
        if(s.active)check(same(s.active.lease.body.project,l.project),'PROJECT_BINDING');
        s.pending={lease:copy(lease),closed:false,evidence:null};return {status:'DRAINING'};});
    },
    closeEvidence() {return store.transact(s=> {check(s.pending,'NO_PENDING_LEASE');const p=s.pending,l=p.lease.body;if(p.evidence)return p.evidence;check(s.operations.every(o=>o.status==='KNOWN'),'RECOVERY_UNRESOLVED');const e=signed({schema:'r16.close.v1',role,peerId:s.grant.body.peers[role].id,grantId:l.grantId,grantVersion:l.grantVersion,projectId:l.project.id,oldGeneration:l.previousGeneration,newGeneration:l.generation,leaseHash:digest(p.lease),requestId:l.requestId,durableClosed:true,pending:0,resultsHash:digest(s.operations.map(o=>({id:o.id,hash:o.hash,outcome:o.outcome,resultHash:o.resultHash})).sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0))},signingKey);p.closed=true;p.evidence=e;store.archive('close-'+digest(p.lease),e);s.closed.push({generation:l.previousGeneration,evidence:e});if(s.closed.length>8)s.closed.shift();return e;});},
    activate({activation}) {const a=verified(activation,issuerKey,'r16.activation.v1');keys(a,['schema','grantId','grantVersion','projectId','generation','leaseHash','evidenceHash','activatedAt']);integer(a.activatedAt);hash(a.evidenceHash);return store.transact((s,now)=>{connected(s);if(s.active&&same(s.active.activation,activation)&&!s.pending){check(now<s.active.lease.body.expiresAt,'LEASE_EXPIRED');return {status:'ACTIVE',generation:a.generation};}check(s.pending?.closed===true,'CLOSE_REQUIRED');const l=s.pending.lease.body;check(a.grantId===l.grantId&&a.grantVersion===l.grantVersion&&a.grantVersion===s.version&&a.projectId===l.project.id&&a.generation===l.generation&&a.leaseHash===digest(s.pending.lease)&&a.activatedAt>=l.issuedAt&&a.activatedAt<=now&&now<l.expiresAt,'ACTIVATION_BINDING');check(!s.closing,'CLOSE_PENDING');archiveOperations(s);s.active={lease:s.pending.lease,activation:copy(activation)};s.lastGeneration=l.generation;s.pending=null;return {status:'ACTIVE',generation:a.generation};});},
    drain({lease}) {const l=verified(lease,issuerKey,'r16.lease.v1');validateLease(l);
      const prior=store.transact(s=>{check(s.grant&&l.grantId===s.grant.body.id&&l.grantHash===digest(s.grant)&&l.channel===s.grant.body.channel,'GRANT_BINDING');
        const old=(s.stopped.find(x=>x.body.leaseHash===digest(lease))||store.archived('stop-'+digest(lease)));if(old){if(l.generation>=s.lastGeneration&&(!s.pending||same(s.pending.lease,lease))&&(!s.closing||same(s.closing,lease))){archiveOperations(s);s.lastGeneration=l.generation;s.active=null;s.pending=null;s.closing=null;}return old;}
        check(l.generation===s.lastGeneration||l.previousGeneration===s.lastGeneration,'GENERATION_MISMATCH');
        if(s.active)check(same(s.active.lease.body.project,l.project),'PROJECT_BINDING');
        if(s.pending)check(same(s.pending.lease,lease),'RENEWAL_PENDING');
        if(s.closing)check(same(s.closing,lease),'CLOSE_PENDING');s.closing=copy(lease);return null;});
      return prior?{status:'CLOSED',proof:prior}:{status:'DRAINING'};
    },
    stop({lease}) {
      const l=verified(lease,issuerKey,'r16.lease.v1');validateLease(l);
      // This commit must happen even when an unresolved operation prevents an ACK.
      const prior=store.transact(s=>{check(s.grant&&l.grantId===s.grant.body.id&&l.grantHash===digest(s.grant)&&l.channel===s.grant.body.channel,'GRANT_BINDING');
        const old=(s.stopped.find(x=>x.body.leaseHash===digest(lease))||store.archived('stop-'+digest(lease)));if(old){if(l.generation>=s.lastGeneration&&(!s.pending||same(s.pending.lease,lease))&&(!s.closing||same(s.closing,lease))){archiveOperations(s);s.lastGeneration=l.generation;s.active=null;s.pending=null;s.closing=null;}return old;}
        check(l.generation===s.lastGeneration||l.previousGeneration===s.lastGeneration,'GENERATION_MISMATCH');
        if(s.active)check(same(s.active.lease.body.project,l.project),'PROJECT_BINDING');
        if(s.pending)check(same(s.pending.lease,lease),'RENEWAL_PENDING');
        if(s.closing)check(same(s.closing,lease),'CLOSE_PENDING');s.closing=copy(lease);return null;});
      if(prior)return prior;
      return store.transact(s=>{check(s.operations.every(o=>o.status==='KNOWN'),'RECOVERY_UNRESOLVED');
        const proof=signed({schema:'r16.stopped.v1',role,peerId:s.grant.body.peers[role].id,grantId:l.grantId,grantVersion:l.grantVersion,projectId:l.project.id,generation:l.generation,leaseHash:digest(lease),requestId:l.requestId,durableClosed:true,pending:0,resultsHash:digest(s.operations.map(o=>({id:o.id,hash:o.hash,outcome:o.outcome,resultHash:o.resultHash})).sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0))},signingKey);
        store.archive('stop-'+digest(lease),proof);archiveOperations(s);s.lastGeneration=l.generation;s.active=null;s.pending=null;s.closing=null;s.stopped.push(proof);if(s.stopped.length>8)s.stopped.shift();return proof;
      });
    },
    begin({operation}) {
      return store.transact((s,now)=> {check(s.grant,'UNPAIRED');const o=verified(operation,s.grant.body.peers.app.publicKey,'r16.operation.v1');keys(o,['schema','id','grantId','projectId','generation','leaseHash','channel','action','payloadHash']);id(o.id);hash(o.payloadHash);hash(o.leaseHash);const prior=lookupOperation(s,o.id);if(prior){check(prior.hash===digest(operation),'OPERATION_CONFLICT');return prior.status==='KNOWN'?{decision:'KNOWN',outcome:prior.outcome,resultHash:prior.resultHash}:{decision:'UNKNOWN'};}
        const l=current(s,now);check(o.grantId===l.grantId&&o.projectId===l.project.id&&o.generation===l.generation&&o.leaseHash===digest(s.active.lease)&&o.channel===l.channel&&l.actions.includes(o.action),'OPERATION_SCOPE');check(same(resolveProject(s.grant.body.workspace,l.project,{actions:l.actions}),l.project),'PROJECT_BINDING');
        s.operations.push({id:o.id,hash:digest(operation),projectId:o.projectId,generation:o.generation,status:'INFLIGHT',outcome:null,resultHash:null});return {decision:'EXECUTE'};});
    },
    refuseUndispatched({operation}) {check(role==='native','NATIVE_RESULT_REQUIRED');return store.transact(s=>{
      check((s.pending||s.closing)&&s.active,'DRAIN_REQUIRED');const l=s.active.lease.body,o=verified(operation,s.grant.body.peers.app.publicKey,'r16.operation.v1');
      keys(o,['schema','id','grantId','projectId','generation','leaseHash','channel','action','payloadHash']);id(o.id);hash(o.payloadHash);
      check(o.grantId===l.grantId&&o.projectId===l.project.id&&o.generation===l.generation&&o.leaseHash===digest(s.active.lease)&&o.channel===l.channel&&l.actions.includes(o.action),'OPERATION_SCOPE');
      const prior=lookupOperation(s,o.id);if(prior){check(prior.hash===digest(operation),'OPERATION_CONFLICT');check(prior.status==='KNOWN','RECOVERY_UNRESOLVED');return resultReceipt(s,prior);}
      const entry={id:o.id,hash:digest(operation),projectId:o.projectId,generation:o.generation,status:'KNOWN',outcome:'NOT_EXECUTED',resultHash:digest({notExecuted:true,operationHash:digest(operation)})};s.operations.push(entry);return resultReceipt(s,entry);
    });},
    markUnknown(operationId) {id(operationId);return store.transact(s=>{const o=lookupOperation(s,operationId);check(o,'OPERATION_UNKNOWN');if(o.status!=='KNOWN')o.status='UNKNOWN';return {status:o.status};});},
    complete({operationId,outcome,resultHash}) {check(role==='native','NATIVE_RESULT_REQUIRED');id(operationId);check(['COMPLETED','REJECTED','NOT_EXECUTED'].includes(outcome));hash(resultHash);return store.transact(s=>{const o=lookupOperation(s,operationId);check(o,'OPERATION_UNKNOWN');if(o.status==='KNOWN'){check(o.outcome===outcome&&o.resultHash===resultHash,'RESULT_CONFLICT');return resultReceipt(s,o);}o.status='KNOWN';o.outcome=outcome;o.resultHash=resultHash;return resultReceipt(s,o);});},
    reconcile({receipt,operation}) {return store.transact(s=>{check(s.grant,'UNPAIRED');const r=verified(receipt,s.grant.body.peers.native.publicKey,'r16.result.v1');keys(r,['schema','role','peerId','grantId','projectId','operationId','operationHash','generation','outcome','resultHash']);check(r.role==='native'&&r.peerId===s.grant.body.peers.native.id&&r.grantId===s.grant.body.id&&['COMPLETED','REJECTED','NOT_EXECUTED'].includes(r.outcome),'RESULT_BINDING');hash(r.resultHash);let o=lookupOperation(s,r.operationId);if(!o&&operation){check(role!=='native'&&(s.pending||s.closing)&&s.active,'DRAIN_REQUIRED');const l=s.active.lease.body,b=verified(operation,s.grant.body.peers.app.publicKey,'r16.operation.v1');keys(b,['schema','id','grantId','projectId','generation','leaseHash','channel','action','payloadHash']);id(b.id);hash(b.payloadHash);check(b.id===r.operationId&&b.grantId===l.grantId&&b.projectId===l.project.id&&b.generation===l.generation&&b.leaseHash===digest(s.active.lease)&&b.channel===l.channel&&l.actions.includes(b.action),'OPERATION_SCOPE');o={id:b.id,hash:digest(operation),projectId:b.projectId,generation:b.generation,status:'UNKNOWN',outcome:null,resultHash:null};s.operations.push(o);}check(o&&o.hash===r.operationHash&&o.projectId===r.projectId&&o.generation===r.generation,'RESULT_BINDING');if(o.status==='KNOWN')check(o.outcome===r.outcome&&o.resultHash===r.resultHash,'RESULT_CONFLICT');o.status='KNOWN';o.outcome=r.outcome;o.resultHash=r.resultHash;return {status:'KNOWN',outcome:o.outcome,resultHash:o.resultHash};});},
    receipt(operationId) {id(operationId);const s=store.snapshot(),o=lookupOperation(s,operationId);check(o?.status==='KNOWN','RECOVERY_UNRESOLVED');return resultReceipt(s,o);},
    revocationAck() {return store.transact(s=>{check(s.fresh?.status==='REVOKED','NOT_REVOKED');return signed({schema:'r16.revocation-ack.v1',grantId:s.grant.body.id,version:s.version,role,peerId:s.grant.body.peers[role].id,newOperationsStopped:true},signingKey);});},
    status() {const s=store.snapshot(),now=store.now();integer(now);const available=!!s.active&&!s.pending&&!s.closing&&s.fresh?.status==='ACTIVE'&&s.fresh.version===s.version&&now>=s.active.lease.body.issuedAt&&now<s.active.lease.body.expiresAt;return {role,available,paired:!!s.grant,version:s.version,connected:!!s.fresh&&s.fresh.status==='ACTIVE',revoked:s.fresh?.status==='REVOKED',generation:s.lastGeneration,closing:!!s.closing,pendingGeneration:s.pending?.lease.body.generation||null,unresolved:s.operations.filter(o=>o.status!=='KNOWN').map(o=>o.id),expiresAt:s.active?.lease.body.expiresAt||null};},
    snapshot:()=>store.snapshot()
  });
}