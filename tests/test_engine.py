"""
Test the basic engine functionality.
"""

from unittest import TestCase, main
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

import json
import os
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
        tmpdir = TemporaryDirectory(prefix="test-nlpplus", ignore_cleanup_errors=True)
        copytree(DATADIR.parent / "analyzers", Path(tmpdir.name) / "analyzers")
        copytree(NLPPLUSDIR / "data", Path(tmpdir.name) / "data")
        # set_working_folder replaces the module's global engine. Leave a
        # default one afterwards, or every later test runs against this
        # folder, which has only the test analyzers.
        try:
            NLPPlus.set_working_folder(tmpdir.name)
            text = read_file(DATADIR / "basic" / "text.txt")
            results = NLPPlus.engine.analyze(text, "basic")
            self.assertEqual(results.output_text, "")
            final_tree = read_file(DATADIR / "basic" / "text.txt_log" / "final.tree")
            self.assertEqual(final_tree, results.final_tree)
        finally:
            NLPPlus.engine.close()
            NLPPlus.engine = NLPPlus.Engine()
            tmpdir.cleanup()


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

    def test_emailaddress_parser(self):
        """Run the emailaddress analyzer and verify that it works."""
        self._run_analyzer("emailaddress")

    def test_telephone_parser(self):
        """Run the telephone analyzer and verify that it works."""
        self._run_analyzer("telephone")

    def test_links_parser(self):
        """Run the links analyzer and verify that it works."""
        self._run_analyzer("links")


class DatumTest(TestCase):
    """analyze(datum=...) reaches the analyzer as G("$datum") (issue #1)."""

    def test_datum(self):
        with TemporaryDirectory(prefix="test-nlpplus", ignore_cleanup_errors=True) as tmp:
            copytree(DATADIR.parent / "analyzers", Path(tmp) / "analyzers")
            copytree(NLPPLUSDIR / "data", Path(tmp) / "data")
            try:
                NLPPlus.set_working_folder(tmp)
                analyze = NLPPlus.engine.analyze
                self.assertEqual(analyze("x", "datum", datum="json").output_text, "json")
                self.assertEqual(analyze("x", "datum", datum="xml").output_text, "xml")
                # Each call sets its own: none carries over from the last.
                self.assertEqual(analyze("x", "datum").output_text, "none")
            finally:
                NLPPlus.engine.close()
                NLPPlus.engine = NLPPlus.Engine()


class ReentrancyRegressionTest(TestCase):
    """nlp-engine #658 / #632 regression.

    Re-entrant ``analyze()`` across working folders must reuse the loaded
    analyzer instead of rebuilding and orphaning it, and switching working
    folders (which tears down the prior engine) must not segfault on teardown.

    Unlike the fixture-based suites above, these tests assert only that the
    calls succeed and -- critically -- that the process survives teardown.
    They deliberately do NOT compare against the output fixtures (which drift
    with the engine and are regenerated separately), so a clean run here is an
    unambiguous signal that the #632 SIGSEGV (exit 139) is gone.
    """

    def test_repeated_analyze_same_process(self):
        """Several analyze() calls in one process exercise the re-entrant
        addAna path that, pre-#658, logged 'Named analyzer already present'
        and orphaned a fresh NLP. Uses the bundled default analyzer."""
        for _ in range(3):
            xml = NLPPlus.analyze("Hello world!")
            self.assertTrue(xml)

    def test_working_dir_switch_teardown(self):
        """The #632 repro: switch to a temp working folder, analyze, then let
        TemporaryDirectory GC-clean it -- which tears down the prior engine.
        Pre-#658 this SIGSEGV'd during teardown; post-fix it exits cleanly."""
        with TemporaryDirectory(prefix="test-nlpplus") as tmp:
            copytree(DATADIR.parent / "analyzers", Path(tmp) / "analyzers")
            copytree(NLPPLUSDIR / "data", Path(tmp) / "data")
            try:
                NLPPlus.set_working_folder(tmp)
                text = read_file(DATADIR / "basic" / "text.txt")
                results = NLPPlus.engine.analyze(text, "basic")
                self.assertIsNotNone(results)
            finally:
                # Release the engine's open log files before the folder is
                # removed (Windows will not delete an open file), and leave
                # the module a default engine for the tests that follow.
                NLPPlus.engine.close()
                NLPPlus.engine = NLPPlus.Engine()


class AnalyzerFolderTest(TestCase):
    """Analyzers folder paths (#12) and clear_logs (#15).

    These use the module's engine and put its analyzers folder back after.
    A second Engine is not used: closing one engine in a process can break
    another that is still open (an engine bug, filed separately)."""

    def setUp(self):
        self.engine = NLPPlus.engine
        self.tmp = TemporaryDirectory(prefix="test-nlpplus", ignore_cleanup_errors=True)
        self.lib = Path(self.tmp.name) / "lib"

    def tearDown(self):
        self.engine.analyzer_path = None
        self.tmp.cleanup()

    def _make_lib(self):
        """An analyzers folder holding the test-only "basic" analyzer. The
        library analyzers keep knowledge base state between runs in one
        process, so running one here would change the results EngineTest
        expects from it."""
        copytree(DATADIR.parent / "analyzers" / "basic", self.lib / "basic")

    def test_folder_as_path(self):
        """A Path works as the analyzers folder, and every method agrees on
        where an analyzer is."""
        self._make_lib()
        self.engine.set_analyzers_folder(self.lib)
        self.assertEqual(self.engine.analyzer_dir("basic"),
                         self.lib.resolve() / "basic")
        results = self.engine.analyze(read_file(DATADIR / "basic" / "text.txt"), "basic")
        self.assertEqual(results.outdir, self.lib.resolve() / "basic" / "output")
        self.assertIsNotNone(results.final_tree)

    def test_relative_folder(self):
        """A relative folder is taken from the current directory when set."""
        self._make_lib()
        cwd = os.getcwd()
        try:
            os.chdir(self.tmp.name)
            self.engine.set_analyzers_folder("lib")
        finally:
            os.chdir(cwd)
        results = self.engine.analyze(read_file(DATADIR / "basic" / "text.txt"), "basic")
        self.assertIsNotNone(results.final_tree)

    def test_clear_logs(self):
        """clear_logs removes output, logs and input/*_log, nothing else."""
        self._make_lib()
        self.engine.set_analyzers_folder(self.lib)
        ana = self.engine.analyzer_dir("basic")
        for d in ("output", "logs", "input/a.txt_log", "input/sub/b.txt_log"):
            (ana / d).mkdir(parents=True, exist_ok=True)
            (ana / d / "x.log").write_text("x")
        (ana / "input" / "a.txt").write_text("keep me")
        self.assertEqual(self.engine.clear_logs("basic"), 4)
        for d in ("output", "logs", "input/a.txt_log", "input/sub/b.txt_log"):
            self.assertFalse((ana / d).exists(), d)
        self.assertTrue((ana / "input" / "a.txt").is_file())
        self.assertTrue((ana / "spec").is_dir())
        self.assertEqual(self.engine.clear_logs("basic"), 0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
