use agents_os_resident::canonical::jcs::canonicalize_json;
use agents_os_resident::napi_frame::{
    CommandBoundary, Disposition, MethodId, parse_request, request_bytes,
};
use agents_os_resident::reducers::command_intake::{COMMAND_TYPE_IDS, submission_value};
use agents_os_resident::resident::{ResidentKernel, ResidentKernelConfig, SyntheticOwnership};
use serde_json::json;

fn kernel(root: &std::path::Path) -> ResidentKernel {
    let ownership = SyntheticOwnership::genesis(
        "incarnation:SYNTHETIC_TEST:wp4-protocol",
        b"wp4-protocol-nonce",
    )
    .expect("ownership");
    let kernel =
        ResidentKernel::start(ResidentKernelConfig::synthetic(root, ownership)).expect("kernel");
    kernel.initialize_ledger_v1().expect("ledger v1");
    kernel
}

#[test]
fn illegal_frames_and_forged_principal_are_rejected_before_ledger_access() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let kernel = kernel(root.path());
    let boundary = CommandBoundary::synthetic(&kernel);
    let command_id = "command:SYNTHETIC_TEST:wp4-illegal";
    let valid_payload = submission_value(command_id, COMMAND_TYPE_IDS[0]).unwrap();
    let valid = request_bytes(MethodId::ExecuteCommand, command_id, valid_payload.clone()).unwrap();

    let mut unknown: serde_json::Value = serde_json::from_slice(&valid).unwrap();
    unknown["path"] = json!("/tmp/not-authority");
    let unknown = canonicalize_json(&serde_json::to_vec(&unknown).unwrap()).unwrap();
    assert!(boundary.invoke(MethodId::ExecuteCommand, &unknown).is_err());

    let noncanonical = String::from_utf8(valid.clone())
        .unwrap()
        .replacen('{', "{ ", 1);
    assert!(
        boundary
            .invoke(MethodId::ExecuteCommand, noncanonical.as_bytes())
            .is_err()
    );

    let mut forged_payload = valid_payload;
    forged_payload["canonical_command"]["claimed_principal_id"] =
        json!("principal:PRODUCTION:forged");
    let forged = request_bytes(MethodId::ExecuteCommand, command_id, forged_payload).unwrap();
    assert!(boundary.invoke(MethodId::ExecuteCommand, &forged).is_err());

    let wrong_method = request_bytes(MethodId::Reconcile, command_id, json!({})).unwrap();
    assert!(parse_request(&wrong_method, MethodId::ExecuteCommand).is_err());
    assert_eq!(kernel.ledger_counts().unwrap().inbox_commands, 0);
    assert_eq!(kernel.ledger_counts().unwrap().replay_rows, 0);
    kernel.shutdown().expect("shutdown");
}

#[test]
fn query_is_closed_and_reserved_methods_are_inert() {
    let root = tempfile::tempdir().expect("temporary synthetic root");
    let kernel = kernel(root.path());
    let boundary = CommandBoundary::synthetic(&kernel);
    let query = request_bytes(
        MethodId::ExecuteQuery,
        "query:SYNTHETIC_TEST:counts",
        json!({"environment":"SYNTHETIC_TEST","query_id":"LEDGER_COUNTS"}),
    )
    .unwrap();
    let response = boundary.invoke(MethodId::ExecuteQuery, &query).unwrap();
    assert_eq!(response.disposition, Disposition::QueryOk);
    assert_eq!(
        response.as_json_value().unwrap()["result"]["runtime_usable"],
        false
    );

    let before = kernel.ledger_counts().unwrap();
    for method in [
        MethodId::ClaimOutbox,
        MethodId::AcknowledgeOutbox,
        MethodId::Reconcile,
    ] {
        let request = request_bytes(method, "request:SYNTHETIC_TEST:reserved", json!({})).unwrap();
        let response = boundary.invoke(method, &request).unwrap();
        assert_eq!(response.disposition, Disposition::ContractNotActive);
    }
    assert_eq!(kernel.ledger_counts().unwrap(), before);
    kernel.shutdown().expect("shutdown");
}
