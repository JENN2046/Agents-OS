// Only disposable test processes. Loads exact Source19 code; no service/config/key access.
import fs from 'node:fs';import path from 'node:path';import {createRequire,Module} from 'node:module';
import {generateKeyPairSync,createPrivateKey,createPublicKey,createHash} from 'node:crypto';import {pathToFileURL} from 'node:url';
const [phase,root]=process.argv.slice(2);if(!['old','new'].includes(phase)||!root?.startsWith('/tmp/')||fs.statSync(root).uid!==process.geteuid()||process.geteuid()===0)throw Error('ISOLATED_PROCESS_ONLY');process.umask(0o077);
const BASE='/opt/r16/releases/r16-daily-20261015-r15-app-recovery-r6',REL='native/upstream/VCPDistributedServer/Plugin/ProjectForge/';
const sha=b=>createHash('sha256').update(b).digest('hex');const raw=fs.readFileSync(BASE+'/native-manifest.json');if(sha(raw)!=='2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4')throw Error('EXACT_PUBLIC_BASE_REQUIRED');const manifest=JSON.parse(raw);
// ESM imports do not pass Module._extensions. Verify the old execution closure
// before importing it, independently of the CJS dependency checks below.
for(const rel of ['src/lease-core.mjs','host/workspace-dispatcher.mjs','host/headless-host.mjs','src/control-clock.mjs']){
 const file=BASE+'/'+rel,st=fs.lstatSync(file);if(!st.isFile()||st.isSymbolicLink()||sha(fs.readFileSync(file))!==manifest.files[rel])throw Error('ESM_DEPENDENCY_PIN');
}
for(const ext of ['.js','.json','.node']){const old=Module._extensions[ext];Module._extensions[ext]=(mod,file)=>{if(file.startsWith(BASE+'/')&&sha(fs.readFileSync(file))!==manifest.files[file.slice(BASE.length+1)])throw Error('DEPENDENCY_PIN');return old(mod,file);};}
const core=await import(pathToFileURL(BASE+'/src/lease-core.mjs'));const now=()=>2000;
let fixture;
if(phase==='old'){
 for(const n of ['workspace','host','db'])fs.mkdirSync(path.join(root,n),{mode:0o700});
 const key=()=>generateKeyPairSync('ed25519').privateKey,issuer=key(),releaseKey=key(),roles=Object.fromEntries(core.ROLES.map(r=>[r,key()]));
 const wr=path.join(root,'workspace'),st=fs.statSync(wr),workspace={id:'fixture-workspace',root:wr,dev:st.dev,ino:st.ino};
 const grant=core.signed({schema:'r16.workspace.v1',id:'r16-projects-daily',version:1,createdAt:1000,workspace,actions:core.ACTIONS,channel:'main',peers:Object.fromEntries(core.ROLES.map(r=>[r,{id:'fixture-'+r,publicKey:core.exportPublicKey(roles[r])}]))},issuer);
 const versions={app:'34731b300ccad9a1fbfd45b07422d847e8989d7e9dc052b0dda939cd99adb500',bridge:'9c58c33478388003fd52da0cb15736ec951a9bfc9cf29738e20de5d741921352',native:'2516e881b0622b3ac2d53c454e6ccf9950441c5cb3c26a53500b45d3b1dbe7b4'};
 const release=core.signed({schema:'r16.release.v1',id:'isolated-source19-release',issuedAt:1000,notAfter:100000000,formats:['r16.workspace.v1'],versions,actions:core.ACTIONS,permissionVersion:1},releaseKey);
 const oldVersions={app:'235a5b919c65ac1d73290732d2b2014c24a338cc4b6795a5064e804803ec1e7a',bridge:versions.bridge,native:'76319c50acaec649967986c1f12e6923ba4f664ac3230596ed2703fce3470ae6'},rows=[['p2vox','c434da49-055a-43dc-a3e3-695cce137909',30],['pmog2','d0364f8b-3a68-4ca2-a396-7953b29cee4c',38]],ops=[];
 const store=new core.ProtectedStore({directory:path.join(root,'dispatcher'),create:true,now,initial:{kind:'r16.native-dispatch.v1',controls:[],pending:[],projects:rows.map(x=>x[0]),revoked:false,version:0}});store.close();
 for(const [projectId,id,generation] of rows){const proot=path.join(wr,projectId);fs.mkdirSync(proot,{mode:0o700});const lease=core.signed({schema:'r16.lease.v1',phase:'PREPARED',grantId:grant.body.id,grantVersion:1,grantHash:core.digest(grant),project:{id:projectId,workspaceId:workspace.id,root:proot},channel:'main',versions:oldVersions,actions:['find_symbol'],generation,previousGeneration:generation-1,issuedAt:1000,expiresAt:1000+core.LEASE_MS,renewAt:1000+core.LEASE_MS-core.RENEW_BEFORE_MS,requestId:'fixture-'+projectId,releaseHash:core.digest('isolated-old-r15-release')},issuer);
 const op=core.signed({schema:'r16.operation.v1',id,grantId:grant.body.id,projectId,generation,leaseHash:core.digest(lease),channel:'main',action:'find_symbol',payloadHash:core.digest('fixture')},roles.app);ops.push(op);const s=new core.ProtectedStore({directory:path.join(root,'dispatcher/project-'+projectId),create:true,now,initial:{...core.participantInitialState('native'),grant,version:1,lastGeneration:generation,active:{lease},operations:[{id,hash:core.digest(op),projectId,generation,status:'UNKNOWN',outcome:null,resultHash:null}]}});s.close();}
 const der=k=>k.export({format:'der',type:'pkcs8'}).toString('base64');fixture={grant,release,versions,issuer:der(issuer),releaseKey:der(releaseKey),roles:Object.fromEntries(Object.entries(roles).map(([r,k])=>[r,der(k)])),ops};fs.writeFileSync(path.join(root,'ephemeral-test-keys.json'),JSON.stringify(fixture),{mode:0o600});
}else fixture=JSON.parse(fs.readFileSync(path.join(root,'ephemeral-test-keys.json')));
const key=b=>createPrivateKey({key:Buffer.from(b,'base64'),format:'der',type:'pkcs8'}),issuerKey=key(fixture.issuer),roleKey=key(fixture.roles.native);
const REQUIRE=createRequire(BASE+'/native/upstream/package.json');let native;
if(phase==='old')native=REQUIRE('./VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js');
else{
 const compile=name=>{const filename=BASE+'/'+REL+name,m=new Module(filename);m.filename=filename;m.paths=Module._nodeModulePaths(path.dirname(filename));return m;};
 const indexer=compile('indexerClient.js');indexer._compile(fs.readFileSync(new URL('../../../native/upstream/VCPDistributedServer/Plugin/ProjectForge/indexerClient.js',import.meta.url),'utf8'),indexer.filename);
 const m=compile('ProjectForgeService.js'),req=m.require.bind(m);m.require=r=>r==='./indexerClient'?indexer.exports:req(r);m._compile(fs.readFileSync(new URL('../../../native/upstream/VCPDistributedServer/Plugin/ProjectForge/ProjectForgeService.js',import.meta.url),'utf8'),m.filename);native=m.exports;
}
native.initialize({dbPath:path.join(root,'db/project.sqlite'),workspaceService:{list:()=>[{id:'fixture-workspace',alias:'fixture',path:path.join(root,'workspace'),enabled:true}],getActiveWorkspaceId:()=> 'fixture-workspace'},config:{AST_INDEX_ENABLED:false},logger:{log(){},warn(){},error(){}}});native.gui.listProjects();
let dispatcherModule;
if(phase==='old')dispatcherModule=await import(pathToFileURL(BASE+'/host/workspace-dispatcher.mjs'));
else{
 let text=fs.readFileSync(new URL('../payload/host/workspace-dispatcher.mjs',import.meta.url),'utf8');
 // Test namespace only: generated fixture signatures are not production historical signatures.
 text=text.replace(/from '(\.\.\/[^']+)'/g,(_,rel)=>`from '${pathToFileURL(path.resolve(BASE+'/host',rel)).href}'`);
 for(const [i,pin]of ['fd13e74ce69cb8ec30817ca0a48631cf3a6b6b2b08a410cc1b442df41992cc1f','38f6af1386e78e5d7ccd0710077d6a3a5e753e81722dd10f11a3a2ff9bd85da1'].entries())text=text.replace(pin,core.digest(fixture.ops[i]));
 dispatcherModule=await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));
}
const store=new core.ProtectedStore({directory:path.join(root,'dispatcher'),create:false,now});const d=dispatcherModule.createWorkspaceDispatcher({store,directory:store.dir,native,crown:{identityCheck(){throw Error('unused');}},grant:fixture.grant,release:fixture.release,versions:fixture.versions,signingKey:roleKey,issuerKey:core.exportPublicKey(issuerKey),releaseKey:core.exportPublicKey(key(fixture.releaseKey)),issuer:{fresh:async({request})=>{const r=core.verified(request,fixture.grant.body.peers.native.publicKey,'r16.fresh-request.v1');return core.signed({schema:'r16.fresh.v1',grantId:fixture.grant.body.id,version:1,status:'ACTIVE',role:'native',peerId:fixture.grant.body.peers.native.id,challenge:r.challenge,issuedAt:2000,expiresAt:32000},issuerKey);}},workspaceAlias:'fixture',databasePath:path.join(root,'db/project.sqlite'),now,historicalOperations:fixture.ops});
const heads=phase==='old'?await import(pathToFileURL(BASE+'/host/headless-host.mjs')):await import(new URL('../../../host/headless-host.mjs',import.meta.url));
const host=heads.createHeadlessHost({port:d,manifest:{name:'ProjectForge'},serverName:'fixture',connect:async()=>({closed:new Promise(()=>{}),onMessage(){},send(){},async close(){}}),acquireLease:()=>heads.acquireProcessLease(path.join(root,'host')),shutdownMs:1000});
await host.start();
if(phase==='old'){
 process.on('SIGTERM',()=>{void host.stop().then(()=>console.log(JSON.stringify({event:'UNEXPECTED_OLD_CLOSE'})),()=>{process.exitCode=1;console.log(JSON.stringify({event:'OLD_CLOSE_REFUSED',writerStillPresent:fs.existsSync(path.join(root,'host/native-writer.lock'))}));});});
 console.log(JSON.stringify({event:'READY',pid:process.pid,oldSignedCode:true,hasNewShutdown:typeof d.shutdownLocalResources==='function'}));setInterval(()=>{},1000);
}else{const result=await host.shutdownLocalResources();console.log(JSON.stringify({event:'NEW_LOCAL_CLOSED',status:result.status,globalExecution:result.globalExecution,firstStopProof:result.firstStopProof,writerReleased:result.writerReleased,retainedHistory:result.retainedHistory.length}));}
