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
 * Wrap the analyze() method to have a more Pythonic interface.
 *
 * Takes an analyzer name (presumed to exist in the "analyzers"
 * subdirectory of the working folder) and a string, returns a string.
 *
 * The output string gets copied a few times, because C++.
 */
const std::string
wrap_analyze(NLP_ENGINE &engine, const std::string &parser, const std::string &input) {
    _TCHAR *_parser = _tcsdup(parser.c_str());
    std::istringstream instream(input);
    std::ostringstream outstream;
    int rv = engine.analyze(_parser, &instream, &outstream);
    free(_parser);
    return outstream.str();
}

NB_MODULE(NLPPlus, m) {
    nb::class_<NLP_ENGINE>(m, "Engine")
        .def(nb::init<std::string, bool>(),
             "workingFolder"_a = ".",
             "silent"_a = true)
        .def("analyze", &wrap_analyze);
}
