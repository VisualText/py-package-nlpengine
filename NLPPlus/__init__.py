"""
Python extension for NLP++ text analysis engine.

Basic usage with the `Engine` class:

    import NLPPlus
    xml = NLPPlus.analyze("This is some text to be parsed", "parse-en-us")
    print(xml)
"""

import os
from .bindings import NLP_ENGINE  # noqa: F401, E402

default_working_folder = os.getcwd()
current_working_folder = None
engine = NLP_ENGINE(default_working_folder, silent=True)


def set_working_folder(working_folder=None):
    global engine, current_working_folder
    if working_folder == current_working_folder:
        return
    current_working_folder = working_folder
    if working_folder is None:
        engine = NLP_ENGINE(default_working_folder, silent=True)
    else:
        engine = NLP_ENGINE(working_folder, silent=True)


def analyze(str, parser="parse-en-us"):
    return engine.analyze(parser, str)
