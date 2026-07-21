//! Rust-owned single ledger-thread and SQLite connection boundary.

use std::path::PathBuf;
use std::sync::mpsc::{self, Receiver, Sender, SyncSender};
use std::thread::{self, JoinHandle, ThreadId};
use std::time::Duration;

use rusqlite::{Connection, TransactionBehavior, params};
use serde_json::{Value, json};

use crate::canonical::fingerprint::canonical_fingerprint;
use crate::canonical::jcs::canonicalize_json;
use crate::home::candidate::HomeCandidateRevision;
use crate::home::handoff::HomeIntentHandoffCandidate;
use crate::ledger::LedgerError;
use crate::ledger::recovery::{self, IntegratedWitness, LedgerCounts, M0BIntegratedWitness};
use crate::ledger::replay::{
    self, OutboxEnqueueFault, ReplayObservation, RequestIdentity, TerminalIntake,
    TerminalIntakeObservation, TerminalOutboxIntake, TerminalOutboxObservation,
    TerminalValidationCompletionIntake, TerminalValidationCompletionObservation,
    ValidationCompletionFault,
};
use crate::ledger::schema::{self, SchemaSnapshot};
use crate::ledger::transaction::{
    self, CanonicalFactInput, EventInput, FactAdvanceResult, HomeCommitFault,
    HomeCommitObservation, HomeHeadExpectation, PointerExpectation, TransactionFault,
};
use crate::reducers::effect_admission::SyntheticOutboxIntent;

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
    InitializeSchema(Sender<Result<SchemaSnapshot, String>>),
    MigrateSchemaV2(Sender<Result<SchemaSnapshot, String>>),
    VerifySchema(Sender<Result<SchemaSnapshot, String>>),
    AdvanceFact(Box<AdvanceFactCommand>),
    CommitHomeCandidate {
        candidate: HomeCandidateRevision,
        expected: HomeHeadExpectation,
        fault: HomeCommitFault,
        response: Sender<Result<HomeCommitObservation, String>>,
    },
    CommitHomeHandoff {
        handoff: HomeIntentHandoffCandidate,
        intent_candidate_id: String,
        fault: HomeCommitFault,
        response: Sender<Result<HomeCommitObservation, String>>,
    },
    RegisterOrResolve {
        request: RequestIdentity,
        response: Sender<Result<ReplayObservation, String>>,
    },
    TerminalIndeterminate {
        intake: TerminalIntake,
        response: Sender<Result<TerminalIntakeObservation, String>>,
    },
    TerminalSyntheticOutbox {
        intake: TerminalOutboxIntake,
        fault: OutboxEnqueueFault,
        response: Sender<Result<TerminalOutboxObservation, String>>,
    },
    TerminalSyntheticGoalPlan {
        intake: TerminalValidationCompletionIntake,
        response: Sender<Result<TerminalValidationCompletionObservation, String>>,
    },
    TerminalSyntheticHomeIntent {
        intake: TerminalValidationCompletionIntake,
        response: Sender<Result<TerminalValidationCompletionObservation, String>>,
    },
    ResolveSyntheticOutbox {
        intent_ref: String,
        response: Sender<Result<Option<SyntheticOutboxIntent>, String>>,
    },
    TerminalSyntheticValidation {
        intake: TerminalValidationCompletionIntake,
        fault: ValidationCompletionFault,
        response: Sender<Result<TerminalValidationCompletionObservation, String>>,
    },
    TerminalSyntheticCompletion {
        intake: TerminalValidationCompletionIntake,
        fault: ValidationCompletionFault,
        response: Sender<Result<TerminalValidationCompletionObservation, String>>,
    },
    Counts(Sender<Result<LedgerCounts, String>>),
    IntegratedWitness(Sender<Result<IntegratedWitness, String>>),
    M0BIntegratedWitness(Sender<Result<M0BIntegratedWitness, String>>),
    Shutdown(Sender<()>),
}

struct AdvanceFactCommand {
    fact: CanonicalFactInput,
    expected: PointerExpectation,
    event: EventInput,
    fault: TransactionFault,
    response: Sender<Result<FactAdvanceResult, String>>,
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

