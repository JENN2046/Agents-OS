//! Strict RFC 8785 JCS encoding for the frozen integer-only M0-A domain.

use std::cmp::Ordering;

use super::types::{CanonicalError, CanonicalValue, parse_strict_json};

pub fn to_jcs_bytes(value: &CanonicalValue) -> Vec<u8> {
    let mut output = Vec::new();
    write_value(value, &mut output);
    output
}

pub fn canonicalize_json(input: &[u8]) -> Result<Vec<u8>, CanonicalError> {
    Ok(to_jcs_bytes(&parse_strict_json(input)?))
}

fn write_value(value: &CanonicalValue, output: &mut Vec<u8>) {
    match value {
        CanonicalValue::Null => output.extend_from_slice(b"null"),
        CanonicalValue::Bool(true) => output.extend_from_slice(b"true"),
        CanonicalValue::Bool(false) => output.extend_from_slice(b"false"),
        CanonicalValue::Integer(value) => output.extend_from_slice(value.to_string().as_bytes()),
        CanonicalValue::String(value) => write_string(value, output),
        CanonicalValue::Array(values) => {
            output.push(b'[');
            for (index, value) in values.iter().enumerate() {
                if index > 0 {
                    output.push(b',');
                }
                write_value(value, output);
            }
            output.push(b']');
        }
        CanonicalValue::Object(fields) => {
            let mut ordered: Vec<&(String, CanonicalValue)> = fields.iter().collect();
            ordered.sort_by(|left, right| compare_utf16(&left.0, &right.0));
            output.push(b'{');
            for (index, (key, value)) in ordered.into_iter().enumerate() {
                if index > 0 {
                    output.push(b',');
                }
                write_string(key, output);
                output.push(b':');
                write_value(value, output);
            }
            output.push(b'}');
        }
    }
}

fn compare_utf16(left: &str, right: &str) -> Ordering {
    left.encode_utf16().cmp(right.encode_utf16())
}

fn write_string(value: &str, output: &mut Vec<u8>) {
    output.push(b'"');
    for character in value.chars() {
        match character {
            '"' => output.extend_from_slice(br#"\""#),
            '\\' => output.extend_from_slice(br#"\\"#),
            '\u{0008}' => output.extend_from_slice(br"\b"),
            '\u{0009}' => output.extend_from_slice(br"\t"),
            '\u{000a}' => output.extend_from_slice(br"\n"),
            '\u{000c}' => output.extend_from_slice(br"\f"),
            '\u{000d}' => output.extend_from_slice(br"\r"),
            character if character <= '\u{001f}' => {
                let escaped = format!("\\u{:04x}", character as u32);
                output.extend_from_slice(escaped.as_bytes());
            }
            character => {
                let mut encoded = [0_u8; 4];
                output.extend_from_slice(character.encode_utf8(&mut encoded).as_bytes());
            }
        }
    }
    output.push(b'"');
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixed_canonical_vectors_match() {
        let vectors: &[(&[u8], &[u8])] = &[
            (
                br#"{"z":0,"a":[true,null,-7]}"#,
                br#"{"a":[true,null,-7],"z":0}"#,
            ),
            (
                br#"{"text":"line\n\u0001\\\""}"#,
                br#"{"text":"line\n\u0001\\\""}"#,
            ),
            ("{\"é\":\"雪\"}".as_bytes(), "{\"é\":\"雪\"}".as_bytes()),
            (
                br#"{"\ud83d\ude00":1,"\ufffd":2}"#,
                "{\"😀\":1,\"�\":2}".as_bytes(),
            ),
        ];
        for (input, expected) in vectors {
            assert_eq!(canonicalize_json(input).unwrap(), *expected);
        }
    }

    #[test]
    fn canonicalization_is_idempotent() {
        let first = canonicalize_json(br#"{"b":2,"a":1}"#).unwrap();
        let second = canonicalize_json(&first).unwrap();
        assert_eq!(first, second);
    }
}
