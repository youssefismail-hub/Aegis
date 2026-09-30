"""
Unit tests for the OTA state-machine simulation.
No external dependencies — stdlib unittest only.
"""

import unittest

from simulate_ota import default_state, deploy, boot_and_healthcheck


class TestOtaStateMachine(unittest.TestCase):
    def test_deploy_writes_to_inactive_slot_as_pending(self):
        state = default_state()
        state = deploy(state, "0.2.0")
        self.assertEqual(state["slot_b"]["version"], "0.2.0")
        self.assertEqual(state["slot_b"]["status"], "pending")
        # Active slot must be untouched by deploy alone.
        self.assertEqual(state["slot_a"]["status"], "active")
        self.assertEqual(state["active_slot"], "a")

    def test_successful_healthcheck_commits_new_slot(self):
        state = default_state()
        state = deploy(state, "0.2.0")
        result = boot_and_healthcheck(state, simulate_failure=False)

        self.assertTrue(result)
        self.assertEqual(state["active_slot"], "b")
        self.assertEqual(state["slot_b"]["status"], "active")
        self.assertEqual(state["slot_a"]["status"], "inactive")

    def test_failed_healthcheck_rolls_back_automatically(self):
        state = default_state()
        state = deploy(state, "0.2.0")
        result = boot_and_healthcheck(state, simulate_failure=True)

        self.assertFalse(result)
        # The device never actually switched — active_slot must be
        # unchanged, and the original version must still be the one
        # marked active. This is the core correctness property of the
        # whole OTA design: a bad update never becomes "active."
        self.assertEqual(state["active_slot"], "a")
        self.assertEqual(state["slot_a"]["status"], "active")
        self.assertEqual(state["slot_a"]["version"], "0.1.0")
        self.assertEqual(state["slot_b"]["status"], "failed")

    def test_boot_without_pending_deployment_raises(self):
        state = default_state()
        with self.assertRaises(ValueError):
            boot_and_healthcheck(state)

    def test_multiple_deploy_cycles_alternate_slots(self):
        """A second successful deploy should land on slot A again,
        proving the slot alternation logic works across cycles, not
        just on a single deploy."""
        state = default_state()
        deploy(state, "0.2.0")
        boot_and_healthcheck(state, simulate_failure=False)
        self.assertEqual(state["active_slot"], "b")

        deploy(state, "0.3.0")
        result = boot_and_healthcheck(state, simulate_failure=False)
        self.assertTrue(result)
        self.assertEqual(state["active_slot"], "a")
        self.assertEqual(state["slot_a"]["version"], "0.3.0")


if __name__ == "__main__":
    unittest.main()