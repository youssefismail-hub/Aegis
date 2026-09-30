"""
OTA state-machine simulation.

Models deploy -> boot -> health-check -> commit-or-rollback, the same
logic Mender implements for real A/B partition updates (see README.md
in this folder for what's real vs. simulated here — short version:
NONE of this touches a real partition or bootloader; it's a JSON file
standing in for what would really be bootloader environment variables).

State shape:
{
    "slot_a": {"version": "0.1.0", "status": "active" | "inactive" | "pending" | "failed"},
    "slot_b": {"version": None,    "status": "inactive"},
    "active_slot": "a"
}
"""

import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")


def default_state():
    """A fresh device: slot A active with an initial version, slot B empty."""
    return {
        "slot_a": {"version": "0.1.0", "status": "active"},
        "slot_b": {"version": None, "status": "inactive"},
        "active_slot": "a",
    }


def load_state(path=STATE_FILE):
    if not os.path.exists(path):
        return default_state()
    with open(path, "r") as f:
        return json.load(f)


def save_state(state, path=STATE_FILE):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def _inactive_slot_name(state):
    return "b" if state["active_slot"] == "a" else "a"


def deploy(state, version):
    """
    Writes a new version into the currently-inactive slot, marked
    'pending' — mirrors Mender writing a new Artifact to the passive
    partition without touching the active one.
    """
    target = _inactive_slot_name(state)
    state[f"slot_{target}"] = {"version": version, "status": "pending"}
    return state


def boot_and_healthcheck(state, simulate_failure=False):
    """
    Simulates rebooting into the pending slot and running a health
    check. On success: commits (pending -> active, old active ->
    inactive). On failure: rolls back automatically (pending -> failed,
    active_slot pointer never moves) — mirroring exactly what a real
    bootloader's automatic-rollback-on-boot-failure mechanism does.

    Returns True if committed, False if rolled back.
    """
    target = _inactive_slot_name(state)
    pending = state[f"slot_{target}"]

    if pending["status"] != "pending":
        raise ValueError(f"No pending deployment on slot {target} to boot into")

    if simulate_failure:
        pending["status"] = "failed"
        # active_slot is deliberately untouched — this IS the rollback.
        # The device never actually left the last-known-good slot.
        return False

    # Health check passed: commit.
    old_active = state["active_slot"]
    state[f"slot_{old_active}"]["status"] = "inactive"
    pending["status"] = "active"
    state["active_slot"] = target
    return True