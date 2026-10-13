import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {generateKeyPairSync,createHash} from 'node:crypto';
import {signed,exportPublicKey,digest,ACTIONS} from '../src/lease-core.mjs';
import {runtimeVersion} from '../authority/runtime-manifest.mjs';
import {inspectReviewedTrustRuntime,BOOTSTRAP_CONFIG,BOOTSTRAP_ROOTS,ENTRY} from '../src/trusted-launcher.mjs';
const pair=()=>generateKeyPairSync('ed25519').privateKey;
const sha=x=>createHash('sha256').update(x).digest('hex');
function fixture(){
 const time=1791900000000,issuer=pair(),publisher=pair(),enroller=pair();
 const id='r16-daily-g1d-isolated-fixture',directory='/opt/r16/releases/'+id;
 const names=[ENTRY,'src/systemd-issuer-credential.mjs','src/minimal-trust-issuer.mjs','src/lease-core.mjs','src/control-clock.mjs'];
 const content=new Map(names.map(name=>[name,fs.readFileSync(new URL('../'+name,import.meta.url))]));
 content.set('host/native-runner.mjs',Buffer.from('// synthetic manifest member only'));
 const manifest={schema:'r16.runtime-code.v1',role:'native',entry:'host/native-runner.mjs',
   files:Object.fromEntries([...content].map(([name,bytes])=>[name,sha(bytes)]))};
 const release=signed({schema:'r16.release.v1',id,issuedAt:time-2000,notAfter:time-1000,
   versions:{app:digest('app'),bridge:digest('bridge'),native:runtimeVersion(manifest,'native')},
   formats:['r16.workspace.v1'],actions:ACTIONS,permissionVersion:1},publisher);
 const handoff=signed({schema:'synthetic-test-only'},enroller);
 const config={schema:'mht.installed-issuer.v1',trustCutoverPhase:'RECOVERY_SHADOW',mode:'recovery_only',
   grantId:'synthetic-grant',issuerPublicKey:exportPublicKey(issuer),releasePublicKey:exportPublicKey(publisher),
   enrollmentAuthorityPublicKey:exportPublicKey(enroller),release,handoff};
 const roots={schema:'mht.trust-roots.v1',installationProfile:'isolated',grantId:config.grantId,
   issuerPublicKey:config.issuerPublicKey,releasePublicKey:config.releasePublicKey,
   enrollmentAuthorityPublicKey:config.enrollmentAuthorityPublicKey,releaseHash:digest(release),handoffHash:digest(handoff)};
 const paths=new Map([...content].map(([name,bytes])=>[directory+'/'+name,bytes]));
 const refresh=()=>{
   paths.set(BOOTSTRAP_CONFIG,Buffer.from(JSON.stringify(config)));
   paths.set(BOOTSTRAP_ROOTS,Buffer.from(JSON.stringify(roots)));
   paths.set(directory+'/native-manifest.json',Buffer.from(JSON.stringify(manifest)));
 };
 refresh();
 const check=()=>inspectReviewedTrustRuntime({euid:0,now:()=>time,readFile:name=>{
   assert.ok(paths.has(name),'unexpected path '+name);return paths.get(name);
 }});
 return {time,config,roots,release,manifest,paths,directory,publisher,enroller,refresh,check};
}
test('actual manifest verifier authenticates every fixture byte for expired recovery-only release',()=>{
 const f=fixture(),result=f.check();
 assert.equal(result.release,f.release.body.id);assert.equal(result.entry,'file://'+f.directory+'/'+ENTRY);
});
test('new active mode is denied even with otherwise valid signed release',()=>{
 const f=fixture();f.config.mode='active';f.refresh();assert.throws(f.check);
});
test('coherent self-signed release and keys cannot replace independently pinned roots',()=>{
 const f=fixture(),attacker=pair();f.config.releasePublicKey=exportPublicKey(attacker);
 f.config.release=signed(f.release.body,attacker);f.refresh();assert.throws(f.check);
});
test('signed release body drift with unchanged release id is denied by exact root hash',()=>{
 const f=fixture();f.config.release=signed({...f.release.body,notAfter:f.time+9999},f.publisher);
 f.refresh();assert.throws(f.check);
});
test('unsigned installed code changes are rejected by real installed-manifest verifier',()=>{
 const f=fixture();f.paths.set(f.directory+'/'+ENTRY,Buffer.from('export const malicious = true;'));
 assert.throws(f.check);
});
test('manifest replacement cannot redirect bootstrap entry without approved release digest',()=>{
 const f=fixture();f.manifest.files[ENTRY]=digest('replacement');f.refresh();assert.throws(f.check);
});
test('future release and missing signed transitive dependency never reach dynamic import',()=>{
 const f=fixture();f.config.release=signed({...f.release.body,issuedAt:f.time+1000,notAfter:f.time+9999},f.publisher);
 f.roots.releaseHash=digest(f.config.release);f.refresh();assert.throws(f.check);
 const g=fixture();delete g.manifest.files['src/systemd-issuer-credential.mjs'];
 g.config.release=signed({...g.release.body,versions:{...g.release.body.versions,native:runtimeVersion(g.manifest,'native')}},g.publisher);
 g.roots.releaseHash=digest(g.config.release);g.refresh();assert.throws(g.check);
});
test('nonroot gate rejects before reading any root configuration',()=>{
 assert.throws(()=>inspectReviewedTrustRuntime({euid:1000,readFile:()=>assert.fail('must not read')}));
});
