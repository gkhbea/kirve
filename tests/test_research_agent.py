"""
Unit tests for Research Agent (Web Automation, Price Collection, Cart, and Guarded Checkout)
"""
import unittest
from kirve.tools.research_agent import ResearchAgent
from kirve.tools.security import SecurityAgent

class TestResearchAgent(unittest.TestCase):
    def test_search_web(self):
        agent = ResearchAgent(headless=True)
        res = agent.search_web("Roborock Q8 Max")
        self.assertTrue(res["success"])
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("title", res["results"][0])

    def test_collect_prices(self):
        agent = ResearchAgent(headless=True)
        res = agent.collect_prices("Roborock Q8 Max")

        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["total_offers"], 3)
        self.assertIn("cheapest_offer", res)
        self.assertIn("average_price", res)
        self.assertLessEqual(res["cheapest_offer"]["price"], res["average_price"])

    def test_cart_management(self):
        agent = ResearchAgent(headless=True)
        # Empty cart check
        cart = agent.get_cart()
        self.assertEqual(cart["total_items"], 0)
        self.assertEqual(cart["total_amount"], 0.0)

        # Add item
        item = {"product_name": "Roborock Q8 Max", "price": 18500.0, "platform": "Amazon TR"}
        add_res = agent.add_to_cart(item, quantity=1)
        self.assertTrue(add_res["success"])

        # Check cart
        cart = agent.get_cart()
        self.assertEqual(cart["total_items"], 1)
        self.assertEqual(cart["total_amount"], 18500.0)

        # Clear cart
        clear_res = agent.clear_cart()
        self.assertTrue(clear_res["success"])
        self.assertEqual(agent.get_cart()["total_items"], 0)

    def test_checkout_rejected_by_patron(self):
        # Security agent rejects payment ('H')
        sec_agent = SecurityAgent(input_provider=lambda p: "h")
        agent = ResearchAgent(security_agent=sec_agent, headless=True)

        agent.add_to_cart({"product_name": "Togg Aksesuar", "price": 1200.0}, quantity=2)

        res = agent.checkout()
        self.assertFalse(res["success"])
        self.assertTrue(res.get("aborted", False))
        # Cart must still be intact
        self.assertEqual(agent.get_cart()["total_items"], 2)

    def test_checkout_approved_by_patron(self):
        # Security agent approves payment ('E')
        sec_agent = SecurityAgent(input_provider=lambda p: "e")
        agent = ResearchAgent(security_agent=sec_agent, headless=True)

        agent.add_to_cart({"product_name": "Togg Aksesuar", "price": 1200.0}, quantity=1)

        res = agent.checkout()
        self.assertTrue(res["success"])
        self.assertTrue(res.get("approved_by_patron", False))
        self.assertIn("order_id", res)
        self.assertEqual(res["paid_amount"], 1200.0)
        # Cart must be cleared after successful checkout
        self.assertEqual(agent.get_cart()["total_items"], 0)

    def test_checkout_empty_cart(self):
        agent = ResearchAgent(headless=True)
        res = agent.checkout()
        self.assertFalse(res["success"])
        self.assertIn("boş", res.get("error", "").lower())

    def test_extract_product_name(self):
        text = "1 kg luk nutella en ucuz nerede arastır"
        product = ResearchAgent.extract_product_name(text)
        self.assertEqual(product, "1 kg nutella")

    def test_find_cheapest_and_open_browser(self):
        from unittest.mock import patch
        agent = ResearchAgent(headless=True)
        with patch("webbrowser.open", return_value=True) as mock_open:
            res = agent.find_cheapest_and_open_browser("1 kg luk nutella en ucuz nerede arastır")
            self.assertTrue(res["success"])
            self.assertEqual(res["product"], "1 kg nutella")
            self.assertIn("akakce.com/arama/?q=1+kg+nutella", res["url"])
            mock_open.assert_called_once()

if __name__ == "__main__":
    unittest.main()
