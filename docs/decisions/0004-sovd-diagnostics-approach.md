# 0004. Diagnostics API: SOVD-style REST alongside raw UDS

**Status:** Accepted

**Date:** 2026-09-22

## Context

Traditional vehicle diagnostics use UDS (ISO 14229) — a CAN request/
response protocol requiring a proprietary tool to interpret. The
industry (per ACTIA's software-defined-trucks material, referenced
during this project's design phase) is moving toward SOVD
(Service-Oriented Vehicle Diagnostics): exposing diagnostics as a
standard REST/HTTP service, so any client — browser, fleet backend,
workshop tool — can query vehicle state the same way it queries any
other web API.

## Options considered

- **Raw UDS only** — matches how most real vehicles work today, but
  requires a proprietary/specialized client to interpret, and doesn't
  demonstrate the direction the industry is actually moving.
- **SOVD-style REST only, no UDS awareness at all** — simpler to build,
  but loses the "this maps to a real underlying protocol" grounding —
  the REST layer would be arbitrary rather than a genuine abstraction
  over something real.
- **SOVD-style REST as a service on the HPC node, sitting in front of
  UDS/Mode 03 DTC data already decoded by the zone controller** — the
  REST layer is a real abstraction over genuine vehicle protocol data,
  not just an arbitrary API shape.

## Decision

Implement a SOVD-inspired REST API (sovd-api service) on the HPC node,
sitting in front of data the zone controller already decodes via
standard OBD-II Mode 01/03. It is explicitly a *simplified, inspired-by*
implementation, not a full SOVD-standard-compliant implementation (the
real standard is far larger in scope) — stated plainly here and in the
service's README.

## Consequences

- Gains: a second, independent, genuinely differentiating API surface
  for the CV/portfolio narrative — almost no student project implements
  diagnostics this way. Demonstrates awareness of current automotive
  industry direction, not just legacy practice.
- Gives up: full SOVD standard compliance — acceptable, since the goal
  is demonstrating the architectural pattern, not shipping a
  certified-compliant diagnostics tool.
- Revisit if: the project ever needs interop with a real SOVD-compliant
  tool/client, at which point the full specification would need to be
  reviewed properly rather than worked from a simplified understanding.