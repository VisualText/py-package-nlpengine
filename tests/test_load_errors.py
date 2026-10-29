"""A failed analyzer load must raise, not return empty output.

The engine reports a missing analyzer, a KB that does not load, or a pass
that does not build only on its own stderr, which Python cannot capture
on Windows. analyze() and compile() used to return normally, so callers
had to guess a build failure from every output coming back empty.

Also covers two engine fixes the error relies on or sits next to: the
logs/ folder (and so make_ana.log) is written on Linux and macOS too, and
a .kbb file with CRLF line ends (a Windows checkout) loads on all of them.
"""

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import NLPPlus

NLPPLUSDIR = Path(NLPPlus.__file__).parent

SEQ = "tokenize\tnil\t# tok\nnlp\tmain\t# main\n"
GOOD = """@CODE
L("v") = findconcept(findroot(), "verbs");
L("o") = "verbs=" + conceptname(L("v"));
if (L("v"))
  L("o") = L("o") + " k=" + strval(down(L("v")), "k");
"result.txt" << L("o");
@@CODE
"""
BAD = '@CODE\nL("x") = ;\n@@CODE\n'


class LoadErrorTest(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory(prefix="test-nlpplus-",
                                      ignore_cleanup_errors=True)
        self.work = Path(self.tmp.name)
        (self.work / "analyzers").mkdir()
        shutil.copytree(NLPPLUSDIR / "data", self.work / "data")
        self.engine = NLPPlus.Engine(self.work)

    def tearDown(self):
        self.engine.close()
        self.tmp.cleanup()

    def make(self, name, main, eol="\n"):
        d = self.work / "analyzers" / name
        (d / "spec").mkdir(parents=True)
        (d / "kb" / "user").mkdir(parents=True)
        (d / "input").mkdir()
        (d / "spec" / "analyzer.seq").write_bytes(SEQ.encode())
        (d / "spec" / "main.nlp").write_bytes(main.encode())
        kbb = eol.join(["verbs", "  buy: k=v1"]) + eol
        (d / "kb" / "user" / "verbs.kbb").write_bytes(kbb.encode())
        return d

    def result(self, d):
        found = list(d.rglob("result.txt"))
        return found[0].read_text().strip() if found else None

    def test_syntax_error_raises_with_the_pass_error(self):
        self.make("broken", BAD)
        with self.assertRaises(NLPPlus.AnalyzerError) as cm:
            self.engine.analyze("Hello.", "broken")
        self.assertEqual(cm.exception.analyzer_name, "broken")
        self.assertIn("2 2 [Syntax error.]", str(cm.exception))
        self.assertNotIn("\x00", str(cm.exception))
        # Caught by code that handles ordinary errors.
        self.assertIsInstance(cm.exception, Exception)

    def test_the_engine_works_after_a_failed_load(self):
        self.make("broken", BAD)
        self.make("good", GOOD)
        with self.assertRaises(NLPPlus.AnalyzerError):
            self.engine.analyze("Hello.", "broken")
        self.engine.analyze("Hello.", "good")
        self.assertEqual(self.result(self.work / "analyzers" / "good"),
                         "verbs=verbs k=v1")
        # And a second try still fails rather than reusing a stale build.
        with self.assertRaises(NLPPlus.AnalyzerError):
            self.engine.analyze("Hello.", "broken")

    def test_missing_analyzer_raises(self):
        with self.assertRaises(NLPPlus.AnalyzerError):
            self.engine.analyze("Hello.", "no-such-analyzer")

    def test_compile_of_a_broken_analyzer_raises(self):
        self.make("broken", BAD)
        with self.assertRaises(NLPPlus.AnalyzerError):
            self.engine.compile("broken", analyzer_only=True)

    def test_logs_are_written(self):
        d = self.make("good", GOOD)
        self.engine.analyze("Hello.", "good")
        self.assertTrue((d / "logs" / "make_ana.log").is_file())

    def test_crlf_kbb_loads(self):
        d = self.make("crlf", GOOD, eol="\r\n")
        self.engine.analyze("Hello.", "crlf")
        self.assertEqual(self.result(d), "verbs=verbs k=v1")


if __name__ == "__main__":
    unittest.main()
