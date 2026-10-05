import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from marketx import core


class MarketSplitTest(unittest.TestCase):
    def test_children_never_exceed_parent(self):
        state = core.new_state("o1", "buy", 10, 4, [(100, 4), (101, 6)])
        out = core.split(state, "r1", core.Counter())
        self.assertLessEqual(sum(qty for _, qty in out["children"]), 10)

    def test_split_reports_remaining(self):
        state = core.new_state("o2", "buy", 5, 5, [(100, 5)])
        out = core.split(state, "r2", core.Counter())
        self.assertIn("remaining", out)

    def test_settle_counts_fills(self):
        state = core.new_state("o3", "buy", 4, 4, [(100, 4)])
        state["children"] = [{"child_id": "c1", "price": 100, "qty": 4}]
        state["remaining"] = 0
        out = core.settle(state, "r3", [(100, 3)], core.Counter())
        self.assertEqual(out["filled"], 3)
        self.assertEqual(state["filled"]["c1"], 3)

    def test_settle_on_missing_price_fills_nothing(self):
        state = core.new_state("o4", "buy", 4, 4, [(100, 4)])
        state["children"] = [{"child_id": "c1", "price": 100, "qty": 4}]
        out = core.settle(state, "r4", [(999, 2)], core.Counter())
        self.assertEqual(out["filled"], 0)

    def test_new_state_starts_unallocated(self):
        state = core.new_state("o5", "sell", 7, 3, [(200, 7)])
        self.assertEqual(state["remaining"], 7)
        self.assertEqual(state["children"], [])


if __name__ == "__main__":
    unittest.main()
