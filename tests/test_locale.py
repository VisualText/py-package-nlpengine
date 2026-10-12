"""The engine must not depend on the caller's C locale.

The engine reads UTF-8 a byte at a time through <ctype.h>.  Under a
single-byte locale such as Windows code page 1252 (what Python sets on
Windows at startup), byte 0xA0 is a no-break space, so the continuation
byte 0xA0 in "à" (C3 A0) or "전" (EC A0 84) used to be taken for
whitespace: words were cut mid-character and the output was no longer
valid UTF-8.  The binding now runs the engine in the "C" locale.
"""

import locale
import unittest

try:
    import NLPPlus
    HAVE_NLPPLUS = True
except Exception:  # native binding not built in this environment
    HAVE_NLPPLUS = False

ANALYZER = "parse-en-us"  # first pass is dicttokz; phrasetext() runs clean_str
TEXT = "Voilà, the form. 오전 9시.\n"

# A locale in which isspace(0xA0) is true.
SINGLE_BYTE_LOCALES = [".1252", "English_United States.1252",
                       "en_US.ISO-8859-1", "en_US.ISO8859-1", "en_US"]


def set_single_byte_locale():
    for name in SINGLE_BYTE_LOCALES:
        try:
            locale.setlocale(locale.LC_CTYPE, name)
        except locale.Error:
            continue
        if "utf" not in locale.setlocale(locale.LC_CTYPE).lower():
            return True
    return False


@unittest.skipUnless(HAVE_NLPPLUS, "NLPPlus native binding not built")
class TestLocale(unittest.TestCase):
    def setUp(self):
        self.saved = locale.setlocale(locale.LC_CTYPE)
        if not set_single_byte_locale():
            locale.setlocale(locale.LC_CTYPE, self.saved)
            self.skipTest("no single-byte locale available")
        self.ctype = locale.setlocale(locale.LC_CTYPE)

    def tearDown(self):
        locale.setlocale(locale.LC_CTYPE, self.saved)

    def test_multibyte_words_survive_single_byte_locale(self):
        with NLPPlus.Engine() as engine:
            # Raised UnicodeDecodeError while the bug was present.
            results = engine.analyze(TEXT, ANALYZER)
            for path in results.outdir.iterdir():
                with self.subTest(file=path.name):
                    path.read_bytes().decode("utf-8")
            # One line per clause, its text passed through clean_str().
            clauses = (results.outdir / "clause.txt").read_text(encoding="utf-8")
        self.assertIn("Voilà, the form", clauses)
        self.assertIn("오전 9시", clauses)

    def test_caller_locale_restored(self):
        with NLPPlus.Engine() as engine:
            engine.analyze(TEXT, ANALYZER)
        self.assertEqual(locale.setlocale(locale.LC_CTYPE), self.ctype)


if __name__ == "__main__":
    unittest.main()
