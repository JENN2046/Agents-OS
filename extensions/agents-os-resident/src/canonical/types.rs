//! Closed canonical JSON value types and strict decoding.

use std::collections::HashSet;
use std::fmt;

use serde::de::Error as _;
use serde::de::{self, DeserializeSeed, MapAccess, SeqAccess, Visitor};
use unicode_normalization::UnicodeNormalization;

/// Largest integer whose exact value is shared by JSON/JavaScript and Rust.
pub const MAX_SAFE_INTEGER: i64 = 9_007_199_254_740_991;
/// Smallest integer whose exact value is shared by JSON/JavaScript and Rust.
pub const MIN_SAFE_INTEGER: i64 = -MAX_SAFE_INTEGER;

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CanonicalValue {
    Null,
    Bool(bool),
    Integer(i64),
    String(String),
    Array(Vec<CanonicalValue>),
    Object(Vec<(String, CanonicalValue)>),
}

#[derive(Debug, thiserror::Error, Eq, PartialEq)]
pub enum CanonicalError {
    #[error("input is not valid UTF-8")]
    InvalidUtf8,
    #[error("invalid strict JSON: {0}")]
    InvalidJson(String),
    #[error("duplicate object key: {0}")]
    DuplicateKey(String),
    #[error("string is not Unicode NFC: {0}")]
    NonNfcString(String),
    #[error("floating-point JSON numbers are forbidden")]
    FloatForbidden,
    #[error("integer is outside the JSON safe-integer domain")]
    UnsafeInteger,
    #[error("expected {expected}, found {actual}")]
    WrongType {
        expected: &'static str,
        actual: &'static str,
    },
    #[error("closed object fields differ: missing={missing:?}, unknown={unknown:?}")]
    ClosedObjectFields {
        missing: Vec<String>,
        unknown: Vec<String>,
    },
    #[error("value is not in the closed enum")]
    UnknownEnum,
}

impl CanonicalValue {
    pub fn kind(&self) -> &'static str {
        match self {
            Self::Null => "null",
            Self::Bool(_) => "boolean",
            Self::Integer(_) => "integer",
            Self::String(_) => "string",
            Self::Array(_) => "array",
            Self::Object(_) => "object",
        }
    }

    pub fn as_object(&self) -> Result<&[(String, CanonicalValue)], CanonicalError> {
        match self {
            Self::Object(fields) => Ok(fields),
            other => Err(CanonicalError::WrongType {
                expected: "object",
                actual: other.kind(),
            }),
        }
    }

    pub fn require_exact_fields(&self, expected: &[&str]) -> Result<(), CanonicalError> {
        let fields = self.as_object()?;
        let actual: HashSet<&str> = fields.iter().map(|(key, _)| key.as_str()).collect();
        let wanted: HashSet<&str> = expected.iter().copied().collect();
        let mut missing: Vec<String> = wanted
            .difference(&actual)
            .map(|value| (*value).to_owned())
            .collect();
        let mut unknown: Vec<String> = actual
            .difference(&wanted)
            .map(|value| (*value).to_owned())
            .collect();
        missing.sort_by(|a, b| a.as_bytes().cmp(b.as_bytes()));
        unknown.sort_by(|a, b| a.as_bytes().cmp(b.as_bytes()));
        if missing.is_empty() && unknown.is_empty() {
            Ok(())
        } else {
            Err(CanonicalError::ClosedObjectFields { missing, unknown })
        }
    }

    pub fn require_enum(&self, allowed: &[&str]) -> Result<&str, CanonicalError> {
        let Self::String(value) = self else {
            return Err(CanonicalError::WrongType {
                expected: "string",
                actual: self.kind(),
            });
        };
        if allowed.contains(&value.as_str()) {
            Ok(value)
        } else {
            Err(CanonicalError::UnknownEnum)
        }
    }
}

fn is_nfc(value: &str) -> bool {
    value.nfc().eq(value.chars())
}

struct CanonicalValueSeed;

impl<'de> DeserializeSeed<'de> for CanonicalValueSeed {
    type Value = CanonicalValue;

    fn deserialize<D>(self, deserializer: D) -> Result<Self::Value, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_any(CanonicalVisitor)
    }
}

struct CanonicalVisitor;

