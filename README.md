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

## Module Development

This module is built using
[scikit-build-core](https://scikit-build-core.readthedocs.io/en/latest/index.html)
and [nanobind](https://nanobind.readthedocs.io/en/latest/index.html).
To set up for development, make sure you have a C++ compiler that
works, and clone the source with:

    git clone --recursive-submodules https://github.com/VisualText/py-package-nlpengine.git

For development it is convenient to disable build isolation, so
install the necessary build dependencies.  We suggest doing this in a
virtual environment:

    cd py-package-nlpengine
    python -m venv venv
    . venv/bin/activate
    pip install -r requirements-dev.txt
    
On Linux, generally, you can simply install the ICU development
libraries system-wide:

    # On Ubuntu / Debian /etc
    sudo apt install libicu-dev
    # On CentOS / RHEL / etc
    sudo yum install libicu-devel
    
Now you can build the module as a "writable" install, which will allow
you to test changes as you make them:

    pip install --no-build-isolation -ve .

If you were not able to install ICU above (such as on MacOS), you have
to use vcpkg:

    git clone --depth 1 https://github.com/Microsoft/vcpkg.git
    ./vcpkg/bootstrap-vcpkg.sh
    pip install --no-build-isolation \
        -C cmake.args=-DCMAKE_TOOLCHAIN_FILE='./nlp-engine/vcpkg/scripts/buildsystems/vcpkg.cmake \
        -ve .
        
Additionally, on MacOS, you'll probably need a whole lot of other
things to use vcpkg:

    brew install autoconf-archive autoconf automake pkg-config

Verify that it works:

    python -m unittest discover -s tests

Note that you might get undefined C++ symbols if you are using Python
from miniconda on Linux.  In this case, please use the system Python
instead.
