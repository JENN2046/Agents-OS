// Real OS validation only: fixed challenge, no issuer business operation.
import fs from 'node:fs';
import {createPublicKey,sign,verify} from 'node:crypto';
import {loadRootIssuerPrivateKey} from '../src/systemd-issuer-credential.mjs';
import {readBoundedOnceInput} from '../src/minimal-trust-issuer-once.mjs';
try {
  if(process.argv.length!==2)throw Error();
  const request=JSON.parse((await readBoundedOnceInput()).toString('utf8'));
  if(JSON.stringify(request)!==JSON.stringify({operation:'credential_proof'}))throw Error();
  const proof=loadRootIssuerPrivateKey();
  const expected=JSON.parse(fs.readFileSync('/var/lib/g1d-os-validation-r1/expected-public.json','utf8'));
  const pub=createPublicKey(proof.key).export({type:'spki',format:'der'}).toString('base64url');
  const challenge=Buffer.from('G1D_REAL_BOUNDED_SOCKET_CREDENTIAL_PROOF_R1');
  if(expected.purpose!=='synthetic-g1d-os-test-only'||pub!==expected.publicKey||
    !verify(null,challenge,createPublicKey(proof.key),sign(null,challenge,proof.key)))throw Error();
  console.log(JSON.stringify({status:'PASS',unit:proof.unit,expectedPublicKeyMatched:true,privateKeyDisclosed:false,productionCredentialUsed:false}));
} catch {console.log(JSON.stringify({status:'REFUSED',privateKeyDisclosed:false}));process.exitCode=1;}
