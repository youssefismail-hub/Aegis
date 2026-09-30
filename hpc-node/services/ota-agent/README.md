# ota-agent

## What this actually is right now

This service does **not** perform real A/B partition swaps or bootloader
integration. That work is handled by **Mender** itself (ADR 0006) once
real hardware (Raspberry Pi CM4) exists — Mender manages the actual
partitions, U-Boot environment variables, and atomic swap/rollback at
the OS level, and reimplementing that here would be pointless duplicate
work of a solved problem.

What lives in this folder is a **state-machine simulation** — the same
deploy → boot → health-check → commit-or-rollback logic Mender
implements, modeled in a small Python script with a JSON state file
standing in for what would really be the bootloader's environment
variables. It proves the *logic* is correct (a failed health check
really does roll back, a passed one really does commit) without a real
partition, real bootloader, or real device. Same SIL-first approach as
the rest of this project — validate the logic before the hardware exists.

## Real integration plan (once Raspberry Pi CM4 hardware exists)

1. Flash the Raspberry Pi with a Mender-integrated Yocto or balena-style
   image (Mender provides reference builds for common boards).
2. Configure `mender-connect` and point it at either Mender's hosted
   Mender Cloud, or a self-hosted Mender server.
3. Package firmware/container updates as Mender Artifacts (`.mender`
   files) using `mender-artifact`.
4. Trigger deployments via the Mender server's API — bridged from AWS
   IoT Jobs per the project spec's fleet-rollout design (ADR 0005's
   local-first, AWS-IoT-Core-later pattern applies here too).
5. Mender's client on-device handles the actual A/B swap and automatic
   rollback on boot failure — the real equivalent of what
   `simulate_ota.py` below models in isolation.

## Files

- `simulate_ota.py` — the state-machine simulation described above
- `test_simulate_ota.py` — unit tests proving deploy/commit and
  deploy/rollback both work correctly