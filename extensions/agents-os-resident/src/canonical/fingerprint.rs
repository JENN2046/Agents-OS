//! SHA-256 fingerprints over exact canonical bytes.

use sha2::{Digest, Sha256};

use super::jcs::canonicalize_json;
use super::types::CanonicalError;

pub fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut encoded = String::with_capacity(64);
    for byte in digest {
        use std::fmt::Write;
        write!(&mut encoded, "{byte:02x}").expect("writing to String cannot fail");
    }
    encoded
}

pub fn canonical_fingerprint(input: &[u8]) -> Result<String, CanonicalError> {
    Ok(sha256_hex(&canonicalize_json(input)?))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixed_sha256_vector_matches() {
        assert_eq!(
            sha256_hex(b"{}"),
            "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
        );
        assert_eq!(
            canonical_fingerprint(br#"{"b":2,"a":1}"#).unwrap(),
            "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
        );
    }

    #[test]
    fn frozen_f1_through_f6_domain_vectors_match() {
        let vectors: &[(&[u8], &str)] = &[
            (
                br#"["f1-canonical-json.v0.1",{"goal_id":"goal:SYNTHETIC_TEST:1","goal_spec_revision":1}]"#,
                "0f05beb3307e2effc07885ed81fd81203a1f5daf12a4a88679c5d0f6c3f7bb2f",
            ),
            (
                br#"["agents-os.actor-identity-revision.v0.1-r8",{"actor_id":"actor:SYNTHETIC_TEST:1","actor_identity_revision":1}]"#,
                "302ea4e2c9288c9425963e1220d8a6d6820e480192a1e3c30a4577f21a498e4b",
            ),
            (
                br#"["agents-os.resident-restore-lineage-claim-ref.v0.1-r4","witness:SYNTHETIC_TEST:1","decision:SYNTHETIC_TEST:1","lineage:SYNTHETIC_TEST:1"]"#,
                "54ed124f01170a13a7fcc149a57c3e40b19aa4b19dcace1e383ad59c3917a104",
            ),
            (
                br#"["agents-os.effect-scope-id.v0.1-r9","effect:SYNTHETIC_TEST:1","MOCK_ONLY"]"#,
                "96c185af2f7759010b0986731b4d5621edd898635bbd35a994e1a41929808854",
            ),
            (
                br#"["agents-os.f5-delivery-receipt-replay-payload.v0.1-r5",{"receipt_id":"receipt:SYNTHETIC_TEST:1","receipt_revision":1}]"#,
                "fbbf842077e09cc2b546f71cdec9920bcc4a422c1de35b8dc879f4fd876dd2b5",
            ),
            (
                br#"["agents-os.f6.validation-current-decision-r3-proof.v0.1",{"requirement_id":"requirement:SYNTHETIC_TEST:1","requirement_revision":1}]"#,
                "f92553b7062aeb50910bf5c1d7e62ca758f32deba0b26f12c7fdeadb770451e0",
            ),
        ];
        for (canonical_bytes, expected) in vectors {
            assert_eq!(canonical_fingerprint(canonical_bytes).unwrap(), *expected);
            assert_eq!(
                canonicalize_json(canonical_bytes).unwrap(),
                *canonical_bytes
            );
        }
    }
}
