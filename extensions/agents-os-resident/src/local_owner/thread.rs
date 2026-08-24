//! Single Rust ledger thread for the local-owner profile.

use std::path::PathBuf;
use std::sync::mpsc::{self, Sender};
use std::thread::{self, JoinHandle};

use serde_json::Value;

use super::store::{LocalOwnerFault, LocalOwnerStore, MmrCoreFault};
use super::LocalOwnerError;

enum Command {
    Health(Sender<Result<Value, LocalOwnerError>>),
    Prepare {
        input: Value,
        response: Sender<Result<Value, LocalOwnerError>>,
    },
    Submit {
        input: Value,
        fault: LocalOwnerFault,
        response: Sender<Result<Value, LocalOwnerError>>,
    },
    PrepareMmr {
        input: Value,
        response: Sender<Result<Value, LocalOwnerError>>,
    },
    SubmitMmr {
        input: Value,
        fault: MmrCoreFault,
        response: Sender<Result<Value, LocalOwnerError>>,
    },
    QueryMmr {
        input: Value,
        response: Sender<Result<Value, LocalOwnerError>>,
    },
    Query {
        input: Value,
        response: Sender<Result<Value, LocalOwnerError>>,
    },
    Invalidate {
        attachment_generation: u64,
        response: Sender<Value>,
    },
    Restore {
        input: Value,
        response: Sender<Result<Value, LocalOwnerError>>,
    },
    ReplicaActivate {
        input: Value,
        response: Sender<Result<Value, LocalOwnerError>>,
    },
    RemovalClaim {
        input: Value,
        response: Sender<Result<Value, LocalOwnerError>>,
    },
    Shutdown(Sender<()>),
}

pub struct LocalOwnerThread {
    sender: Sender<Command>,
    join: Option<JoinHandle<()>>,
}

impl LocalOwnerThread {
    pub fn start(
        database_path: PathBuf,
        process_nonce: Option<Vec<u8>>,
        initialize_genesis: bool,
    ) -> Result<Self, LocalOwnerError> {
        let (command_tx, command_rx) = mpsc::channel();
        let (startup_tx, startup_rx) = mpsc::sync_channel(1);
        let join = thread::Builder::new()
            .name("agents-os-local-owner-ledger".to_owned())
            .spawn(move || {
                let mut store = match LocalOwnerStore::open_admitted(
                    &database_path,
                    process_nonce.as_deref(),
                    initialize_genesis,
                ) {
                    Ok(store) => {
                        let _ = startup_tx.send(Ok(()));
                        store
                    }
                    Err(error) => {
                        let _ = startup_tx.send(Err(error.fixed_code().to_owned()));
                        return;
                    }
                };
                while let Ok(command) = command_rx.recv() {
                    match command {
                        Command::Health(response) => {
                            let _ = response.send(store.health());
                        }
                        Command::Prepare { input, response } => {
                            let _ = response.send(store.prepare_proposal(&input));
                        }
                        Command::Submit {
                            input,
                            fault,
                            response,
                        } => {
                            let _ = response.send(store.submit_consent(&input, fault));
                        }
                        Command::PrepareMmr { input, response } => {
                            let _ = response.send(store.prepare_mmr_mutation(&input));
                        }
                        Command::SubmitMmr {
                            input,
                            fault,
                            response,
                        } => {
                            let _ = response.send(store.submit_mmr_consent(&input, fault));
                        }
                        Command::QueryMmr { input, response } => {
                            let _ = response.send(store.query_mmr_core(&input));
                        }
                        Command::Query { input, response } => {
                            let _ = response.send(store.query(&input));
                        }
                        Command::Invalidate {
                            attachment_generation,
                            response,
                        } => {
                            let _ = response.send(store.invalidate(attachment_generation));
                        }
                        Command::Restore { input, response } => {
                            let _ = response.send(store.restore(&input));
                        }
                        Command::ReplicaActivate { input, response } => {
                            let _ = response.send(store.attempt_replica_activation(&input));
                        }
                        Command::RemovalClaim { input, response } => {
                            let _ = response.send(store.evaluate_removal_claim(&input));
                        }
                        Command::Shutdown(response) => {
                            let _ = response.send(());
                            break;
                        }
                    }
                }
            })
            .map_err(LocalOwnerError::Io)?;
        match startup_rx.recv() {
            Ok(Ok(())) => Ok(Self {
                sender: command_tx,
                join: Some(join),
            }),
            Ok(Err(_)) => {
                let _ = join.join();
                Err(LocalOwnerError::StartupFailed)
            }
            Err(_) => {
                let _ = join.join();
                Err(LocalOwnerError::ThreadUnavailable)
            }
        }
    }

