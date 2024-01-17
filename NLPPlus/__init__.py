"""
Python extension for NLP++ text analysis engine.

Basic usage with the `Engine` class:

    from NLPPlus import Engine
    e = Engine()
    xml = e.analyze("parse-en-us", "This is some text to be parsed")
    print(xml)
"""

import os

# NOTE: This definition must precede the import below
THISDIR = os.path.dirname(__file__)

from .bindings import Engine  # noqa: F401, E402
