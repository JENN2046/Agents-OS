// Isolated OS acceptance only. Never reads or replaces production credentials.
import fs from 'node:fs';
import {generateKeyPairSync} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const dir='/var/lib/g1d-os-validation-r1';
try {
  if(process.geteuid()!==0||process.argv.length!==2)throw Error();
  const st=fs.lstatSync('/var/lib/systemd/credential.secret');
  if(!st.isFile()||st.isSymbolicLink()||st.uid!==0||(st.mode&0o077))throw Error();
  fs.mkdirSync(dir,{mode:0o700});
  const pair=generateKeyPairSync('ed25519');
  const bytes=pair.privateKey.export({type:'pkcs8',format:'der'});
  let encrypted;
  try {
    const r=spawnSync('/usr/bin/systemd-creds',['encrypt','--with-key=host','--name=issuer-signing-key','-','-'],{input:bytes,stdio:['pipe','pipe','ignore'],maxBuffer:16384,timeout:15000,killSignal:'SIGTERM',env:{PATH:'/usr/bin:/bin'}});
    if(r.status!==0||r.signal||r.error||!r.stdout?.length)throw Error();
    encrypted=r.stdout;
  } finally {bytes.fill(0);}
  const put=(name,data)=>{const fd=fs.openSync(dir+'/'+name,fs.constants.O_CREAT|fs.constants.O_EXCL|fs.constants.O_WRONLY|fs.constants.O_NOFOLLOW,0o400);try{fs.writeFileSync(fd,data);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}};
  put('issuer-signing-key.cred',encrypted);
  put('expected-public.json',JSON.stringify({purpose:'synthetic-g1d-os-test-only',publicKey:pair.publicKey.export({type:'spki',format:'der'}).toString('base64url')}));
  const fd=fs.openSync(dir,fs.constants.O_DIRECTORY);try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  console.log(JSON.stringify({status:'SYNTHETIC_ENCRYPTED_CREDENTIAL_CREATED',productionCredentialUsed:false}));
} catch {console.log(JSON.stringify({status:'SYNTHETIC_PROVISION_FAILED',partialRetained:true}));process.exitCode=1;}
