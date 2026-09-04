//! Private transport helper: inspect only the connected socket inherited on fd 0.
//! No Resident initialization, protocol input, path lookup, or N-API export.

use std::io::{self, Write};
use std::process::ExitCode;

use rustix::net::{AddressFamily, SocketType, getpeername, sockopt};

fn credentials() -> Result<String, ()> {
    if std::env::args_os().nth(1).is_some() {
        return Err(());
    }
    let socket = io::stdin();
    if sockopt::socket_domain(&socket).map_err(|_| ())? != AddressFamily::UNIX
        || sockopt::socket_type(&socket).map_err(|_| ())? != SocketType::STREAM
        || getpeername(&socket).map_err(|_| ())?.is_none()
    {
        return Err(());
    }
    let peer = sockopt::socket_peercred(&socket).map_err(|_| ())?;
    let pid = peer.pid.as_raw_pid();
    if pid <= 0 {
        return Err(());
    }
    Ok(format!(
        "{{\"pid\":{pid},\"uid\":{},\"gid\":{}}}\n",
        peer.uid.as_raw(),
        peer.gid.as_raw()
    ))
}

fn main() -> ExitCode {
    if let Ok(output) = credentials()
        && io::stdout().lock().write_all(output.as_bytes()).is_ok()
    {
        return ExitCode::SUCCESS;
    }
    let _ = io::stderr()
        .lock()
        .write_all(b"RESIDENT_DAEMON_IDENTITY_UNAVAILABLE\n");
    ExitCode::FAILURE
}
