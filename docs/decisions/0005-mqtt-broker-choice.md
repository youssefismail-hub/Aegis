# 0005. Local Mosquitto broker now, AWS IoT Core migration path later

**Status:** Accepted

**Date:** 2026-09-24

## Context

The connectivity service needs somewhere to publish telemetry and for a
consumer (eventually the cloud/rules engine) to receive it. Project spec
Section 4 names AWS IoT Core as the target for device registry, Device
Shadows, and IoT Jobs. Building directly against AWS from day one adds
account setup, cost management, and network dependency friction to every
local dev/test cycle.

## Options considered

- **Build directly against AWS IoT Core from the start** — matches the
  final target exactly, but every local test now depends on internet
  connectivity and a configured AWS account, slowing the dev loop for
  no benefit at this stage (no real device exists yet to justify cloud
  device management).
- **Local Mosquitto broker (Docker) now, migrate to AWS IoT Core later**
  — MQTT is MQTT; a well-structured publisher/subscriber using standard
  topics and QoS levels ports to AWS IoT Core's MQTT endpoint with
  connection-config changes, not application-logic changes. Fast local
  dev loop, no cloud dependency until there's a real reason to add one.

## Decision

Run Mosquitto locally via Docker for development. Structure the
connectivity service's MQTT client code so the only AWS-IoT-Core-specific
work later is: TLS certificate-based auth (vs. Mosquitto's open local
config) and the broker endpoint URL — topic structure and pub/sub logic
stay identical.

## Consequences

- Gains: fast, offline-capable local development; genuine portability to
  AWS IoT Core since both are standard MQTT.
- Gives up: not testing AWS-specific features (Device Shadows, IoT Jobs)
  until that migration actually happens — acceptable, since those are
  cloud-side features not exercised by the connectivity service's core
  pub/sub logic anyway.
- Revisit: when device fleet management (registry, Jobs, Shadows) is
  actually being built — that's the point this ADR's migration path gets
  exercised for real.