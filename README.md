# AEGIS — Automotive Edge Gateway for Intelligent Systems

A software-defined-vehicle-inspired telematics device: real-time CAN reading
on a Zone Controller, software services (diagnostics, OTA, connectivity) on
an HPC compute node, and a cloud backend for fleet-style dashboards.

Architecture is deliberately split the way modern commercial-vehicle E/E
systems are moving — a narrow, deterministic real-time domain (Zone
Controller) separated from a software-centric domain (HPC node) that
carries the complexity and the update churn. See `docs/architecture.md`.

## Status

- [ ] Zone controller SIL (Software-in-the-Loop) stage
- [ ] Zone controller on real hardware (Nucleo-G431KB + TJA1051T/3)
- [ ] HPC node services (telemetry API, SOVD diagnostics API, OTA agent)
- [ ] Cloud backend (TimescaleDB schema, AWS IoT Core wiring)
- [ ] PCB design
- [ ] 3D enclosure
- [ ] Real-vehicle integration test

## Repository layout

\`\`\`
zone-controller-firmware/   Real-time CAN reading + PID/DTC decode logic
hpc-node/                   Containerized services: telemetry API, SOVD diagnostics, OTA agent
hardware/                   PCB schematics/layout (zone controller board, power stage)
enclosure/                  3D CAD files for the physical housing
cloud/                      Database schema + cloud infrastructure notes
dbc/                        CAN signal database (DBC format) — shared source of truth
docs/                       Architecture notes and Architecture Decision Records (ADRs)
scripts/                    Dev environment setup helpers
.github/workflows/          CI: automated build + test on every push
\`\`\`

## Getting started

Start with `zone-controller-firmware/README.md`.

## Design decisions

Significant technical decisions are recorded in `docs/decisions/` as
Architecture Decision Records (ADRs) — one file per decision, with the
context, the choice, and the trade-offs.