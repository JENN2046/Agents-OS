//! Synthetic-only physical-boundary admission.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Admission {
    pub executable: bool,
    pub reason: &'static str,
}

pub fn synthetic_nonauthority() -> Admission {
    Admission {
        executable: false,
        reason: "SYNTHETIC_INPUT",
    }
}
