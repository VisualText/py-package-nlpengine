"""
Test the basic engine functionality.
"""

from unittest import TestCase, main
from pathlib import Path

import json
import logging

import NLPPlus

DATADIR = Path(__file__).parent / "data"

def read_file(path):
    with open(path, "rt") as infh:
        return infh.read()


class EngineTest(TestCase):
    """Test the NLPPlus library"""

    maxDiff = None

    def test_basic(self):
        """Run the "basic" analyzer and verify that it works."""

        output = NLPPlus.analyze("Hello world!", "basic")
        # This analyzer does not produce any output :)
        self.assertEqual(output, "")
        # Here's a better API!
        text = read_file(DATADIR / "basic" / "text.txt")
        results = NLPPlus.engine.analyze(text, "basic")
        self.assertEqual(results.output_text, "")
        final_tree = read_file(DATADIR / "basic" / "text.txt_log" / "final.tree")
        self.assertEqual(final_tree, results.final_tree)

    # FIXME: we have to do this to get them in separate tests, but
    # with pytest we could do a parameterized test case.
    def _run_analyzer(self, name):
        text = read_file(DATADIR / name / "text.txt")
        results = NLPPlus.engine.analyze(text, name)
        self.assertEqual(results.output_text, "")
        output = json.loads(
            read_file(DATADIR / name / "text.txt_log" / "output.json")
        )
        self.assertEqual(output, results.output)

    def test_address_parser(self):
        """Run the address parser and verify that it works."""
        self._run_analyzer("address-parser")

    def test_emailaddress_parser(self):
        """Run the emailaddress analyzer and verify that it works."""
        self._run_analyzer("emailaddress")

    def test_telephone_parser(self):
        """Run the telephone analyzer and verify that it works."""
        self._run_analyzer("telephone")

    def test_links_parser(self):
        """Run the links analyzer and verify that it works."""
        self._run_analyzer("links")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
