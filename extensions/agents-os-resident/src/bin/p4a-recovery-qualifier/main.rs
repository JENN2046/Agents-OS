//! Validation-only, read-only bridge to the canonical P4-A recovery qualifier.
//! It has no recovery execution, checkpoint write, database, or grant surface.

mod logic;

use std::io::{self, Read};
use std::path::Path;

use logic::{RecoveryFixtureIdentity, classify_recovery_identities, qualify_recovery_fixture};
use serde::Deserialize;

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct FrozenFixturePair {
    live: RecoveryFixtureIdentity,
    recovery: RecoveryFixtureIdentity,
}

fn argument<'a>(arguments: &'a [String], name: &str) -> Result<&'a str, String> {
    let index = arguments
        .iter()
        .position(|value| value == name)
        .ok_or_else(|| format!("missing argument {name}"))?;
    arguments
        .get(index + 1)
        .map(String::as_str)
        .ok_or_else(|| format!("missing value for {name}"))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let arguments: Vec<String> = std::env::args().skip(1).collect();
    let qualification = if arguments.as_slice() == ["--classify-json"] {
        let mut input = String::new();
        io::stdin().read_to_string(&mut input)?;
        let fixtures: FrozenFixturePair = serde_json::from_str(&input)?;
        classify_recovery_identities(fixtures.live, fixtures.recovery)
    } else {
        let live = argument(&arguments, "--live")?;
        let recovery = argument(&arguments, "--recovery")?;
        if arguments.len() != 4 {
            return Err("expected exactly --live PATH --recovery PATH".into());
        }
        qualify_recovery_fixture(Path::new(live), Path::new(recovery))?
    };
    println!("{}", serde_json::to_string(&qualification)?);
    Ok(())
}
