# 0006. OTA tooling: Mender

**Status:** Accepted

**Date:** 2026-09-29

## Context

Project spec Section 4b requires A/B partition OTA with automatic
rollback on failed health checks. Hand-rolling partition-swap and
bootloader-integration logic is real, substantial embedded-Linux systems
work, and reinventing it is exactly the kind of undifferentiated
infrastructure work worth avoiding (same reasoning as choosing AWS IoT
Core over hand-rolled device management).

## Options considered

- **Mender** — open-source, purpose-built for exactly this (A/B
  partitions, automatic rollback, staged rollout), has an official QEMU
  virtual-device demo for testing the full OTA flow without physical
  hardware — genuinely useful for this project's SIL-first approach.
- **balena** — similar goal, built around balenaCloud as the fleet
  management layer; strong tooling but pulls the project toward
  balena's own cloud platform rather than the AWS IoT Core path already
  chosen in ADR 0005 for device/fleet management.
- **Hand-rolled A/B script** — full control, but reimplements a solved,
  genuinely hard problem (bootloader state, atomic partition switching,
  crash-safe rollback) — not a good use of project time.

## Decision

Use Mender. Its standalone/QEMU demo device lets the OTA flow be tested
the same SIL-first way the zone controller and connectivity pieces were
— proven before physical hardware exists — and it doesn't couple device
management to a second cloud platform alongside AWS IoT Core.

## Consequences

- Gains: real, battle-tested A/B/rollback logic; a genuine no-hardware
  testing path via Mender's QEMU demo; stays aligned with the AWS IoT
  Core direction already chosen for fleet management.
- Gives up: balena's more polished, unified fleet dashboard UI — a real
  usability trade, not a technical one.
- Note: unlike the FastAPI services built so far, this component is
  fundamentally an OS/device-integration concern, not application code
  — "building" it means configuring and integrating an existing agent,
  not writing an equivalent from scratch. Documented honestly in the
  ota-agent service's README rather than presented as hand-written logic.