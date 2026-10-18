#!/usr/bin/python3 -I
"""Fixed login-bound SSH forwarding; emit no SSH diagnostics or credentials."""
import os
import random
import signal
import subprocess
import time

COMMAND=['/usr/bin/ssh','-F','/dev/null','-T','-N','-o','BatchMode=yes', '-o', 'IdentityAgent=none', '-o', 'IdentitiesOnly=yes', '-i', '/home/jenn/.ssh/TXY_159_75_139_246_ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/etc/r16-owner/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-o','ConnectTimeout=8','-L','127.0.0.1:6016:127.0.0.1:6016','ubuntu@159.75.139.246']
def permanent_failure(text):
    return any(x in text.lower() for x in (b'permission denied',b'host key verification failed',b'remote host identification has changed',b'address already in use',b'bad configuration option',b'unprotected private key'))
def main():
    if os.geteuid()!=1000:return 78
    stopping=False;child=None
    def stop(_signal,_frame):
        nonlocal stopping
        stopping=True
        if child and child.poll() is None:child.send_signal(signal.SIGTERM)
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    attempt=0
    while not stopping:
        started=time.monotonic()
        child=subprocess.Popen(COMMAND,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,env={'PATH':'/usr/bin:/bin','HOME':'/home/jenn','LANG':'C'})
        # SSH emits only bounded diagnostics with default LogLevel, not traffic.
        # Retain at most 8192 bytes; never send these bytes to logs or the caller.
        tail=bytearray()
        while True:
            chunk=child.stderr.read(1024)
            if not chunk:break
            tail.extend(chunk)
            if len(tail)>8192:del tail[:-8192]
        child.wait()
        if stopping:return 0
        if permanent_failure(tail):return 78
        if time.monotonic()-started>=60:attempt=0
        delay=min(60,2**min(attempt,6))*random.uniform(.8,1.2);attempt+=1
        deadline=time.monotonic()+min(60,delay)
        while not stopping and time.monotonic()<deadline:time.sleep(min(.25,max(0,deadline-time.monotonic())))
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:raise SystemExit(78)