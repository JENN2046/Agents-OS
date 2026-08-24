//! Spoken/typed local-owner consent parsing and frozen challenge dictionary.

use std::fs::File;
use std::io::Read;

use unicode_normalization::UnicodeNormalization;

use crate::canonical::fingerprint::sha256_hex;

use super::LocalOwnerError;

const FIRST: [char; 32] = [
    '青', '松', '星', '云', '山', '月', '风', '雨', '雪', '竹', '梅', '兰', '海', '江', '湖', '泉',
    '晨', '暮', '春', '秋', '夏', '冬', '明', '静', '清', '远', '安', '宁', '初', '新', '玉', '金',
];
const SECOND: [char; 16] = [
    '舟', '林', '河', '桥', '灯', '石', '谷', '岸', '亭', '原', '野', '溪', '湾', '岭', '岚', '泉',
];

pub const DICTIONARY_SIZE: usize = FIRST.len() * SECOND.len();

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ConsentKind {
    Create,
    Change,
    Complete,
    Close,
}

impl ConsentKind {
    pub fn prefix(self) -> &'static str {
        match self {
            Self::Create => "确认创建",
            Self::Change => "确认变更",
            Self::Complete => "确认完成",
            Self::Close => "确认关闭",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Challenge {
    pub words: [String; 3],
}

impl Challenge {
    pub fn prompt(&self, kind: ConsentKind) -> String {
        format!(
            "{}，{}、{}、{}",
            kind.prefix(),
            self.words[0],
            self.words[1],
            self.words[2]
        )
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ConsentParse {
    Approve,
    Cancel,
    Reject,
}

pub fn dictionary_word(index: usize) -> Result<String, LocalOwnerError> {
    if index >= DICTIONARY_SIZE {
        return Err(LocalOwnerError::RandomnessUnavailable);
    }
    let first = FIRST[index / SECOND.len()];
    let second = SECOND[index % SECOND.len()];
    Ok(format!("{first}{second}"))
}

pub fn generate_challenge() -> Result<Challenge, LocalOwnerError> {
    let mut bytes = [0_u8; 12];
    File::open("/dev/urandom")
        .and_then(|mut file| file.read_exact(&mut bytes))
        .map_err(|_| LocalOwnerError::RandomnessUnavailable)?;
    challenge_from_bytes(bytes)
}

pub fn challenge_from_bytes(bytes: [u8; 12]) -> Result<Challenge, LocalOwnerError> {
    let mut indexes = [0_usize; 3];
    for (position, chunk) in bytes.chunks_exact(4).enumerate() {
        let value = u32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]) as usize;
        indexes[position] = value % DICTIONARY_SIZE;
    }
    if indexes[1] == indexes[0] {
        indexes[1] = (indexes[1] + 1) % DICTIONARY_SIZE;
    }
    while indexes[2] == indexes[0] || indexes[2] == indexes[1] {
        indexes[2] = (indexes[2] + 1) % DICTIONARY_SIZE;
    }
    Ok(Challenge {
        words: [
            dictionary_word(indexes[0])?,
            dictionary_word(indexes[1])?,
            dictionary_word(indexes[2])?,
        ],
    })
}

pub fn normalize_transcript(input: &str) -> String {
    input
        .nfc()
        .collect::<String>()
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

pub fn consent_commitment(input: &str) -> String {
    let normalized = normalize_transcript(input);
    sha256_hex(
        format!("agents-os.local-owner.consent-commitment.v1\0{normalized}").as_bytes(),
    )
}

pub fn parse_transcript(
    transcript: &str,
    kind: ConsentKind,
    challenge: &Challenge,
) -> ConsentParse {
    let normalized = normalize_transcript(transcript);
    if normalized == "取消本次操作" {
        return ConsentParse::Cancel;
    }
    if normalized.is_empty()
        || normalized
            .chars()
            .any(|value| "\"'“”‘’「」『』".contains(value))
        || ["不", "没", "否", "别", "取消"]
            .iter()
            .any(|value| normalized.contains(value))
    {
        return ConsentParse::Reject;
    }

    let mut without_terminal = normalized.as_str();
    if without_terminal
        .chars()
        .last()
        .is_some_and(|value| "。.!！?？".contains(value))
    {
        let terminal_index = without_terminal
            .char_indices()
            .last()
            .map(|value| value.0)
            .unwrap_or(0);
        without_terminal = &without_terminal[..terminal_index];
        if without_terminal
            .chars()
            .last()
            .is_some_and(|value| "。.!！?？".contains(value))
        {
            return ConsentParse::Reject;
        }
    }
    let Some(tokens) = split_fixed_tokens(without_terminal) else {
        return ConsentParse::Reject;
    };
    if tokens.len() == 4
        && tokens[0] == kind.prefix()
        && tokens[1] == challenge.words[0]
        && tokens[2] == challenge.words[1]
        && tokens[3] == challenge.words[2]
    {
        ConsentParse::Approve
    } else {
        ConsentParse::Reject
    }
}

fn split_fixed_tokens(input: &str) -> Option<Vec<String>> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    let mut chars = input.chars().peekable();
    while let Some(value) = chars.next() {
        if value.is_whitespace() {
            while chars.peek().is_some_and(|next| next.is_whitespace()) {
                chars.next();
            }
            if chars.peek().is_some_and(|next| [',', '，', '、'].contains(next)) {
                chars.next();
                if chars.peek().is_some_and(|next| [',', '，', '、'].contains(next)) {
                    return None;
                }
                while chars.peek().is_some_and(|next| next.is_whitespace()) {
                    chars.next();
                }
            }
            if current.is_empty() {
                return None;
            }
            tokens.push(std::mem::take(&mut current));
            continue;
        }
        if [',', '，', '、'].contains(&value) {
            if current.is_empty()
                || chars.peek().is_some_and(|next| [',', '，', '、'].contains(next))
            {
                return None;
            }
            while chars.peek().is_some_and(|next| next.is_whitespace()) {
                chars.next();
            }
            tokens.push(std::mem::take(&mut current));
            continue;
        }
        current.push(value);
    }
    if current.is_empty() {
        None
    } else {
        tokens.push(current);
        Some(tokens)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn example() -> Challenge {
        Challenge {
            words: ["青舟".to_owned(), "松林".to_owned(), "星河".to_owned()],
        }
    }

    #[test]
    fn dictionary_is_frozen_unique_and_large_enough() {
        let mut words = std::collections::BTreeSet::new();
        for index in 0..DICTIONARY_SIZE {
            words.insert(dictionary_word(index).unwrap());
        }
        assert_eq!(DICTIONARY_SIZE, 512);
        assert_eq!(words.len(), 512);
        assert!(words.contains("青舟"));
        assert!(words.contains("松林"));
        assert!(words.contains("星河"));
    }

    #[test]
    fn punctuation_and_whitespace_equivalents_are_exact() {
        let challenge = example();
        for transcript in [
            "确认创建，青舟、松林、星河",
            "  确认创建 青舟 松林 星河。 ",
            "确认创建,青舟,松林,星河!",
            "确认创建， 青舟、 松林、 星河！",
        ] {
            assert_eq!(
                parse_transcript(transcript, ConsentKind::Create, &challenge),
                ConsentParse::Approve
            );
        }
    }

    #[test]
    fn fuzzy_extra_negated_quoted_and_homophone_forms_fail() {
        let challenge = example();
        for transcript in [
            "我确认创建，青舟、松林、星河",
            "确认创建，青舟、松林、星河，请执行",
            "不确认创建，青舟、松林、星河",
            "“确认创建，青舟、松林、星河”",
            "确认创建，轻舟、松林、星河",
            "确认创建青舟松林星河",
            "确认创建，，青舟、松林、星河",
            "确认创建，青舟、、松林、星河",
            "确认创建，青舟、松林、星河！！",
        ] {
            assert_eq!(
                parse_transcript(transcript, ConsentKind::Create, &challenge),
                ConsentParse::Reject
            );
        }
    }
}
