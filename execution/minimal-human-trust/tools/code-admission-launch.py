#!/usr/bin/python3
"""Initial HostAdmin bootstrap for exact reviewed public code; never auto-run.
The administrator must review this bootstrap and both external SHA-256 pins.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys

# -I excludes user import paths. Read/hold the script before compilation; no
# user-writable Python module is imported by the root interpreter.
LOADER = r'''import hashlib,os,stat,sys
p,pin=sys.argv[1:3]
assert os.getuid()==os.geteuid()==0
assert len(pin)==64 and all(x in '0123456789abcdef' for x in pin)
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 s=os.fstat(fd)
 assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and 0<s.st_size<=1048576
 raw=os.read(fd,1048577)
 assert len(raw)==s.st_size and hashlib.sha256(raw).hexdigest()==pin
finally: os.close(fd)
sys.argv=[p]+sys.argv[3:]
exec(compile(raw,p,'exec'),{'__name__':'__main__','__file__':p})
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('describe', 'apply', 'readback', 'remove-unused'))
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--source-sha256', required=True)
    p.add_argument('--catalog', required=True, type=Path)
    p.add_argument('--catalog-sha256', required=True)
    p.add_argument('--packet', required=True, type=Path)
    a = p.parse_args()
    for pin in (a.source_sha256, a.catalog_sha256):
        if not re.fullmatch('[a-f0-9]{64}', pin): raise ValueError('EXTERNAL_SHA256_REQUIRED')
    # This is the initial, still-unprotected bootstrap: native HostAdmin review
    # of its exact source and loader is required, not inferred from a checksum.
    for path, pin in ((a.source, a.source_sha256), (a.catalog, a.catalog_sha256)):
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != pin:
            raise ValueError('REVIEWED_SOURCE_OR_CATALOG_DRIFT')
    argv = [str(a.source.resolve()), a.source_sha256, a.mode, '--catalog', str(a.catalog.resolve()),
            '--catalog-sha256', a.catalog_sha256, '--packet', str(a.packet.resolve())]
    if a.mode == 'describe':
        return subprocess.run(['/usr/bin/python3', '-I', '-B', str(a.source.resolve()), *argv[2:]], check=False).returncode
    if os.getuid() != 1000 or not all(os.isatty(fd) for fd in (0, 1, 2)):
        raise ValueError('REAL_LOCAL_ADMIN_TERMINAL_REQUIRED')
    print('只进行指定的代码准入/只读核查/未使用代码撤回；真实范围须在原生窗口核对。', flush=True)
    print('installer SHA-256: ' + a.source_sha256, flush=True)
    print('catalog SHA-256: ' + a.catalog_sha256, flush=True)
    # -k invalidates cached sudo authentication for this exact invocation.
    return subprocess.run(['/usr/bin/sudo', '-k', '--', '/usr/bin/python3', '-I', '-B', '-c', LOADER, *argv],
                          check=False, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'TERM': os.environ.get('TERM', 'xterm')}).returncode


if __name__ == '__main__':
    try: raise SystemExit(main())
    except (OSError, ValueError):
        print('CODE_BOOTSTRAP_REFUSED_NO_AUTOMATIC_RETRY')
        raise SystemExit(78)
