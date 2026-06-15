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
 * `compiled=true` tells the engine to dlopen the analyzer's
 * `bin/run.<ext>` and `bin/kb.<ext>` shared libraries (produced by an
 * earlier `compile()` call plus a cmake/cloud build step).  Without
 * it, the engine runs interpreted from the .nlp source.
 *
 * The output string gets copied a few times, because C++.
 */
const std::string
wrap_analyze(NLP_ENGINE &engine, const std::string &parser,
             const std::string &input, const bool develop,
             const bool compiled) {
    _TCHAR *_parser = _tcsdup(parser.c_str());
    std::istringstream instream(input);
    std::ostringstream outstream;
    int rv = engine.analyze(_parser, &instream, &outstream,
                            develop, /*silent*/false,
                            /*compile*/false, compiled,
                            /*compileKB*/false);
    free(_parser);
    return outstream.str();
}

/**
 * Trigger the engine's `-COMPILE` mode for the named analyzer.
 *
 * This generates the C++ source files for the analyzer (under
 * `<analyzer>/run/`) and the knowledge base (under `<analyzer>/kb/`).
 * Those still need to be built into a shared library by an external
 * step — either cmake locally or the nlp-compile-service in the
 * cloud — before they can be loaded via `analyze(..., compiled=True)`.
 *
 * Maps directly to the engine's `init(analyzer, develop, silent,
 * compile=true, compiled=false, compileKB=false)` call (see
 * nlp/main.cpp's `if (compile)` branch).
 *
 * `kbOnly=true` switches to KB-only codegen — the analyzer grammar is
 * skipped and only `<analyzer>/kb/` is emitted.  Matches `init(...,
 * compileKB=true)`.
 *
 * `analyzerOnly=true` switches to analyzer-only codegen — only
 * `<analyzer>/run/` is emitted and the KB is left alone.  Matches
 * `init(..., compileAna=true)`.  Mutually exclusive with kbOnly.
 */
void
wrap_compile(NLP_ENGINE &engine, const std::string &analyzer,
             const bool develop, const bool kbOnly, const bool analyzerOnly) {
    _TCHAR *_analyzer = _tcsdup(analyzer.c_str());
    engine.init(_analyzer, develop, /*silent*/false,
                /*compile*/(!kbOnly && !analyzerOnly), /*compiled*/false,
                /*compileKB*/kbOnly, /*compileAna*/analyzerOnly);
    free(_analyzer);
}

/**
 * Return the bundled nlp-engine version string (e.g. "3.1.49").
 *
 * `cloud_compile()` in __init__.py uses this to populate the manifest
 * sent to the nlp-compile-service dispatcher — the dispatcher matches
 * it against published `nlpengine-compile-libs-<platform>.zip` release
 * artifacts in github.com/VisualText/nlp-engine.
 *
 * NLP_ENGINE_VERSION is the compile-time string baked into nlp/main.cpp;
 * scikit-build-core defines it via target_compile_definitions in
 * CMakeLists.txt.  If unset (older build), we fall back to "unknown" so
 * Python-side callers can detect the missing version cleanly.
 */
const std::string
wrap_engine_version() {
#ifdef NLP_ENGINE_VERSION
    return NLP_ENGINE_VERSION;
#else
    return "unknown";
#endif
}

NB_MODULE(bindings, m) {
    m.def("engine_version", &wrap_engine_version,
          "Return the bundled nlp-engine version string (e.g. '3.1.49').");
    nb::class_<NLP_ENGINE>(m, "NLP_ENGINE", "Instance of the NLP++ Engine.")
        .def(nb::init<std::string, bool>(),
             "workingFolder"_a = ".",
             "silent"_a = true)
        .def("analyze", &wrap_analyze,
             "parser"_a, "input"_a, "develop"_a = false,
             "compiled"_a = false,
             "Analyze `input` with `parser`.\n"
             "The `parser` argument refers to an analyzer contained in the\n"
             "`analyzers` folder inside the workingFolder used to create\n"
             "this `Engine` instance.\n"
             "If `compiled=True`, the engine loads bin/run.<ext> and\n"
             "bin/kb.<ext> from the analyzer dir instead of running\n"
             "interpreted from the .nlp source.  Build those shared\n"
             "libraries first via `compile()` plus an external cmake/\n"
             "cloud build step.")
        .def("compile", &wrap_compile,
             "analyzer"_a, "develop"_a = false, "kbOnly"_a = false,
             "analyzerOnly"_a = false,
             "Emit C++ source files for `analyzer`.\n"
             "Generates <analyzer>/run/*.cpp and <analyzer>/kb/*.cpp\n"
             "(or just <analyzer>/kb/*.cpp if `kbOnly=True`, or just\n"
             "<analyzer>/run/*.cpp if `analyzerOnly=True`).  Those\n"
             "still need to be built into shared libraries before\n"
             "`analyze(..., compiled=True)` can load them.")
        // NLP_ENGINE has two close() overloads: close() and
        // close(_TCHAR *analyzer). Cast to pick the nullary one
        // (we want the global teardown, not the per-analyzer one).
        .def("close",
             static_cast<int (NLP_ENGINE::*)()>(&NLP_ENGINE::close),
             "Tear down the engine's VTRun runtime and release the open\n"
             "<workfolder>/logs/cgerr.log handle. Safe to call multiple\n"
             "times (engine v3.1.55+ NLP-ENGINE-523 made close()\n"
             "idempotent). After close() returns, any subsequent\n"
             "analyze()/compile() call on this instance is undefined\n"
             "behavior. NLPPlus.Engine.close() / __exit__ / __del__\n"
             "calls this before deleting the TemporaryDirectory backing\n"
             "the working folder; this is what makes the temp-dir\n"
             "cleanup safe on Windows where an open file handle would\n"
             "otherwise block the rmtree.");
}
