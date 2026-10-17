"""Kernel sudo/PTY HostAdmin guard, reused from reviewed code admission.
No Human identity/enrollment or graphical/localness claim is made here.
"""
import os,re,socket,stat,sys
from pathlib import Path
def need(ok,code):
 if not ok:raise ValueError(code)

def _native_proc(pid):
    """Only identity metadata; never read argv, environ or terminal input."""
    raw = Path('/proc/' + str(pid) + '/stat').read_text()
    need(raw.startswith(str(pid) + ' (') and ')' in raw, 'NATIVE_PROC_REFUSED')
    fields = raw[raw.rfind(')') + 2:].split()
    status = Path('/proc/' + str(pid) + '/status').read_text()
    uid_rows = [x.split()[1:] for x in status.splitlines() if x.startswith('Uid:')]
    need(len(fields) >= 20 and len(uid_rows) == 1 and len(uid_rows[0]) == 4
         and all(x.isdecimal() for x in uid_rows[0]), 'NATIVE_PROC_REFUSED')
    return {'pid': pid, 'ppid': int(fields[1]), 'pgrp': int(fields[2]), 'sid': int(fields[3]),
            'ttyNr': int(fields[4]) & 0xffffffff, 'foregroundPgrp': int(fields[5]),
            'startTicks': fields[19], 'uids': tuple(int(x) for x in uid_rows[0])}


def _native_executable(path):
    # Python3 may be the distribution's versioned symlink. Resolve the fixed
    # trusted name, then verify every real ancestor and final inode.
    p = Path(path).resolve(strict=True)
    for q in (*reversed(p.parents), p):
        s = q.lstat()
        need(s.st_uid == 0 and not s.st_mode & 0o022 and not stat.S_ISLNK(s.st_mode), 'NATIVE_EXECUTABLE_REFUSED')
    s = p.stat()
    need(stat.S_ISREG(s.st_mode), 'NATIVE_EXECUTABLE_REFUSED')
    return (s.st_dev, s.st_ino)