impl<'de> Visitor<'de> for CanonicalVisitor {
    type Value = CanonicalValue;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("strict canonical JSON with safe integers only")
    }

    fn visit_unit<E>(self) -> Result<Self::Value, E> {
        Ok(CanonicalValue::Null)
    }

    fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E> {
        Ok(CanonicalValue::Bool(value))
    }

    fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        if (MIN_SAFE_INTEGER..=MAX_SAFE_INTEGER).contains(&value) {
            Ok(CanonicalValue::Integer(value))
        } else {
            Err(E::custom("integer is outside the JSON safe-integer domain"))
        }
    }

    fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        if value <= MAX_SAFE_INTEGER as u64 {
            Ok(CanonicalValue::Integer(value as i64))
        } else {
            Err(E::custom("integer is outside the JSON safe-integer domain"))
        }
    }

    fn visit_f64<E>(self, _value: f64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Err(E::custom("floating-point JSON numbers are forbidden"))
    }

    fn visit_str<E>(self, value: &str) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        if is_nfc(value) {
            Ok(CanonicalValue::String(value.to_owned()))
        } else {
            Err(E::custom(format!("string is not Unicode NFC: {value}")))
        }
    }

    fn visit_string<E>(self, value: String) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        self.visit_str(&value)
    }

    fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        let mut values = Vec::new();
        while let Some(value) = sequence.next_element_seed(CanonicalValueSeed)? {
            values.push(value);
        }
        Ok(CanonicalValue::Array(values))
    }

    fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        let mut seen = HashSet::new();
        let mut fields = Vec::new();
        while let Some(key) = map.next_key::<String>()? {
            if !is_nfc(&key) {
                return Err(A::Error::custom(format!(
                    "object key is not Unicode NFC: {key}"
                )));
            }
            if !seen.insert(key.clone()) {
                return Err(A::Error::custom(format!("duplicate object key: {key}")));
            }
            let value = map.next_value_seed(CanonicalValueSeed)?;
            fields.push((key, value));
        }
        Ok(CanonicalValue::Object(fields))
    }
}

pub fn parse_strict_json(input: &[u8]) -> Result<CanonicalValue, CanonicalError> {
    std::str::from_utf8(input).map_err(|_| CanonicalError::InvalidUtf8)?;
    let mut deserializer = serde_json::Deserializer::from_slice(input);
    let value = CanonicalValueSeed
        .deserialize(&mut deserializer)
        .map_err(|error| classify_json_error(&error.to_string()))?;
    deserializer
        .end()
        .map_err(|error| CanonicalError::InvalidJson(error.to_string()))?;
    Ok(value)
}

fn classify_json_error(message: &str) -> CanonicalError {
    if let Some(value) = message.strip_prefix("duplicate object key: ") {
        CanonicalError::DuplicateKey(value.split(" at line").next().unwrap_or(value).to_owned())
    } else if message.starts_with("floating-point JSON numbers are forbidden") {
        CanonicalError::FloatForbidden
    } else if message.starts_with("integer is outside the JSON safe-integer domain") {
        CanonicalError::UnsafeInteger
    } else if let Some(value) = message.strip_prefix("string is not Unicode NFC: ") {
        CanonicalError::NonNfcString(value.split(" at line").next().unwrap_or(value).to_owned())
    } else if let Some(value) = message.strip_prefix("object key is not Unicode NFC: ") {
        CanonicalError::NonNfcString(value.split(" at line").next().unwrap_or(value).to_owned())
    } else {
        CanonicalError::InvalidJson(message.to_owned())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_duplicate_keys() {
        assert!(matches!(
            parse_strict_json(br#"{"a":1,"a":2}"#),
            Err(CanonicalError::DuplicateKey(key)) if key == "a"
        ));
    }

    #[test]
    fn rejects_float_and_unsafe_integer_domains() {
        for input in [
            b"1.0".as_slice(),
            b"1e0".as_slice(),
            b"9007199254740992".as_slice(),
            b"-9007199254740992".as_slice(),
        ] {
            assert!(parse_strict_json(input).is_err(), "{input:?}");
        }
    }

    #[test]
    fn rejects_non_nfc_keys_and_values() {
        assert!(matches!(
            parse_strict_json("{\"é\":\"e\\u0301\"}".as_bytes()),
            Err(CanonicalError::NonNfcString(_))
        ));
        assert!(matches!(
            parse_strict_json("{\"e\\u0301\":true}".as_bytes()),
            Err(CanonicalError::NonNfcString(_))
        ));
    }

    #[test]
    fn closed_fields_enum_types_and_nullability_fail_closed() {
        let value = parse_strict_json(br#"{"kind":"KNOWN","value":null}"#).unwrap();
        value.require_exact_fields(&["kind", "value"]).unwrap();
        let fields = value.as_object().unwrap();
        fields[0].1.require_enum(&["KNOWN"]).unwrap();
        assert!(value.require_exact_fields(&["kind"]).is_err());
        assert!(fields[1].1.require_enum(&["KNOWN"]).is_err());
        assert!(fields[0].1.require_enum(&["OTHER"]).is_err());
    }
}
