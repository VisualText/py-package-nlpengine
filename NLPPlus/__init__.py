"""Python extension for NLP++ text analysis engine.

On loading this module an analyzer is created with a working folder in
the current directory.  You may change this with `set_working_folder`.

Basic usage, assuming that you are running from a directory containing
`analyzers/parse-en-us`:

    import NLPPlus
    xml = NLPPlus.analyze("This is some text to be parsed")
    print(xml)

"""

import os
from .bindings import NLP_ENGINE

default_working_folder = os.getcwd()
current_working_folder = default_working_folder
engine = NLP_ENGINE(default_working_folder, silent=True)


def set_working_folder(working_folder: str = None):
    """Reinitialize the NLP++ engine with a different working folder.

    Args:

      working_folder(str): Working folder to use, or `None` to use the
                           current working directory.
    """
    global engine, current_working_folder
    if working_folder is None:
        working_folder = os.getcwd()
    if working_folder == current_working_folder:
        return
    current_working_folder = working_folder
    engine = NLP_ENGINE(working_folder, silent=True)


def analyze(str: str, parser: str = "parse-en-us"):
    """Run the analyzer named on the input string."""
    return engine.analyze(parser, str)
