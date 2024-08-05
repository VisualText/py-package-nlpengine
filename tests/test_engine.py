"""
Test the basic engine functionality.
"""

from unittest import TestCase, main
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

import json
import logging

import NLPPlus

DATADIR = Path(__file__).parent / "data"
NLPPLUSDIR = Path(__file__).parent.parent / "NLPPlus"


def read_file(path):
    with open(path, "rt") as infh:
        return infh.read()


class ModuleTest(TestCase):
    """Test the NLPPlus module"""

    maxDiff = None

    def test_simple(self):
        """Test the simplest possible usage with parse-en-us."""
        xml = NLPPlus.analyze("Hello world!")
        hello = read_file(DATADIR / "out.xml")
        self.assertEqual(xml, hello)

    def test_working_dir(self):
        """Test that set_working_folder works."""
        tmpdir = TemporaryDirectory(prefix="test-nlpplus")
        copytree(DATADIR.parent / "analyzers", Path(tmpdir.name) / "analyzers")
        copytree(NLPPLUSDIR / "data", Path(tmpdir.name) / "data")
        NLPPlus.set_working_folder(tmpdir.name)
        text = read_file(DATADIR / "basic" / "text.txt")
        results = NLPPlus.engine.analyze(text, "basic")
        self.assertEqual(results.output_text, "")
        final_tree = read_file(DATADIR / "basic" / "text.txt_log" / "final.tree")
        self.assertEqual(final_tree, results.final_tree)


class EngineTest(TestCase):
    """Test the NLPPlus Engine class"""

    maxDiff = None

    # FIXME: we have to do this to get them in separate tests, but
    # with pytest we could do a parameterized test case.
    def _run_analyzer(self, name):
        text = read_file(DATADIR / name / "text.txt")
        results = NLPPlus.engine.analyze(text, name)
        self.assertEqual(results.output_text, "")
        output = json.loads(read_file(DATADIR / name / "text.txt_log" / "output.json"))
        self.assertEqual(output, results.output)

    def test_address_parser(self):
        """Run the address parser and verify that it works."""
        self._run_analyzer("address-parser")

    # def test_emailaddress_parser(self):
    #     """Run the emailaddress analyzer and verify that it works."""
    #     self._run_analyzer("emailaddress")

    def test_telephone_parser(self):
        """Run the telephone analyzer and verify that it works."""
        self._run_analyzer("telephone")

    def test_links_parser(self):
        """Run the links analyzer and verify that it works."""
        self._run_analyzer("links")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
