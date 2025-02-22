#include <cstring>
#include <cstdlib>

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include "lite/nlp_engine.h"
#include "lite/vtrun.h"

#ifdef LINUX /* FIXME: Not a great "not Windows" symbol */
#define _tcsdup strdup
#endif

namespace nb = nanobind;
using namespace nb::literals;

/**
 * Wrap the analyze() method to deal with C++ friction.
 *
 * Takes an analyzer name (presumed to exist in the "analyzers"
 * subdirectory of the working folder) and a string, returns a string.
 * Note that few analyzers actually return a string, but instead
 * generally write stuff to the "output" directory in their working
 * folder.  That gets handled by the Python code in `__init__.py`.
 *
 * The output string gets copied a few times, because C++.
 */
const std::string
wrap_analyze(NLP_ENGINE &engine, const std::string &parser,
             const std::string &input, const bool develop) {
    _TCHAR *_parser = _tcsdup(parser.c_str());
    std::istringstream instream(input);
    std::ostringstream outstream;
    int rv = engine.analyze(_parser, &instream, &outstream, develop);
    free(_parser);
    return outstream.str();
}

NB_MODULE(bindings, m) {
    nb::class_<NLP_ENGINE>(m, "NLP_ENGINE", "Instance of the NLP++ Engine.")
        .def(nb::init<std::string, bool>(),
             "workingFolder"_a = ".",
             "silent"_a = true)
        .def("analyze", &wrap_analyze,
             "parser"_a, "input"_a, "develop"_a = false,
             "Analyze `input` with `parser`.\n"
             "The `parser` argument refers to an analyzer contained in the\n"
             "`analyzers` folder inside the workingFolder used to create\n"
             "this `Engine` instance.");
}
