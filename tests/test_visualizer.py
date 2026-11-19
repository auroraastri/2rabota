import os
import sys
import unittest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)
from visualizer import build_graph, get_test_deps


class TestVisualizer(unittest.TestCase):

    def test_get_test_deps_success(self):
        deps = get_test_deps("test_repo.json", "A")
        self.assertIn("B", deps)
        self.assertIn("E", deps)

    def test_cycle_handling(self):
        graph, load_order = build_graph(
            pkg="A",
            ver="1.0",
            url="test_repo.json",
            is_test=True,
            max_d=3,
        )
        self.assertIn("A", graph)
        self.assertEqual(load_order.count("A"), 1)

    def test_depth_limit(self):
        graph, _ = build_graph(
            pkg="A",
            ver="1.0",
            url="test_repo.json",
            is_test=True,
            max_d=0,
        )
        self.assertEqual(graph["A"], {})


if __name__ == "__main__":
    unittest.main()