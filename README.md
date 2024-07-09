# NLPPlus

NLPPlus is the first 100% customizable NLP package for Python. NLPPlus
uses the [open-source NLP Engine](https://github.com/VisualText/nlp-engine).
Unlike other NLP packages which are black boxes, NLPPlus analyzers are
100% NLP++ code that can be modified. NLPPlus comes with four starter
analyzers: telephone numbers, links, emails, and a full English parser.

If for example, the telephone number analyzer is not working properly for your
application, you can use the [NLP++ VSCode extension](http://vscode.visualtect.org)
to edit and test the NLP++ code, and then use updated code instantly. Universities
around the world are starting to use NLP++ to write human digital readers for
[many different applications](https://nluglob.org/category/projects/).

## Learn More About NLP++

* [Lectures on NLP++ by NLP++ co-author David de Hilster](http://talks.visualtext.org)
* [YouTube tutorials on NLP++](http://tutorials.visualtext.org)
* [VisualText website](http://visualtext.org)
* [Natural Language Understanding Global Initiative website](http://nluglob.org)
 
## Requirements 

* Python 3.10 or newer

## Installation

### Future Installation (waiting for approval)

NLPPlus should eventually be installable from PyPI using pip, at which
point you can simply run:

    pip install nlpplus

### Installing By Downloading the Package (currently the only method)

For the moment, you can find the installable "wheel" files under each
release in the [Releases
page](https://github.com/VisualText/py-package-nlpengine/releases/).
Choose the correct version for your platform and Python version based
on the filename, for instance, wheels for Python 3.12 and MacOS will
have `cp312` and `macos` in the filename, for Windows you will find
`cp312` and `win`, and for Linux `linux`.  These files can be
installed with `pip` on the command line, for example:

    pip install nlpplus-0.1.2-cp310-cp310-win_amd64.whl

For the most recent version you can also download them from [the
GitHub actions
page](https://github.com/VisualText/py-package-nlpengine/actions/workflows/publish.yml?query=is%3Asuccess).
Click on the link at the top of the list of "workflow run results"
under "Build and upload to PyPI".  After scrolling to the bottom of
the page, you should see a section marked "Artifacts".  Click on the
appropriate link for your platform:

- For Linux: `cibw-wheels-linux`
- For MacOS 11 and later: `cibw-wheels-macos`
- For Windows 10 and later: `cibw-wheels-windows`

This will download a ZIP file containing installation files for each
supported version of Python on your platform.  The version number is
shown in the filename, for instance, for Python 3.10 on Windows you
will see a file with a name like
`nlpplus-0.1.dev1+g55d691d-cp310-cp310-win_amd64.whl` - the `cp310`
means Python 3.10.  For Python 3.12 it would be `cp312`, and so forth.
You can install this file with `pip`:

    pip install nlpplus-0.1.2-cp310-cp310-win_amd64.whl
    
For specific instructions on setting up Python on your platform please
consult the Python documentation.

If your platform is not supported you can also compile it from source,
which will require a working C++ compiler.  See the platform specific
instructions below for the requirements to build.

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
    results = NLPPlus.engine.analyze("Reach me at hello@example.com","emailaddress")
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
and `data`.  If you wish to initialize a new working folder with the
default analyzers and data, you can pass `initialize=True`:

    import NLPPlus
    NLPPlus.set_working_folder("somewhere/else", initialize=True)

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
    
### Linux Setup

On Linux, generally, you can simply install the ICU development
libraries system-wide:

    # On Ubuntu / Debian /etc
    sudo apt install libicu-dev
    # On CentOS / RHEL / etc
    sudo yum install libicu-devel
    
Now you can build the module as a "writable" install, which will allow
you to test changes as you make them:

    pip install --no-build-isolation -ve .

### MacOS and other Unix Setup

If you were not able to install ICU above (such as on MacOS), you have
to use vcpkg:

    git clone --depth 1 https://github.com/Microsoft/vcpkg.git
    ./vcpkg/bootstrap-vcpkg.sh

Additionally, on MacOS, you'll probably need a whole lot of other
things to use vcpkg:

    brew install autoconf-archive autoconf automake pkg-config

Now you can install with this somewhat more complicated command:

    pip install --no-build-isolation \
        -C cmake.args=-DCMAKE_TOOLCHAIN_FILE=./nlp-engine/vcpkg/scripts/buildsystems/vcpkg.cmake \
        -ve .

### Windows Setup

On Windows, everything is vastly more complicated for a number of
reasons:

- The ICU library on which NLP++ depends is built as DLLs, and these
  have to be included with the package
- Python won't load arbitrary DLLs from the current directory, unlike
  the rest of Windows (this is a good thing)
- Builds take 10x longer on Windows than on reasonable operating
  systems, so you will wait a long time to find out that the module
  you built actually doesn't work

For this reason "editable" installs (the `-e` option to `pip install`)
do not work on Windows and can't be expected to work.  Instead it is
necessary to build a wheel file and "repair" it with
[delvewheel](https://pypi.org/project/delvewheel/) to package the DLLs
correctly, then install that wheel.

If that sounds like too much trouble then just install from PyPI or
the wheel files [as described above](#Installation)

### Testing

Verify that it works:

    python -m unittest discover -s tests

Note that you might get undefined C++ symbols if you are using Python
from miniconda on Linux.  In this case, please use the system Python
instead.

## Making a release

For developer reference: the release process is managed using GitHub
actions.  To make a release from the `main` branch, make an
*annotated* tag (with `-m` and `-a`, this is important) of the form
`vX.Y` or `vX.Y.Z` (e.g. `v0.1.3`) and push the tag and the branch:

    git tag -m 'Release 0.1.3' -a v0.1.3
    git push --follow-tags
    
