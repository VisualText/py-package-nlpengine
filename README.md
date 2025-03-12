# NLPPlus

The NLPPlus Python Package is the package that allows for python scripts
to call text and NLP analyzers created using [NLP++](https://visualtext.org). The package uses
the C++ libraries for the [NLP Engine](https://github.com/VisualText/nlp-engine) making the calling more efficient than
using the [NLP++ python class](https://github.com/VisualText/python) that calls command line version of the NLP
Engine "nlp.exe".

The major advantage of NLPPlus over other NLP packages is that is 100%
rule-based and modifiable and allows for any non-linguistic programmer
to create text analyzers 100% taylored to their needs.

## Long-Term, Open-Source, Glass-Box Project

NLP++ allows any programmer to write text and NLP programs that can be
shared by everyone. It represents the first universal programming
language for text and NLP. [As the community grows](https://nluglob.org), the number of open-source
solutions including dictionaries, knowledge bases, and analyzers will
grow - all of which can be modified by any programmer using the [NLP++
Language Extension for VSCode](https://vscode.visualtext.org).

## READ FIRST

It is important to understand that the NLPPlus package for Python is very
different from ALL other NLP packages in a very important and practical way.

Current NLP python packages have the "intention" of being plug-and-play
systems that perform natural language tasks without modification. The
problem is that when these systems ultimately fail in critical situations,
coders are left with no real way to fix these systems and they are quickly
abandoned.

The problem is that most all of these packages rely on statistical methods
such as machine learning or neural networks, or in the simpler cases, they
rely on Regex. Statistical systems cannot logically be corrected and Regex
is extremely limited and unreadable and impossible to maintain or extend.
Plus, these systems offer little if any means to modify them even though
every NLP task is slightly different in important ways.

The NLPPlus Python Package is different from all other NLP Python packages.
All its analyzers are 100% human readable and modifiable code that allows
any non-NLP coder to become a NLP programmer using the NLP++ VSCode
Language Extension appropriately called "VisualText". The VisualText
extension allows for the visualization of any NLP process. Coders can "see"
the syntactic parse tree along each step of the process, see rule matches
directly in the text, and print out the knowledge base at any point in the
process. Plus, dictionaries and knowledge bases are human readable unlike
json files or databases.

NLPPlus comes with five starter analyzers: telephone numbers, links, emails,
addresses, and a full English parser. And because NLP++ is a glassbox, all
analyzers can easily be modified by any coder.

If for example, the telephone number analyzer is not working properly for your
application, you can use the [NLP++ VSCode extension](http://vscode.visualtext.org)
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

## <span style='color:orange'>Installation</span>

### Installation

NLPPlus can be installed using pip:

    pip install nlpplus

### Installing By Downloading the Package Manually

You can find the installable "wheel" files under each
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
    
For specific instructions on setting up Python on your platform please
consult the Python documentation.

If your platform is not supported you can also compile it from source,
which will require a working C++ compiler.  See the platform specific
instructions below for the requirements to build.

## <span style='color:green'>Why Use NLP++?</span>

There are many reasons to consider using NLP++. Whether it be to be
able to write Regex-like rule patterns, to having the ability to 
modify 100% of the NLP code, or to visualize the NLP analyzer in
an intunitive way, NLP++ should be in every coder and programmer's
toolkit.

To put it simply, NLP++ turns any coder or programmer into an NLP
engineer.

### 1000 Times Better than Regex

For matching patterns in text, NLP++ is a Regex killer. The rule
matching system in NLP++ is human readable and is performed by calling
rules in a sequence, making creating and debugging rule-based patterns
a breeze. Along with 

### 100% Modifiable

The main reason to use NLP++
it is to engineer an NLP system to a specific task. Most all extraction
or understanding tasks in NLP require specific processing that is never
included in "generic" systems. NLP++ allows for the creation or
modification of any NLP++ system.

It must be emphasized that what separates NLPPlus from all the other
NLP packages in Python is that fact that all parsers are 100% modifiable
using the VSCode NLP++ Language Extension. Other NLP packages use regex
patterns which are impossible to modify or use trained machine learning
or neural network systems which cannot be fixed when 

### VisualText Editor

Writing an NLP system from scratch is thought to be for only those in
computational linguistics. But VisualText, NLP++, and the conceptual
Grammar changes all that.

Taking full advantage of the familiar VSCode environment, the NLP++
language extension makes NLP a visual process and logical process that
is easy to understand.

## <span style='color:yellow;'>Usng the NLPPlus Python Package</span>

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

### NLPPlus Engine Functions

These are the current functions that come with the NLPPlus package.

#### set_analyzer_folder(analyzer_folder_path: str)
This is used to set the folder where your analyzers are located.

#### analyze(text: str, parser: str = "parse-en-us"): str
This calls one of the analyzers in the analyzer folder on the text.
If the analyzer folder was not set, it will use the library analyzers
that come with NLPPlus. If you are planning to modify the library analyzers, it is recommended that you use the function
copy_library_analyzers to copy the analyzers to avoid having them
overwritten when a new version of NLPPlus is installed.

The analyze function returns a results object that make the analyzer
output files easily accessible to python. (see reults below)

#### copy_library_analyzers(self, to_dir: str, overwrite: bool=True)
This function copies the NLPPlus library analyzers into a safe
folder away from where they can be overwritten by newer versions
of the NLPPlus package. This allows coders to edit and modify the
analyzers to their liking. Remember to use the set_analyzers_folder
if you want to call your versions of these library analyzers
using the NLPPlus package.

#### input_text(analyzer_name: str, file_name: str)
When developing or editing NLP++ analyzers and calling them from
Python, it is convenient to test your python code on text you
have used to develop your analyzer in in the NLP++ VisualText extension for VSCode. This function retrieves the
text from a file in the analyzer's input directory for easy
access while developing your python code in conjunction with
and NLP++ analyzer.

### NLPPlus Engine Results

#### output
This returns a json object based on the parsed output.json file
producted by the analyzer. The analyzer has to purposely construct
the output.json file for this to work.

#### output.json
The output file produced by the analyzer that is a string, not
a json object. This file must explicity be created by the analyzer.

#### final.tree
All analyzers output a final tree of the text that is being processed.
This file is in the NLP++ tree format.

## <span style='color:orange'>NLP++ Development</span>

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
    
