"""Ordinary-user source-only physical capsule; no service, key, SSH or root use."""
import hashlib,json,os,shutil,stat
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=Path('/home/jenn/Documents/Codex/2026-10-15/G1D-R15-FIRST-STOP-R8-R2/delivery/first-stop-capsule')
OUT=Path('/home/jenn/Documents/Codex/2026-10-15/G1D-EMPTY-ARTIFACT-QUARANTINE-R1/delivery')
SOURCE_PIN='cfa55305623727e1b7607705c7b7a8eb76d2221250368828d21b7779da75af41'
POLICY='1ee6217b557dbce981211929201864bfbdde0b278e84b4081937354b09300a9c'
RUNTIME=('bootstrap.py','entry.py','backend.py','driver.py')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encode(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def build():
 if os.geteuid()==0:raise ValueError('UNPRIVILEGED_BUILD_REQUIRED')
 if OUT.exists():raise ValueError('FRESH_DELIVERY_REQUIRED')
 raw=(SOURCE/'CAPSULE.json').read_bytes()
 if sha(raw)!=SOURCE_PIN:raise ValueError('FROZEN_SOURCE_CAPSULE_DRIFT')
 old=json.loads(raw)
 for name,pin in old['files'].items():
  if '/' in name or name in ('.','..') or sha((SOURCE/name).read_bytes())!=pin:raise ValueError('FROZEN_SOURCE_MEMBER_DRIFT')
 capsule=OUT/'capsule';(capsule/'r8').mkdir(parents=True,mode=0o755);OUT.chmod(0o755);capsule.chmod(0o755)
 for name in [*old['files'],'CAPSULE.json']:shutil.copyfile(SOURCE/name,capsule/'r8'/name)
 for name in RUNTIME:shutil.copyfile(HERE/name,capsule/name)
 for p in capsule.rglob('*'):
  if p.is_file():p.chmod(0o644)
 pins={str(p.relative_to(capsule)):sha(p.read_bytes()) for p in sorted(capsule.rglob('*')) if p.is_file()}
 manifest={'schema':'r16.empty-temp-quarantine-capsule.v1','policyProposalSha256':POLICY,'sourceCapsuleHash':SOURCE_PIN,'nativeExecutionAlreadyAuthorized':False,'files':pins}
 raw=encode(manifest);h=sha(raw);(capsule/'CAPSULE.json').write_bytes(raw);(capsule/'CAPSULE.json').chmod(0o644)
 launcher=(HERE/'launch_terminal.py').read_text().replace('@CAPSULE_SHA@',h).replace('@BOOTSTRAP_SHA@',pins['bootstrap.py'])
 (OUT/'RUN_IN_DESKTOP_TERMINAL.py').write_text(launcher);(OUT/'RUN_IN_DESKTOP_TERMINAL.py').chmod(0o644)
 verifier=(HERE/'verify_delivery.py').read_text().replace('@CAPSULE_SHA@',h).replace('@LAUNCHER_SHA@',sha(launcher.encode()))
 (OUT/'VERIFY_SOURCE_ONLY.py').write_text(verifier);(OUT/'VERIFY_SOURCE_ONLY.py').chmod(0o644)
 record={'schema':'r16.exact-empty-artifact-source-build.v1','capsuleHash':h,'bootstrapSha256':pins['bootstrap.py'],'sourceCapsuleHash':SOURCE_PIN,'policyProposalHash':POLICY,'sealedSourceFiles':len(pins),'sourceRawBytes':sum(p.stat().st_size for p in capsule.rglob('*') if p.is_file()),'payloadCopied':False,'rootUsed':False,'nativeIntentCreated':False,'productionMutationPerformed':False,'productionBusinessAcceptance':False}
 (OUT/'PHYSICAL_BUILD.json').write_text(json.dumps(record,indent=2)+'\n');(OUT/'PHYSICAL_BUILD.json').chmod(0o644);return record
if __name__=='__main__':print(json.dumps(build()))
