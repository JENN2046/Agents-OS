//! Phase 5B M0-B Home boundary.
//!
//! WP0 fixed the module layout. WP1 adds only strict synthetic observation
//! decoding and zero-write nonpromotion decisions. WP2 derives immutable,
//! candidate-only F7 revisions without persistence. WP3 adds explicit observe,
//! discard, Memory Candidate and Intent Candidate gates. WP4 composes the
//! nonauthoritative F8 handoff from sealed owner commitments and canonical
//! history. WP5 adapts only the exact resulting candidate into the existing F3
//! `execute_command` frame; F3 alone authenticates, commits and replays it.

pub mod candidate;
pub mod handoff;
pub mod session_boundary;

pub const M0B_ENVIRONMENT: &str = "SYNTHETIC_TEST";
pub const M0B_RUNTIME_USABLE: bool = false;
pub const WP0_LAYOUT_ID: &str = "PHASE_5B_M0B_WP0_EXTENSION_SKELETON_V0_1";

pub fn module_ids() -> [&'static str; 3] {
    [
        session_boundary::MODULE_ID,
        candidate::MODULE_ID,
        handoff::MODULE_ID,
    ]
}
