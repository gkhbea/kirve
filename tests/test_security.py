"""
Unit tests for Security Agent (Mandatory Patron Confirmation Layer)
"""
import unittest
from kirve.tools.security import SecurityAgent

class TestSecurityAgent(unittest.TestCase):
    def test_request_confirmation_positive(self):
        # Test all valid approval responses
        for positive_input in ["e", "E", "evet", "EVET", "y", "yes"]:
            agent = SecurityAgent(input_provider=lambda prompt: positive_input)
            self.assertTrue(agent.request_confirmation("Kritik işlem"))

    def test_request_confirmation_negative(self):
        # Test negative or unexpected responses
        for negative_input in ["h", "H", "hayir", "HAYIR", "", "no", "iptal"]:
            agent = SecurityAgent(input_provider=lambda prompt: negative_input)
            self.assertFalse(agent.request_confirmation("Kritik işlem"))

    def test_guard_action_approved(self):
        executed = []
        def test_fn():
            executed.append("done")
            return {"status": "ok"}

        agent = SecurityAgent(input_provider=lambda prompt: "e")
        res = agent.guard_action("Test aksiyonu", test_fn)

        self.assertTrue(res["success"])
        self.assertTrue(res["approved_by_patron"])
        self.assertEqual(executed, ["done"])

    def test_guard_action_rejected(self):
        executed = []
        def test_fn():
            executed.append("should_not_run")
            return {"status": "ok"}

        agent = SecurityAgent(input_provider=lambda prompt: "h")
        res = agent.guard_action("Test aksiyonu", test_fn)

        self.assertFalse(res["success"])
        self.assertTrue(res.get("aborted", False))
        self.assertEqual(executed, [])  # Action was NOT executed

if __name__ == "__main__":
    unittest.main()
