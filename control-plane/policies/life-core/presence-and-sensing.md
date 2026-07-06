# Life Core Policy Module: Presence And Sensing

Policy ID: `life-core.presence-and-sensing.v0.1`
Status: `presence_formal_sensing_pending_patch`
Source anchor: `agents-os-life-core-v0.1.local-mirror.md` section 11
Local scope: presence governance, sensing levels, device/context visibility

## Core Boundary

- Presence is not monitoring.
- Accompaniment is not listening.
- Seeing is not recording.
- Memory must be chosen.

## Sensing Levels

- `S0`: no sensing.
- `S1`: Jenn active input only.
- `S2`: current conversation, app, or document.
- `S3`: current device context.
- `S4`: real-world environment summary.
- `S5`: continuous sensing.
- `S6`: high-sensitive sensing, default forbidden.

## Executable Rules

- Presence Permission is governance, not runtime implementation.
- S3, S4, and S5 need explicit authorization formats before use.
- S6 only allows Forbidden Capability Proposal Path.
- Third-party information defaults to downgrade or refusal.
- Consent, retention, witness mode, emergency-only gates, and cross-device
  migration rules must be explicit before implementation.

## Hard Denials

- Do not open continuous listening, continuous watching, or automatic real-life
  recording through this module.
- Do not treat phone, headphone, AR, or cross-device possibility as permission.

## Receipt Rule

Presence or sensing receipts must state level, consent basis, retention,
third-party handling, and whether implementation was only proposed or executed.