    pub(super) fn initialize_schema(&self) -> Result<SchemaSnapshot, ResidentError> {
        self.request(LedgerCommand::InitializeSchema)
    }

    pub(super) fn verify_schema(&self) -> Result<SchemaSnapshot, ResidentError> {
        self.request(LedgerCommand::VerifySchema)
    }

    pub(super) fn migrate_schema_v2(&self) -> Result<SchemaSnapshot, ResidentError> {
        self.request(LedgerCommand::MigrateSchemaV2)
    }

    pub(super) fn advance_fact(
        &self,
        fact: CanonicalFactInput,
        expected: PointerExpectation,
        event: EventInput,
        fault: TransactionFault,
    ) -> Result<FactAdvanceResult, ResidentError> {
        self.request(|response| {
            LedgerCommand::AdvanceFact(Box::new(AdvanceFactCommand {
                fact,
                expected,
                event,
                fault,
                response,
            }))
        })
    }

    pub(super) fn commit_home_candidate(
        &self,
        candidate: HomeCandidateRevision,
        expected: HomeHeadExpectation,
        fault: HomeCommitFault,
    ) -> Result<HomeCommitObservation, ResidentError> {
        self.request(|response| LedgerCommand::CommitHomeCandidate {
            candidate,
            expected,
            fault,
            response,
        })
    }

    pub(super) fn commit_home_handoff(
        &self,
        handoff: HomeIntentHandoffCandidate,
        intent_candidate_id: String,
        fault: HomeCommitFault,
    ) -> Result<HomeCommitObservation, ResidentError> {
        self.request(|response| LedgerCommand::CommitHomeHandoff {
            handoff,
            intent_candidate_id,
            fault,
            response,
        })
    }

    pub(super) fn register_or_resolve(
        &self,
        request: RequestIdentity,
    ) -> Result<ReplayObservation, ResidentError> {
        self.request(|response| LedgerCommand::RegisterOrResolve { request, response })
    }

    pub(super) fn terminal_indeterminate(
        &self,
        intake: TerminalIntake,
    ) -> Result<TerminalIntakeObservation, ResidentError> {
        self.request(|response| LedgerCommand::TerminalIndeterminate { intake, response })
    }

    pub(super) fn terminal_synthetic_outbox(
        &self,
        intake: TerminalOutboxIntake,
        fault: OutboxEnqueueFault,
    ) -> Result<TerminalOutboxObservation, ResidentError> {
        self.request(|response| LedgerCommand::TerminalSyntheticOutbox {
            intake,
            fault,
            response,
        })
    }

    pub(super) fn terminal_synthetic_goal_plan(
        &self,
        intake: TerminalValidationCompletionIntake,
    ) -> Result<TerminalValidationCompletionObservation, ResidentError> {
        self.request(|response| LedgerCommand::TerminalSyntheticGoalPlan { intake, response })
    }

    pub(super) fn terminal_synthetic_home_intent(
        &self,
        intake: TerminalValidationCompletionIntake,
    ) -> Result<TerminalValidationCompletionObservation, ResidentError> {
        self.request(|response| LedgerCommand::TerminalSyntheticHomeIntent { intake, response })
    }

    pub(super) fn resolve_synthetic_outbox(
        &self,
        intent_ref: String,
    ) -> Result<Option<SyntheticOutboxIntent>, ResidentError> {
        self.request(|response| LedgerCommand::ResolveSyntheticOutbox {
            intent_ref,
            response,
        })
    }

    pub(super) fn terminal_synthetic_validation(
        &self,
        intake: TerminalValidationCompletionIntake,
        fault: ValidationCompletionFault,
    ) -> Result<TerminalValidationCompletionObservation, ResidentError> {
        self.request(|response| LedgerCommand::TerminalSyntheticValidation {
            intake,
            fault,
            response,
        })
    }

    pub(super) fn terminal_synthetic_completion(
        &self,
        intake: TerminalValidationCompletionIntake,
        fault: ValidationCompletionFault,
    ) -> Result<TerminalValidationCompletionObservation, ResidentError> {
        self.request(|response| LedgerCommand::TerminalSyntheticCompletion {
            intake,
            fault,
            response,
        })
    }

