// Pure existing-public-state planner; no signer, filesystem or effect authority.
import {combineRevisionEvidence} from './public-state.mjs';
let raw='';for await(const b of process.stdin){if(raw.length+b.length>8*1024*1024)throw Error('REVISION_INPUT_TOO_LARGE');raw+=b;}
const v=JSON.parse(raw);if(JSON.stringify(Object.keys(v).sort())!==JSON.stringify(['cloud','local','requested']))throw Error('FIXED_REVISION_FIELDS_REQUIRED');
process.stdout.write(JSON.stringify(combineRevisionEvidence(v.local,v.cloud,v.requested)));