    pub fn health(&self) -> Result<Value, LocalOwnerError> {
        self.request(Command::Health)
    }

    pub fn prepare(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.request(|response| Command::Prepare { input, response })
    }

    pub fn submit(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.submit_with_fault(input, LocalOwnerFault::None)
    }

    pub fn submit_with_fault(
        &self,
        input: Value,
        fault: LocalOwnerFault,
    ) -> Result<Value, LocalOwnerError> {
        self.request(|response| Command::Submit {
            input,
            fault,
            response,
        })
    }

    pub fn query(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.request(|response| Command::Query { input, response })
    }

    pub fn prepare_mmr(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.request(|response| Command::PrepareMmr { input, response })
    }

    pub fn submit_mmr(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.submit_mmr_with_fault(input, MmrCoreFault::None)
    }

    pub fn submit_mmr_with_fault(
        &self,
        input: Value,
        fault: MmrCoreFault,
    ) -> Result<Value, LocalOwnerError> {
        self.request(|response| Command::SubmitMmr {
            input,
            fault,
            response,
        })
    }

    pub fn query_mmr(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.request(|response| Command::QueryMmr { input, response })
    }

    pub fn invalidate(&self, attachment_generation: u64) -> Result<Value, LocalOwnerError> {
        let (response_tx, response_rx) = mpsc::channel();
        self.sender
            .send(Command::Invalidate {
                attachment_generation,
                response: response_tx,
            })
            .map_err(|_| LocalOwnerError::ThreadUnavailable)?;
        response_rx
            .recv()
            .map_err(|_| LocalOwnerError::ThreadUnavailable)
    }

    pub fn restore(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.request(|response| Command::Restore { input, response })
    }

    pub fn attempt_replica_activation(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.request(|response| Command::ReplicaActivate { input, response })
    }

    pub fn evaluate_removal_claim(&self, input: Value) -> Result<Value, LocalOwnerError> {
        self.request(|response| Command::RemovalClaim { input, response })
    }

    pub fn shutdown(mut self) -> Result<(), LocalOwnerError> {
        let (response_tx, response_rx) = mpsc::channel();
        self.sender
            .send(Command::Shutdown(response_tx))
            .map_err(|_| LocalOwnerError::ThreadUnavailable)?;
        response_rx
            .recv()
            .map_err(|_| LocalOwnerError::ThreadUnavailable)?;
        self.join
            .take()
            .ok_or(LocalOwnerError::ThreadUnavailable)?
            .join()
            .map_err(|_| LocalOwnerError::ThreadUnavailable)
    }

    fn request<T>(
        &self,
        make: impl FnOnce(Sender<Result<Value, LocalOwnerError>>) -> T,
    ) -> Result<Value, LocalOwnerError>
    where
        T: Into<Command>,
    {
        let (response_tx, response_rx) = mpsc::channel();
        self.sender
            .send(make(response_tx).into())
            .map_err(|_| LocalOwnerError::ThreadUnavailable)?;
        response_rx
            .recv()
            .map_err(|_| LocalOwnerError::ThreadUnavailable)?
    }
}

impl Drop for LocalOwnerThread {
    fn drop(&mut self) {
        if self.join.is_none() {
            return;
        }
        let (response_tx, response_rx) = mpsc::channel();
        if self.sender.send(Command::Shutdown(response_tx)).is_ok() {
            let _ = response_rx.recv();
        }
        if let Some(join) = self.join.take() {
            let _ = join.join();
        }
    }
}
