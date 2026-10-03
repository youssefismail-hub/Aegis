# 0007. Secure boot: HMAC-SHA256 simulation now, secure-element-backed later

**Status:** Accepted

**Date:** 2026-10-03

## Context

docs/architecture.md's trust-boundary section names an authenticated
zone-controller <-> HPC-node link as planned but not yet built — real
hardware doesn't exist yet. The underlying mechanism (a secure element
verifying a signature before trusting firmware/a message) can be proven
in software first, same SIL-first approach as the rest of this project.

## Options considered

- **mbedTLS** — the real target library (lightweight, designed for
  embedded/MCU use, what would actually run on the STM32G431KB). Setting
  it up as a standalone library in this Linux dev environment adds
  nontrivial build complexity for a stage that's explicitly about
  proving logic, not final firmware.
- **OpenSSL (via libssl-dev)** — not what the final MCU firmware will
  use (too heavy for a microcontroller), but ships readily on Linux,
  well documented, and the *verification logic being tested* (hash,
  compare, accept/reject) is identical in shape to what mbedTLS would
  do — it's the same cryptographic pattern, different library.
- **HMAC-SHA256 (symmetric) vs. ECDSA (asymmetric)** — real secure
  elements (ATECC608A/SE050) commonly support both. HMAC chosen for
  this simulation stage specifically because it needs no key
  generation/certificate infrastructure to demonstrate the core
  accept/reject logic — asymmetric signing is the more realistic
  final choice (the HPC node shouldn't hold the same secret used to
  sign firmware) and is named here as the real follow-up.

## Decision

Simulate secure-boot verification using OpenSSL's HMAC-SHA256 in C,
in zone-controller-firmware, proving the core logic: a tampered or
unsigned image is correctly rejected, a correctly-signed one is
correctly accepted. Explicitly not the final mechanism — real
implementation moves to mbedTLS + secure-element-backed ECDSA once
hardware exists.

## Consequences

- Gains: proves the accept/reject logic correctly now, in the same
  language (C) the real firmware will use, without hardware or a heavy
  embedded crypto library setup.
- Gives up: doesn't exercise mbedTLS's actual API, and HMAC's symmetric
  key model is weaker than ECDSA's asymmetric model for this use case
  (whoever can verify can also forge, with HMAC — not true of ECDSA).
  Both are named limitations, not oversights.
- Revisit: when real hardware exists and the actual zone-controller <->
  HPC link gets built — that's the point this ADR's "later" actually
  happens.