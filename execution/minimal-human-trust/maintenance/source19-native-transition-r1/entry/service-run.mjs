// This capsule admits read-only preflight code only. No signer or driver is
// imported, and no credential, journal, service or application state is read.
// A later execution capsule needs a separately reviewed target-C recovery
// contract and exact native authority. Changing argv/environment cannot admit it.
process.stderr.write(JSON.stringify({
 code:'PROTECTED_TRANSITION_ENGINE_NOT_ADMITTED',
 scope:'READONLY_PREFLIGHT_SOURCE',
 productionEffects:0,
 businessAcceptance:false,
 automaticRetry:false
})+'\n');
process.exitCode=78;
