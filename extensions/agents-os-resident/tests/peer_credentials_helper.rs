use std::fs::File;
use std::os::fd::OwnedFd;
use std::os::unix::net::{UnixDatagram, UnixStream};
use std::process::{Command, Output, Stdio};

use rustix::net::{AddressFamily, SocketType, socket};

fn run(descriptor: impl Into<OwnedFd>, arguments: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_resident-peer-credentials"))
        .args(arguments)
        .env_clear()
        .stdin(Stdio::from(descriptor.into()))
        .output()
        .expect("run private credentials helper")
}

fn rejected(output: Output) {
    assert!(!output.status.success());
    assert!(output.stdout.is_empty());
    assert_eq!(output.stderr, b"RESIDENT_DAEMON_IDENTITY_UNAVAILABLE\n");
}

#[test]
fn inherited_connected_stream_reports_kernel_peer_credentials_without_tools() {
    let (client, _peer) = UnixStream::pair().expect("synthetic socket pair");
    let output = run(client, &[]);
    assert!(output.status.success());
    assert!(output.stderr.is_empty());
    assert_eq!(
        output.stdout,
        format!(
            "{{\"pid\":{},\"uid\":{},\"gid\":{}}}\n",
            std::process::id(),
            rustix::process::getuid().as_raw(),
            rustix::process::getgid().as_raw()
        )
        .as_bytes()
    );
}

#[test]
fn regular_file_is_rejected_without_reading_its_contents() {
    rejected(run(
        tempfile::tempfile().expect("empty synthetic file"),
        &[],
    ));
    rejected(run(File::open("/dev/null").expect("null input"), &[]));
}

#[test]
fn extra_arguments_are_rejected() {
    let (client, _peer) = UnixStream::pair().expect("synthetic socket pair");
    rejected(run(client, &["--socket-path", "/untrusted/control.sock"]));
}

#[test]
fn connected_datagram_is_rejected() {
    let (client, _peer) = UnixDatagram::pair().expect("synthetic datagram pair");
    rejected(run(client, &[]));
}

#[test]
fn unconnected_stream_and_non_unix_socket_are_rejected() {
    for family in [AddressFamily::UNIX, AddressFamily::INET] {
        let descriptor = socket(family, SocketType::STREAM, None).expect("unbound socket");
        rejected(run(descriptor, &[]));
    }
}
