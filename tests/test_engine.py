"""
Test the basic engine functionality.
"""

from unittest import TestCase, main
from pathlib import Path

import logging

import NLPPlus

DATADIR = Path(__file__).parent / "data"


class EngineTest(TestCase):
    """Test the NLPPlus library"""

    def test_basic(self):
        """Run the "basic" analyzer and verify that it creates some output."""

        output = NLPPlus.analyze("Hello world!", "basic")
        # This analyzer does not produce any output :)
        self.assertEqual(output, "")
        # Here's a better API ;-)
        results = NLPPlus.engine.analyze("Hello world!", "basic")
        with open(DATADIR / "basic" / "output" / "final.tree") as infh:
            final_tree = infh.read()
        self.assertEqual(results.final_tree, final_tree)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
