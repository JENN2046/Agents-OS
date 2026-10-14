// Test-only child executable. Never ship this as a privileged service.
// It reads *synthetic* disposable test keys from an isolated fixture directory.
import fs from 'node:fs';
import {createPrivateKey} from 'node:crypto';
import {resolveRegisteredProject} from '../../src/lease-core.mjs';
import {runMinimalTrustOnce} from '../../src/minimal-trust-issuer.mjs';
try{
 const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
 const keyBytes=Buffer.from(input.issuerPkcs8,'base64');
 let issuerPrivateKey;
 try{issuerPrivateKey=createPrivateKey({key:keyBytes,format:'der',type:'pkcs8'});}
 finally{keyBytes.fill(0);}
 const resolveProject=(workspace,project)=>resolveRegisteredProject(workspace,project,
   id=>id===input.project.id?input.project:null);
 const value=runMinimalTrustOnce({
   issuerDirectory:input.issuerDirectory,replayDirectory:input.replayDirectory,
   issuerPrivateKey,issuerPublicKey:input.issuerPublicKey,
   releasePublicKey:input.releasePublicKey,
   release:input.release,grantId:input.grantId,resolveProject,
   humanAuthorityPublicKey:input.humanAuthorityPublicKey,
   mode:input.mode,now:()=>input.now,
   envelope:input.envelope,
 });
 process.stdout.write(JSON.stringify({ok:true,value})+'\n');
}catch(error){
 process.stdout.write(JSON.stringify({ok:false,error:error?.code??'TEST_CHILD_REFUSED'})+'\n');
 process.exitCode=1;
}