def _native_exe_is(pid, expected):
    # /proc/pid/exe is the kernel-held executable inode, not a process name or
    # caller-provided SUDO_* environment claim.
    s = os.stat('/proc/' + str(pid) + '/exe')
    need(stat.S_ISREG(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022
         and (s.st_dev, s.st_ino) == expected, 'NATIVE_EXECUTABLE_REFUSED')


def _native_pts(pid=None):
    rows = [os.fstat(fd) if pid is None else os.stat('/proc/' + str(pid) + '/fd/' + str(fd)) for fd in (0, 1, 2)]
    names = [os.ttyname(fd) if pid is None else os.readlink('/proc/' + str(pid) + '/fd/' + str(fd)) for fd in (0, 1, 2)]
    key = lambda s: (s.st_dev, s.st_ino, s.st_rdev, s.st_uid, s.st_gid, stat.S_IMODE(s.st_mode))
    need(all(re.fullmatch(r'/dev/pts/[0-9]+', n) and n == names[0] for n in names)
         and all(stat.S_ISCHR(s.st_mode) and stat.S_IMODE(s.st_mode) in (0o600, 0o620)
                 and key(s) == key(rows[0]) for s in rows), 'SAME_FOREGROUND_JENN_TTY_REQUIRED')
    # No-follow traversal binds the actual named devpts inode. The /dev/tty
    # alias is intentionally not compared with this real pts metadata.
    root = os.open('/dev', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        pts = os.open('pts', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root)
        try:
            fd = os.open(names[0].rsplit('/', 1)[1], os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=pts)
            try:
                need(key(os.fstat(fd)) == key(rows[0]), 'NATIVE_PTS_NODE_DRIFT')
                if pid is None:
                    need(os.tcgetpgrp(fd) == os.getpgrp(), 'FOREGROUND_NATIVE_TTY_REQUIRED')
            finally: os.close(fd)
        finally: os.close(pts)
    finally: os.close(root)
    return {'path': names[0], 'identity': key(rows[0])}


def native_root_context(host):
    need(os.getuid() == os.geteuid() == 0 and host in ('jenn-System-Product-Name','VM-0-12-ubuntu') and socket.gethostname() == host, 'LOCAL_HOST_ADMIN_REQUIRED')
    need(sys.stdin.isatty() and all(os.isatty(fd) and os.tcgetpgrp(fd) == os.getpgrp() for fd in (0, 1, 2)), 'FOREGROUND_NATIVE_TTY_REQUIRED')
    alias = os.open('/dev/tty', os.O_RDWR | os.O_NOFOLLOW)
    try: need(os.tcgetpgrp(alias) == os.getpgrp(), 'FOREGROUND_NATIVE_TTY_REQUIRED')
    finally: os.close(alias)
    inner = _native_pts()
    need(inner['identity'][3] in (0, 1000), 'JENN_OR_PROVEN_SUDO_PTY_REQUIRED')
    sudo = _native_executable('/usr/bin/sudo')
    python = _native_executable('/usr/bin/python3')
    original = _native_proc(os.getpid())
    need(original['uids'] == (0, 0, 0, 0) and original['pgrp'] == os.getpgrp()
         and original['ttyNr'] == inner['identity'][2] and original['foregroundPgrp'] == os.getpgrp(), 'NATIVE_ROOT_PROCESS_DRIFT')
    _native_exe_is(original['pid'], python)
    chain = []
    pid = original['ppid']
    for _ in range(2):
        row = _native_proc(pid)
        if row['uids'][1:] != (0, 0, 0):
            break
        # sudo may preserve the invoking real UID while retaining root
        # effective/saved/filesystem UIDs. No other real UID is admitted.
        need(row['uids'][0] in (0, 1000), 'NATIVE_SUDO_UID_REFUSED')
        if not chain:
            need(row['sid'] == original['sid'], 'NATIVE_SUDO_SESSION_DRIFT')
        _native_exe_is(pid, sudo)
        chain.append(row)
        pid = row['ppid']
    need(len(chain) in (1, 2), 'TRUSTED_SUDO_ANCESTRY_REQUIRED')
    launcher = _native_proc(pid)
    need(launcher['uids'] == (1000, 1000, 1000, 1000), 'JENN_LAUNCHER_REQUIRED')
    _native_exe_is(pid, python)
    outer = _native_pts(pid)
    need(outer['identity'][3] == 1000, 'JENN_OUTER_PTY_REQUIRED')
    for row in chain:
        need(_native_pts(row['pid']) == outer, 'SUDO_OUTER_PTY_DRIFT')
    need((inner == outer) if inner['identity'][3] == 1000 else inner['path'] != outer['path'], 'SUDO_INNER_PTY_UNPROVEN')
    allowed_outer_groups = {chain[-1]['pgrp'], launcher['pgrp']}
    if inner == outer:
        allowed_outer_groups.add(original['pgrp'])
    # A different controlling TTY cannot be queried with TIOCGPGRP from the
    # inner session (Linux correctly returns ENOTTY). Its real owner process's
    # kernel stat carries tty_nr/tpgid; bind both to the verified outer pts.
    need(launcher['ttyNr'] == outer['identity'][2] and launcher['foregroundPgrp'] in allowed_outer_groups,
         'OUTER_NATIVE_TTY_BACKGROUND')
    if len(chain) == 2:
        need(chain[-1]['ttyNr'] == outer['identity'][2]
             and chain[-1]['foregroundPgrp'] == launcher['foregroundPgrp'], 'SUDO_OUTER_FOREGROUND_DRIFT')
    # This G1 action admits public code under TRUSTED_HOST_ADMIN. Neither a
    # global graphical Display nor a sudo TTY establishes Human identity or
    # physical caller localness. The separate G2/G3 pkexec/auth_self ceremony
    # retains those requirements; this entry never substitutes for it.
    for row in (original, *chain, launcher):
        need(_native_proc(row['pid']) == row, 'NATIVE_PROCESS_ANCESTRY_CHANGED')
        if row in chain: _native_exe_is(row['pid'], sudo)
    _native_exe_is(original['pid'], python)
    _native_exe_is(launcher['pid'], python)
    need(_native_pts() == inner and _native_pts(launcher['pid']) == outer
         and all(_native_pts(row['pid']) == outer for row in chain)
         and all(os.tcgetpgrp(fd) == os.getpgrp() for fd in (0, 1, 2)), 'NATIVE_PTY_CHANGED')
    return {'process': original, 'sudoAncestors': chain, 'launcher': launcher, 'inner': inner, 'outer': outer,
            'outerForegroundPgrp': launcher['foregroundPgrp'],
            'authorityType': 'TRUSTED_HOST_ADMIN_NATIVE_MAINTENANCE', 'humanIdentityConfirmed': False,
            'callerLocalness': 'NOT_ASSERTED_BY_HOST_ADMIN_ADMISSION'}
