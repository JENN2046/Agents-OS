//! Rust-owned single ledger-thread and SQLite connection boundary.

use std::path::PathBuf;
use std::sync::mpsc::{self, Receiver, Sender, SyncSender};
use std::thread::{self, JoinHandle, ThreadId};
use std::time::Duration;

use rusqlite::Connection;

use super::{ResidentError, SyntheticOwnership};

const LEDGER_THREAD_NAME: &str = "agents-os-m0a-ledger";

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LedgerSnapshot {
    pub resident_id: String,
    pub incarnation_id: String,
    pub authority_epoch: u64,
    pub owner_thread_name: String,
    pub authoritative_connection_count: u64,
    pub attached_database_count: u64,
    pub journal_mode: String,
    pub synchronous_level: u64,
    pub foreign_keys_enabled: bool,
    pub busy_timeout_ms: u64,
}

enum LedgerCommand {
    Health(Sender<Result<LedgerSnapshot, String>>),
    Shutdown(Sender<()>),
}

pub(super) struct LedgerThread {
    sender: Sender<LedgerCommand>,
    join: Option<JoinHandle<()>>,
    owner_thread_id: ThreadId,
}

impl LedgerThread {
    pub(super) fn start(
        database_path: PathBuf,
        ownership: SyntheticOwnership,
    ) -> Result<Self, ResidentError> {
        let (command_tx, command_rx) = mpsc::channel();
        let (startup_tx, startup_rx) = mpsc::sync_channel(1);
        let join = thread::Builder::new()
            .name(LEDGER_THREAD_NAME.to_owned())
            .spawn(move || run(database_path, ownership, command_rx, startup_tx))
            .map_err(ResidentError::ThreadSpawn)?;
        let owner_thread_id = match startup_rx.recv() {
            Ok(Ok(thread_id)) => thread_id,
            Ok(Err(message)) => {
                let _ = join.join();
                return Err(ResidentError::LedgerStartup(message));
            }
            Err(_) => {
                let _ = join.join();
                return Err(ResidentError::LedgerUnavailable);
            }
        };
        Ok(Self {
            sender: command_tx,
            join: Some(join),
            owner_thread_id,
        })
    }

    pub(super) fn health_snapshot(&self) -> Result<LedgerSnapshot, ResidentError> {
        let (response_tx, response_rx) = mpsc::channel();
        self.sender
            .send(LedgerCommand::Health(response_tx))
            .map_err(|_| ResidentError::LedgerUnavailable)?;
        match response_rx.recv() {
            Ok(Ok(snapshot)) => Ok(snapshot),
            Ok(Err(message)) => Err(ResidentError::LedgerStartup(message)),
            Err(_) => Err(ResidentError::LedgerUnavailable),
        }
    }

    pub(super) fn assert_current_thread_is_owner(&self) -> Result<(), ResidentError> {
        if thread::current().id() == self.owner_thread_id {
            Ok(())
        } else {
            Err(ResidentError::WrongThread)
        }
    }

    pub(super) fn shutdown(&mut self) -> Result<(), ResidentError> {
        let Some(join) = self.join.take() else {
            return Ok(());
        };
        let (response_tx, response_rx) = mpsc::channel();
        let shutdown_observed = self
            .sender
            .send(LedgerCommand::Shutdown(response_tx))
            .is_ok()
            && response_rx.recv().is_ok();
        join.join().map_err(|_| ResidentError::ThreadJoin)?;
        if shutdown_observed {
            Ok(())
        } else {
            Err(ResidentError::LedgerUnavailable)
        }
    }
}

impl Drop for LedgerThread {
    fn drop(&mut self) {
        let _ = self.shutdown();
    }
}

fn run(
    database_path: PathBuf,
    ownership: SyntheticOwnership,
    commands: Receiver<LedgerCommand>,
    startup: SyncSender<Result<ThreadId, String>>,
) {
    let connection = match open_connection(&database_path) {
        Ok(connection) => connection,
        Err(error) => {
            let _ = startup.send(Err(error.to_string()));
            return;
        }
    };
    let owner_thread_id = thread::current().id();
    if startup.send(Ok(owner_thread_id)).is_err() {
        return;
    }

    for command in commands {
        match command {
            LedgerCommand::Health(response) => {
                let result = health_snapshot(&connection, &ownership, owner_thread_id)
                    .map_err(|error| error.to_string());
                let _ = response.send(result);
            }
            LedgerCommand::Shutdown(response) => {
                drop(connection);
                let _ = response.send(());
                return;
            }
        }
    }
}

fn open_connection(database_path: &PathBuf) -> Result<Connection, ResidentError> {
    let connection = Connection::open(database_path)?;
    connection.busy_timeout(Duration::ZERO)?;
    let journal_mode: String =
        connection.pragma_update_and_check(None, "journal_mode", "DELETE", |row| row.get(0))?;
    if journal_mode != "delete" {
        return Err(ResidentError::LedgerStartup(
            "SQLite did not enter DELETE journal mode".to_owned(),
        ));
    }
    connection.pragma_update(None, "synchronous", "EXTRA")?;
    connection.pragma_update(None, "foreign_keys", "ON")?;
    Ok(connection)
}

fn health_snapshot(
    connection: &Connection,
    ownership: &SyntheticOwnership,
    owner_thread_id: ThreadId,
) -> Result<LedgerSnapshot, ResidentError> {
    if thread::current().id() != owner_thread_id {
        return Err(ResidentError::WrongThread);
    }
    let journal_mode: String = connection.query_row("PRAGMA journal_mode", [], |row| row.get(0))?;
    let synchronous_level: i64 =
        connection.query_row("PRAGMA synchronous", [], |row| row.get(0))?;
    let foreign_keys: i64 = connection.query_row("PRAGMA foreign_keys", [], |row| row.get(0))?;
    let busy_timeout_ms: i64 = connection.query_row("PRAGMA busy_timeout", [], |row| row.get(0))?;
    let attached_database_count: i64 =
        connection.query_row("SELECT COUNT(*) FROM pragma_database_list", [], |row| {
            row.get(0)
        })?;
    Ok(LedgerSnapshot {
        resident_id: ownership.identity().resident_id().to_owned(),
        incarnation_id: ownership.incarnation().incarnation_id().to_owned(),
        authority_epoch: ownership.epoch().authority_epoch(),
        owner_thread_name: thread::current()
            .name()
            .unwrap_or(LEDGER_THREAD_NAME)
            .to_owned(),
        authoritative_connection_count: 1,
        attached_database_count: nonnegative_sqlite_integer(attached_database_count)?,
        journal_mode,
        synchronous_level: nonnegative_sqlite_integer(synchronous_level)?,
        foreign_keys_enabled: foreign_keys == 1,
        busy_timeout_ms: nonnegative_sqlite_integer(busy_timeout_ms)?,
    })
}

fn nonnegative_sqlite_integer(value: i64) -> Result<u64, ResidentError> {
    u64::try_from(value).map_err(|_| {
        ResidentError::LedgerStartup("SQLite returned a negative configuration value".to_owned())
    })
}
