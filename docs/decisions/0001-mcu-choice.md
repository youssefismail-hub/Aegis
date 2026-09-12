# 0001. Zone Controller MCU: STM32G431KB (Nucleo-G431KB) over NXP S32K144EVB

**Status:** Accepted

**Date:** 2026-09-12

## Context

The zone controller needs a real-time MCU with a CAN peripheral capable of
reading standard OBD-II PIDs from a vehicle. Candidates were evaluated
against: automotive relevance, CAN capability, cost, and realistic
sourcing/shipping to Tunisia (international distributors add customs
delay and cost that a hobbyist/solo budget can't always absorb).

## Options considered

- **NXP S32K144EVB-Q100** — AEC-Q100 automotive-qualified, native CAN-FD.
  The most "correct" automotive choice on paper, but expensive and slow
  to source reliably from Tunisia via Mouser/DigiKey, and requires a
  separate debugger in some configurations.
- **STM32G431KB (Nucleo-G431KB)** — STM32G4 family has genuine
  AEC-Q100-qualified automotive variants, real FDCAN peripheral, built-in
  ST-LINK debugger (no separate programmer needed), ~$10-13, reliably
  available via AliExpress/Mouser.
- **ESP32** — cheapest, easiest to source, native TWAI (CAN) controller,
  but not automotive-qualified silicon at all, and the project already
  has WiFi/BLE connectivity handled separately on the HPC node, so
  ESP32's main advantage (built-in wireless) isn't needed on this board.

## Decision

Use the STM32G431KB via a Nucleo-G431KB dev board for the zone controller.

## Consequences

- Gains: real sourcing reliability, built-in debugger, retains CAN-FD
  capability, automotive-qualified silicon exists in the same MCU family
  (useful to cite even though the dev board itself isn't automotive-rated).
- Gives up: the NXP S32K's slightly stronger "pure" automotive pedigree in
  documentation/marketing terms — not a functional loss for this project's
  scope, since OBD-II's legislated diagnostic bus is classic CAN 500kbps
  regardless of MCU CAN-FD capability.
- Revisit if: a future phase needs to read manufacturer-specific CAN-FD
  buses beyond standard OBD-II PIDs, or needs certified automotive-grade
  hardware for reasons beyond prototyping (e.g. actual vehicle
  certification), at which point re-evaluate NXP S32K or an automotive
  STM32G4 production variant (not the Nucleo dev board).