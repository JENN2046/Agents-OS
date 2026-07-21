//! Phase 5B M0-B Home boundary.
//!
//! WP0 fixes the module layout only. The modules are synthetic-only and do
//! not yet decode Session observations, create candidates, form handoffs or
//! call the F3 command boundary.

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
