"""Tests for placing JSON in an analyzer's kb/user directory.

``put_json_file`` / ``put_json_object`` drop JSON into ``<analyzer>/kb/user``
so the analyzer's ``json2kbb`` python pass can convert it to a ``.kbb``. These
tests only exercise the file placement (no engine ``analyze`` run), so they do
not hit the engine-teardown segfault the main suite is skipped for.
"""

import json
import tempfile
import unittest
from pathlib import Path

try:
    import NLPPlus
    HAVE_NLPPLUS = True
except Exception:  # native binding not built in this environment
    HAVE_NLPPLUS = False

ANALYZER = "emailaddress"  # a bundled library analyzer


@unittest.skipUnless(HAVE_NLPPLUS, "NLPPlus native binding not built")
class TestPutJson(unittest.TestCase):
    def setUp(self):
        self.wf = tempfile.mkdtemp(prefix="nlpjson-")
        NLPPlus.set_working_folder(self.wf, initialize=True)
        self.kbuser = Path(self.wf) / "analyzers" / ANALYZER / "kb" / "user"

    def test_put_json_object(self):
        dest = NLPPlus.put_json_object(ANALYZER, {"company": {"name": "Acme"}}, "company")
        self.assertEqual(Path(dest), self.kbuser / "company.json")
        self.assertTrue(Path(dest).is_file())
        self.assertEqual(json.loads(Path(dest).read_text(encoding="utf-8")),
                         {"company": {"name": "Acme"}})

    def test_put_json_object_appends_extension(self):
        dest = NLPPlus.put_json_object(ANALYZER, [1, 2, 3], "nums")
        self.assertEqual(Path(dest).name, "nums.json")

    def test_put_json_file_default_name(self):
        src = Path(self.wf) / "src.json"
        src.write_text('{"x": [1, 2]}', encoding="utf-8")
        dest = NLPPlus.put_json_file(ANALYZER, src)
        self.assertEqual(Path(dest), self.kbuser / "src.json")
        self.assertEqual(json.loads(Path(dest).read_text(encoding="utf-8")),
                         {"x": [1, 2]})

    def test_put_json_file_named(self):
        src = Path(self.wf) / "src.json"
        src.write_text('{"x": 1}', encoding="utf-8")
        dest = NLPPlus.put_json_file(ANALYZER, src, "renamed")
        self.assertEqual(Path(dest).name, "renamed.json")

    def test_put_json_file_missing_raises(self):
        with self.assertRaises(NLPPlus.EngineException):
            NLPPlus.put_json_file(ANALYZER, Path(self.wf) / "does-not-exist.json")


if __name__ == "__main__":
    unittest.main()
