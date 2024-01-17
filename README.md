# NLPPlus

This is a Python package for the NLP++ engine. You can find detailed
documentation about nlp-engine at
https://github.com/VisualText/nlp-engine.

## Requirements 
* Python 3.8

## Installation

NLPPlus should be installable from PyPI using pip.  If your platform
is not supported you can also compile it from source, which will
require a working C++ compiler.

We suggest you use a virtual environment to install NLPPlus:

    python -m venv nlpplus-venv
    . nlpplus-venv/bin/activate
    pip install .

## Using the Library

Very basic usage, which runs the default parser for US English and
returns parsing results as xML:

    import NLPPlus
    xml = NLPPlus.analyze("Hello world.")

This may be less useful than using a domain-specific analyzer.
Several of these are included with the module:

- `address-parser`: Extract addresses from text
- `emailaddress`: Extract email addresses from text
- `links`: Extract hyperlinks from text
- `telephone`: Extract telephone numbers from text

In contrast to the default analyzer these do not return any text by
default.  You will have to use the extended API to get the parse tree
or JSON output from them:

    import NLPPlus
    results = NLPPlus.engine.analyze("Reach me at hello@example.com")
    parsed_address = results.output["email_address"][0]
    parse_tree = results.final_tree

## NLP++ Development

By default the `NLPPlus` module will create a temporary working
directory with the default parser and the small set of analyzers
mentioned above.  If you are developing NLP++ code, you can also point
it at an existing working folder using `set_working_folder`:

    import NLPPlus
    NLPPlus.set_working_folder("somewhere/else")

This working folder is expected to contain the directories `analyzers`
and `data`.
