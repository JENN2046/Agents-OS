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
}
