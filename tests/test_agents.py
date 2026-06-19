import unittest
from src.Core.state import AgentState
from src.Tools.tools import extract_base_domain

class TestAgentPipeline(unittest.TestCase):
    def test_state_subscriptable(self):
        state = AgentState(input="google.com", run_id="test-123")
        
        # Test bracket get
        self.assertEqual(state["input"], "google.com")
        self.assertEqual(state["run_id"], "test-123")
        
        # Test bracket set
        state["errors"] = 5
        self.assertEqual(state.errors, 5)
        self.assertEqual(state["errors"], 5)
        
        # Test in operator
        self.assertTrue("input" in state)
        
        # Test get method
        self.assertEqual(state.get("model", "default"), "fast")
        self.assertEqual(state.get("nonexistent", "default"), "default")

    def test_extract_base_domain(self):
        self.assertEqual(extract_base_domain("https://www.geeksforgeeks.org/data-science/"), "geeksforgeeks.org")
        self.assertEqual(extract_base_domain("http://api.example.co.uk/test"), "example.co.uk")
        self.assertEqual(extract_base_domain("http://localhost:8000/"), "localhost")
        self.assertEqual(extract_base_domain("geeksforgeeks.org"), "geeksforgeeks.org")

if __name__ == "__main__":
    unittest.main()