    pub(super) fn counts(&self) -> Result<LedgerCounts, ResidentError> {
        self.request(LedgerCommand::Counts)
    }

    pub(super) fn integrated_witness(&self) -> Result<IntegratedWitness, ResidentError> {
        self.request(LedgerCommand::IntegratedWitness)
    }

    pub(super) fn m0b_integrated_witness(&self) -> Result<M0BIntegratedWitness, ResidentError> {
        self.request(LedgerCommand::M0BIntegratedWitness)
    }

    fn request<T>(
        &self,
        command: impl FnOnce(Sender<Result<T, String>>) -> LedgerCommand,
    ) -> Result<T, ResidentError> {
        let (response_tx, response_rx) = mpsc::channel();
        self.sender
            .send(command(response_tx))
            .map_err(|_| ResidentError::LedgerUnavailable)?;
        match response_rx.recv() {
            Ok(Ok(result)) => Ok(result),
            Ok(Err(message)) => Err(ResidentError::LedgerOperation(message)),
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
    let mut connection = match open_connection(&database_path) {
        Ok(connection) => connection,
        Err(error) => {
            let _ = startup.send(Err(error.to_string()));
            return;
        }
    };
    let owner_thread_id = thread::current().id();
    let startup_result = schema::initialize_v1(&mut connection)
        .and_then(|_| bind_or_verify_ownership(&mut connection, &ownership))
        .and_then(|_| replay::ensure_closed_synthetic_registry(&mut connection));
    if let Err(error) = startup_result {
        let _ = startup.send(Err(error.to_string()));
        return;
    }
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
            LedgerCommand::InitializeSchema(response) => {
                let result = schema::verify_schema(&connection)
                    .and_then(|snapshot| {
                        bind_or_verify_ownership(&mut connection, &ownership)?;
                        replay::verify_closed_synthetic_registry(&connection)?;
                        Ok(snapshot)
                    })
                    .map_err(|error| error.to_string());
                let _ = response.send(result);
            }
            LedgerCommand::MigrateSchemaV2(response) => {
                let result = schema::migrate_synthetic_test_v1_to_v2(&mut connection)
                    .and_then(|snapshot| {
                        bind_or_verify_ownership(&mut connection, &ownership)?;
                        replay::verify_closed_synthetic_registry(&connection)?;
                        Ok(snapshot)
                    })
                    .map_err(|error| error.to_string());
                let _ = response.send(result);
            }
            LedgerCommand::VerifySchema(response) => {
                let result = schema::verify_schema(&connection)
                    .and_then(|snapshot| {
                        bind_or_verify_ownership(&mut connection, &ownership)?;
                        replay::verify_closed_synthetic_registry(&connection)?;
                        Ok(snapshot)
                    })
                    .map_err(|error| error.to_string());
                let _ = response.send(result);
            }
            LedgerCommand::AdvanceFact(command) => {
                let AdvanceFactCommand {
                    fact,
                    expected,
                    event,
                    fault,
                    response,
                } = *command;
                let _ = response.send(
                    transaction::advance_fact(&mut connection, &fact, &expected, &event, fault)
                        .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::CommitHomeCandidate {
                candidate,
                expected,
                fault,
                response,
            } => {
                let _ = response.send(
                    transaction::commit_home_candidate(
                        &mut connection,
                        &candidate,
                        &expected,
                        fault,
                    )
                    .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::CommitHomeHandoff {
                handoff,
                intent_candidate_id,
                fault,
                response,
            } => {
                let _ = response.send(
                    transaction::commit_home_handoff(
                        &mut connection,
                        &handoff,
                        &intent_candidate_id,
                        fault,
                    )
                    .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::RegisterOrResolve { request, response } => {
                let _ = response.send(
                    replay::register_or_resolve(&mut connection, &request)
                        .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::TerminalIndeterminate { intake, response } => {
                let _ = response.send(
                    replay::terminal_indeterminate(&mut connection, &intake)
                        .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::TerminalSyntheticOutbox {
                intake,
                fault,
                response,
            } => {
                let _ = response.send(
                    replay::terminal_synthetic_outbox(&mut connection, &intake, fault)
                        .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::ResolveSyntheticOutbox {
                intent_ref,
                response,
            } => {
                let _ = response.send(
                    schema::verify_schema(&connection)
                        .and_then(|_| replay::resolve_synthetic_outbox(&connection, &intent_ref))
                        .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::TerminalSyntheticGoalPlan { intake, response } => {
                let _ = response.send(
                    replay::terminal_synthetic_goal_plan(&mut connection, &intake)
                        .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::TerminalSyntheticHomeIntent { intake, response } => {
                let _ = response.send(
                    replay::terminal_synthetic_home_intent(&mut connection, &intake)
                        .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::TerminalSyntheticValidation {
                intake,
                fault,
                response,
            } => {
                let _ = response.send(
                    replay::terminal_synthetic_validation(&mut connection, &intake, fault)
                        .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::TerminalSyntheticCompletion {
                intake,
                fault,
                response,
            } => {
                let _ = response.send(
                    replay::terminal_synthetic_completion(&mut connection, &intake, fault)
                        .map_err(|error| error.to_string()),
                );
            }
            LedgerCommand::Counts(response) => {
                let result = schema::verify_schema(&connection)
                    .and_then(|_| bind_or_verify_ownership(&mut connection, &ownership))
                    .and_then(|_| replay::verify_closed_synthetic_registry(&connection))
                    .and_then(|_| recovery::counts(&connection))
                    .map_err(|error| error.to_string());
                let _ = response.send(result);
            }
            LedgerCommand::IntegratedWitness(response) => {
                let result = schema::verify_schema(&connection)
                    .and_then(|_| bind_or_verify_ownership(&mut connection, &ownership))
                    .and_then(|_| replay::verify_closed_synthetic_registry(&connection))
                    .and_then(|_| recovery::integrated_witness(&connection))
                    .map_err(|error| error.to_string());
                let _ = response.send(result);
            }
            LedgerCommand::M0BIntegratedWitness(response) => {
                let result = schema::verify_schema(&connection)
                    .and_then(|_| bind_or_verify_ownership(&mut connection, &ownership))
                    .and_then(|_| replay::verify_closed_synthetic_registry(&connection))
                    .and_then(|_| recovery::m0b_integrated_witness(&connection))
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

fn bind_or_verify_ownership(
    connection: &mut Connection,
    ownership: &SyntheticOwnership,
) -> Result<(), LedgerError> {
    let resident_id = ownership.identity().resident_id();
    let identity_revision = ownership.identity().identity_revision();
    let identity_fingerprint = ownership.identity().identity_fingerprint();
    let incarnation_id = ownership.incarnation().incarnation_id();
    let incarnation_revision = ownership.incarnation().incarnation_revision();
    let process_nonce_fingerprint = ownership.incarnation().process_nonce_fingerprint();
    let authority_epoch = ownership.epoch().authority_epoch();
    let epoch_fingerprint = ownership.epoch().epoch_fingerprint();
    let previous_epoch = ownership.epoch().expected_previous_authority_epoch();
    let previous_epoch_fingerprint = ownership.epoch().previous_authority_epoch_fingerprint();
    let previous_incarnation_id = ownership.epoch().previous_incarnation_id();
    let event_sequence = authority_epoch;
    let event_id = format!("event:f3-ownership:{resident_id}:{authority_epoch}");
    let event_kind = "RESIDENT_OWNERSHIP_STARTED";
    let event_bytes = canonical_json_bytes(&json!({
        "aggregate_ref": resident_id,
        "aggregate_revision": authority_epoch,
        "command_id": null,
        "event_id": event_id,
        "event_kind": event_kind,
        "event_sequence": event_sequence,
        "incarnation_id": incarnation_id,
        "predecessor_event_fingerprint": previous_epoch_fingerprint,
        "runtime_usable": false
    }))?;
    let event_fingerprint = canonical_fingerprint(&event_bytes)?;
    let witness_reservation_ref =
        format!("reservation:SYNTHETIC_TEST:{resident_id}:{authority_epoch}");
    let witness_reservation_bytes = canonical_json_bytes(&json!([
        "agents-os.synthetic-witness-reservation.v0.1",
        {
            "authority_epoch": authority_epoch,
            "incarnation_id": incarnation_id,
            "resident_id": resident_id,
            "runtime_usable": false
        }
    ]))?;
    let witness_reservation_fingerprint = canonical_fingerprint(&witness_reservation_bytes)?;
    let epoch_bytes = canonical_json_bytes(&json!([
        "agents-os.synthetic-resident-authority-epoch.v0.1",
        {
            "authority_epoch": authority_epoch,
            "authority_generation": authority_epoch,
            "expected_previous_authority_epoch": previous_epoch,
            "incarnation_id": incarnation_id,
            "incarnation_revision": incarnation_revision,
            "previous_authority_epoch_fingerprint": previous_epoch_fingerprint,
            "previous_incarnation_id": previous_incarnation_id,
            "process_nonce_fingerprint": process_nonce_fingerprint,
            "resident_id": resident_id
        }
    ]))?;
    if canonical_fingerprint(&epoch_bytes)? != epoch_fingerprint {
        return Err(LedgerError::SchemaMismatch(
            "synthetic ownership epoch bytes do not match the supplied fingerprint".to_owned(),
        ));
    }

    let identity_count: i64 =
        connection.query_row("SELECT COUNT(*) FROM resident_identity", [], |row| {
            row.get(0)
        })?;
    let incarnation_count: i64 =
        connection.query_row("SELECT COUNT(*) FROM resident_incarnation", [], |row| {
            row.get(0)
        })?;
    let epoch_count: i64 =
        connection.query_row("SELECT COUNT(*) FROM resident_authority_epoch", [], |row| {
            row.get(0)
        })?;
    if (identity_count, incarnation_count, epoch_count) == (0, 0, 0) {
        let event_count: i64 =
            connection.query_row("SELECT COUNT(*) FROM event", [], |row| row.get(0))?;
        if authority_epoch != 1
            || previous_epoch.is_some()
            || previous_epoch_fingerprint.is_some()
            || previous_incarnation_id.is_some()
            || event_count != 0
        {
            return Err(LedgerError::SchemaMismatch(
                "a new ledger requires the exact genesis ownership tuple".to_owned(),
            ));
        }
        let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
        tx.execute(
            "INSERT INTO resident_identity(resident_id,identity_revision,identity_fingerprint,created_event_sequence) VALUES(?1,?2,?3,?4)",
            params![resident_id, identity_revision as i64, identity_fingerprint, event_sequence as i64],
        )?;
        tx.execute(
            "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,command_id,canonical_bytes,event_fingerprint,predecessor_event_fingerprint) VALUES(?1,?2,?3,?4,?5,NULL,?6,?7,NULL)",
            params![event_sequence as i64, event_id, event_kind, resident_id, authority_epoch as i64, event_bytes, event_fingerprint],
        )?;
        tx.execute(
            "INSERT INTO resident_incarnation(incarnation_id,resident_id,incarnation_revision,process_nonce_fingerprint,created_event_sequence,created_event_id,created_event_fingerprint,created_event_kind,created_event_aggregate_ref,created_event_aggregate_revision) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10)",
            params![incarnation_id, resident_id, incarnation_revision as i64, process_nonce_fingerprint, event_sequence as i64, event_id, event_fingerprint, event_kind, resident_id, authority_epoch as i64],
        )?;
        tx.execute(
            "INSERT INTO resident_authority_epoch(resident_id,authority_epoch,epoch_fingerprint,expected_previous_authority_epoch,previous_authority_epoch_fingerprint,authority_generation,witness_reservation_ref,witness_reservation_fingerprint,incarnation_id,incarnation_revision,previous_incarnation_id,restore_decision_ref,restore_decision_fingerprint,ownership_event_sequence,ownership_event_id,ownership_event_fingerprint,ownership_event_kind,ownership_event_aggregate_ref,ownership_event_aggregate_revision,canonical_bytes) VALUES(?1,?2,?3,NULL,NULL,?4,?5,?6,?7,?8,NULL,NULL,NULL,?9,?10,?11,?12,?13,?14,?15)",
            params![resident_id, authority_epoch as i64, epoch_fingerprint, authority_epoch as i64, witness_reservation_ref, witness_reservation_fingerprint, incarnation_id, incarnation_revision as i64, event_sequence as i64, event_id, event_fingerprint, event_kind, resident_id, authority_epoch as i64, epoch_bytes],
        )?;
        let violations: i64 =
            tx.query_row("SELECT COUNT(*) FROM pragma_foreign_key_check", [], |row| {
                row.get(0)
            })?;
        if violations != 0 {
            return Err(LedgerError::SchemaMismatch(
                "ownership binding failed deferred foreign-key validation".to_owned(),
            ));
        }
        tx.commit()?;
    }

    let exact_identity: i64 = connection.query_row(
        "SELECT COUNT(*) FROM resident_identity WHERE resident_id=?1 AND identity_revision=?2 AND identity_fingerprint=?3 AND created_event_sequence=?4",
        params![resident_id, identity_revision as i64, identity_fingerprint, event_sequence as i64],
        |row| row.get(0),
    )?;
    let exact_incarnation: i64 = connection.query_row(
        "SELECT COUNT(*) FROM resident_incarnation WHERE incarnation_id=?1 AND resident_id=?2 AND incarnation_revision=?3 AND process_nonce_fingerprint=?4 AND created_event_sequence=?5 AND created_event_id=?6 AND created_event_fingerprint=?7 AND created_event_kind=?8 AND created_event_aggregate_ref=?9 AND created_event_aggregate_revision=?10",
        params![incarnation_id, resident_id, incarnation_revision as i64, process_nonce_fingerprint, event_sequence as i64, event_id, event_fingerprint, event_kind, resident_id, authority_epoch as i64],
        |row| row.get(0),
    )?;
    let exact_epoch: i64 = connection.query_row(
        "SELECT COUNT(*) FROM resident_authority_epoch WHERE resident_id=?1 AND authority_epoch=?2 AND epoch_fingerprint=?3 AND expected_previous_authority_epoch IS ?4 AND previous_authority_epoch_fingerprint IS ?5 AND authority_generation=?6 AND witness_reservation_ref=?7 AND witness_reservation_fingerprint=?8 AND incarnation_id=?9 AND incarnation_revision=?10 AND previous_incarnation_id IS ?11 AND restore_decision_ref IS NULL AND restore_decision_fingerprint IS NULL AND ownership_event_sequence=?12 AND ownership_event_id=?13 AND ownership_event_fingerprint=?14 AND ownership_event_kind=?15 AND ownership_event_aggregate_ref=?16 AND ownership_event_aggregate_revision=?17 AND canonical_bytes=?18",
        params![resident_id, authority_epoch as i64, epoch_fingerprint, previous_epoch.map(|v| v as i64), previous_epoch_fingerprint, authority_epoch as i64, witness_reservation_ref, witness_reservation_fingerprint, incarnation_id, incarnation_revision as i64, previous_incarnation_id, event_sequence as i64, event_id, event_fingerprint, event_kind, resident_id, authority_epoch as i64, epoch_bytes],
        |row| row.get(0),
    )?;
    let exact_event: i64 = connection.query_row(
        "SELECT COUNT(*) FROM event WHERE event_sequence=?1 AND event_id=?2 AND event_kind=?3 AND aggregate_ref=?4 AND aggregate_revision=?5 AND command_id IS NULL AND canonical_bytes=?6 AND event_fingerprint=?7 AND predecessor_event_fingerprint IS ?8",
        params![event_sequence as i64, event_id, event_kind, resident_id, authority_epoch as i64, event_bytes, event_fingerprint, previous_epoch_fingerprint],
        |row| row.get(0),
    )?;
    if identity_count > 1
        || incarnation_count > 1
        || epoch_count > 1
        || (exact_identity, exact_incarnation, exact_epoch, exact_event) != (1, 1, 1, 1)
    {
        return Err(LedgerError::SchemaMismatch(
            "stored Resident ownership does not equal the supplied immutable tuple".to_owned(),
        ));
    }
    Ok(())
}

fn canonical_json_bytes(value: &Value) -> Result<Vec<u8>, LedgerError> {
    let encoded = serde_json::to_vec(value)
        .map_err(|_| LedgerError::InvalidInput("ownership JSON serialization failed"))?;
    Ok(canonicalize_json(&encoded)?)
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
