# NLPPlus

This is a Python package for the NLP++ engine. You can find detailed
documentation about nlp-engine at
https://github.com/VisualText/nlp-engine.

## Requirements 
* Python 3.8
* A C++ compiler

## Installation

We suggest you use a virtual environment to install NLPPlus:

    python -m venv nlpplus-venv
    . nlpplus-venv/bin/activate
    pip install .

## Using the Library

On importing the `NLPPlus` module, an NLP++ engine instance is created
with the current working directory as the working folder.  This
repository is set up already to be used as a working folder.  So, for
instance, you may run:

    import NLPPlus
    NLPPlus.analyze("My email adress is someone@example.com.",
                    "emailaddress")

This will run the `email` analyzer on the text provided.  Where the
output goes depends entirely on the NLP++ code in the analyzer, but in
this case you can find it in
`analyzers/emailaddress/output/output.json`.  Some other analyzers
will return XML code from the call to `analyze`.  For more information
please contact the author of the analyzer in question.

If you like, you can also copy the `analyzers` and `data` directories
to your preferred location, and set the working directory with the
`set_working_folder` function:

    from NLPPlus import set_working_folder, analyze
    set_working_folder("somewhere/else")
    analyze("some text", "my-parser")

It is expected that the working folder contains, at a minimum, the
directories `analyzers` and `data`.  Each directory inside `analyzers`
contains the directories `spec`, `input`, `kb`, `tmp`, `logs`, and
`output`.  The `tmp`, `logs`, and `output` directories, at a minimum,
need to be writable.
