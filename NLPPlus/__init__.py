"""Python extension for NLP++ text analysis engine.

Basic usage:

    import NLPPlus
    xml = NLPPlus.analyze("This is some text to be parsed")
    print(xml)

"""

import json
import logging
from shutil import copytree, rmtree
from tempfile import TemporaryDirectory
from os import PathLike, getcwd
from pathlib import Path
from typing import Optional, Any
import os
import glob

from .bindings import NLP_ENGINE  # type: ignore

LOGGER = logging.getLogger("NLPPlus")


def maybe_readfile(path: Path) -> Optional[str]:
    """Bogus utility function to maybe read a file."""
    if not path.exists():
        return None
    with open(path, "rt") as infh:
        return infh.read()


class EngineException(BaseException):
    pass


class Results:
    """Various results produced by the NLP++ analyzer."""

    def __init__(self, outtext: str, outdir: PathLike):
        LOGGER.info("Reading output from %s", outdir)
        self.output_text = outtext
        self.outdir = Path(outdir)

    @property
    def final_tree(self) -> Optional[str]:
        """The final parse tree, if any was produced."""
        return maybe_readfile(self.outdir / "final.tree")

    @property
    def output_json(self) -> Optional[str]:
        """The output JSON text, if any was produced."""
        return maybe_readfile(self.outdir / "output.json")

    @property
    def output(self) -> Optional[Any]:
        """The parsed output Json, if any was produced"""
        output_json = self.output_json
        if output_json is not None:
            return json.loads(output_json)
        return None


class Engine:
    """NLP++ Engine for a given working folder.

    Args:

      working_folder(optional, PathLike): Working folder for this
           instance.  If None, a temporary directory will be created
           and initialized with the default analyzers.  Otherwise,
           this must contain an `analyzers` and a `data` folder,
           unless `initialize` is `True`.
      verbose(optional, bool): Be more verbose.
      initialize(optional, bool): Initialize `working_folder` with
           the default analyzers.
    """
    def __init__(
        self,
        working_folder: Optional[PathLike] = None,
        analyzer_path: str = None,
        verbose: bool = False,
        initialize: bool = False,
    ):
        self._closed = False
        if working_folder is None:
            # ignore_cleanup_errors=True is now defense-in-depth: close()
            # / __exit__ / __del__ explicitly call self.engine.close()
            # before TemporaryDirectory.cleanup, which closes the engine's
            # cgerr.log handle and lets Windows delete the temp dir
            # cleanly. The flag still catches the corner case of an
            # interpreter shutdown where __del__ never runs (e.g. crash,
            # os._exit) — the OS reclaims the tempdir at process exit
            # regardless, so swallowing the cleanup error keeps stderr
            # quiet for users who never explicitly close. Engine-side
            # fix shipped in NLP-ENGINE-523 (engine v3.1.55+).
            self.tmpdir = TemporaryDirectory(
                prefix="NLPPlus-", ignore_cleanup_errors=True
            )
            self.working_folder = Path(self.tmpdir.name)
            initialize = True
        else:
            self.tmpdir = None
            self.working_folder = Path(working_folder)
        self.analyzer_path = None
        if initialize:
            copytree(
                Path(__file__).parent / "analyzers", self.working_folder / "analyzers"
            )
            copytree(Path(__file__).parent / "data", self.working_folder / "data")
            LOGGER.info("Initialized working folder in %s", self.working_folder)
        if not (self.working_folder / "analyzers").is_dir():
            raise EngineException(
                f"analyzers directory not found in folder '{working_folder}'"
            )
        if not (self.working_folder / "data").is_dir():
            raise EngineException(
                f"data directory not found in folder '{working_folder}'"
            )
        self.engine = NLP_ENGINE(str(self.working_folder), silent=not verbose)

    def close(self):
        """Tear down the underlying engine and release the working folder.

        Idempotent: safe to call multiple times. After ``close()``, any
        call to :meth:`analyze`, :meth:`compile`, or :meth:`cloud_compile`
        is undefined behavior — create a new ``Engine`` instead.

        On Windows in particular, calling ``close()`` (or using ``Engine``
        as a context manager) is what makes the auto-created
        ``TemporaryDirectory`` working folder delete cleanly: the engine
        keeps a file handle on ``<workfolder>/logs/cgerr.log`` open for
        the lifetime of the C++ instance, and Windows refuses to delete
        a directory that contains an open file. ``close()`` calls into
        the C++ engine's ``close()`` (NLP-ENGINE-523, engine v3.1.55+),
        which releases that handle before the tempdir is removed.
        """
        if self._closed:
            return
        self._closed = True
        # Engine.close() is idempotent on the C++ side as of engine
        # v3.1.55; older engines just no-op the second teardown.
        try:
            self.engine.close()
        except AttributeError:
            # Pre-3.1.55 binding without the close() method exposed;
            # fall back to letting __del__ tear it down. The tempdir
            # cleanup below will still hit the PermissionError on
            # Windows in that case — same situation as before 2.0.4.
            pass
        if self.tmpdir is not None:
            self.tmpdir.cleanup()
            self.tmpdir = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def __del__(self):
        # Best-effort: __del__ may run during interpreter shutdown when
        # modules are being torn down and the bindings module may already
        # be gone. Swallow anything that goes wrong here; the explicit
        # close() / context-manager paths are the supported way to get
        # deterministic cleanup.
        try:
            self.close()
        except Exception:
            pass

    def analyze(self, text: str, analyzer_name: str, develop: bool = False,
                compiled: bool = False) -> Results:
        """Analyze text with the named analyzer.

        Args:
          text: input text to analyze.
          analyzer_name: name of the analyzer under the working folder.
          develop: if True, the engine emits intermediate log/tree files
                   into the analyzer's `_log` directory.
          compiled: if True, the engine loads the analyzer's compiled
                    shared libraries (``bin/run.<ext>`` for the analyzer
                    body and ``bin/kb.<ext>`` for the compiled KB)
                    instead of running interpreted from the ``.nlp``
                    source.  See :meth:`compile` to produce the
                    generated C++ sources for those libraries, and the
                    package README for the cmake / cloud build step
                    that turns them into the actual ``.so``/``.dylib``/
                    ``.dll`` files.
        """
        analyzer_name = Path(analyzer_name)
        outdir = self.working_folder / "analyzers" / analyzer_name / "output"
        if self.analyzer_path:
            analyzer_name = Path(self.analyzer_path) / analyzer_name
            outdir = Path(self.analyzer_path) / "analyzers" / analyzer_name / "output"
        # Delete all files in the outdir
        file_list = glob.glob(str(outdir / "*"))
        for file_path in file_list:
            os.remove(file_path)
        outtext = self.engine.analyze(str(analyzer_name), text, develop,
                                      compiled)
        return Results(outtext, outdir)

    def compile(self, analyzer_name: str, develop: bool = False,
                kb_only: bool = False, analyzer_only: bool = False) -> Path:
        """Generate C++ source files for the named analyzer.

        Runs the engine in ``-COMPILE`` mode, or ``-COMPILEKB`` if
        ``kb_only=True`` (KB only), or ``-COMPILEANA`` if
        ``analyzer_only=True`` (analyzer rules only, skipping the KB).
        ``-COMPILE`` emits the analyzer body under ``<analyzer>/run/``
        and the knowledge base under ``<analyzer>/kb/``; ``-COMPILEKB``
        emits just ``<analyzer>/kb/``; ``-COMPILEANA`` emits just
        ``<analyzer>/run/``.  Returns the analyzer directory containing
        those generated trees.

        Use ``analyzer_only=True`` when only the rules changed and the
        KB is already compiled.  ``kb_only`` and ``analyzer_only`` are
        mutually exclusive.

        The generated C++ still needs to be built into shared
        libraries before :meth:`analyze` can load them with
        ``compiled=True``.  Use :meth:`cloud_compile` to do the build
        step via the public nlp-compile-service in one call.
        """
        if kb_only and analyzer_only:
            raise ValueError("compile: kb_only and analyzer_only are mutually exclusive")
        analyzer_name_p = Path(analyzer_name)
        if self.analyzer_path:
            analyzer_dir = (
                Path(self.analyzer_path) / "analyzers" / analyzer_name_p
            )
            engine_arg = str(Path(self.analyzer_path) / analyzer_name_p)
        else:
            analyzer_dir = (
                self.working_folder / "analyzers" / analyzer_name_p
            )
            engine_arg = str(analyzer_name_p)
        self.engine.compile(engine_arg, develop, kb_only, analyzer_only)
        return analyzer_dir

    def cloud_compile(self, analyzer_name: str,
                      dispatcher_url: Optional[str] = None,
                      kb_only: bool = False,
                      analyzer_only: bool = False,
                      develop: bool = False,
                      poll_interval: float = 2.0,
                      timeout: float = 30 * 60,
                      skip_local_compile: bool = False) -> Path:
        """End-to-end compile: codegen + cloud build + stage into bin/.

        Runs :meth:`compile` to produce the analyzer's ``run/`` + ``kb/``
        C++ trees (unless ``skip_local_compile=True``), packages them
        plus an auto-generated ``StdAfx.h`` stub into a tarball, submits
        that tarball to the public nlp-compile-service dispatcher, polls
        for the GitHub-Actions runner build to complete, downloads the
        resulting shared library, and stages it into
        ``<analyzer>/bin/`` as ``run.<ext>`` and ``kb.<ext>`` (and the
        Windows ``runu.<ext>`` / ``kbu.<ext>`` variants).  After this
        returns, :meth:`analyze` with ``compiled=True`` will load the
        compiled artifact.

        Returns the ``bin/`` directory path.

        Args:
          analyzer_name: analyzer under the engine's working folder.
          dispatcher_url: override the public dispatcher endpoint
            (default: ``cloud.DEFAULT_DISPATCHER_URL``).
          kb_only: compile only the KB.
          analyzer_only: compile only the analyzer rules (skip the KB).
            Mutually exclusive with ``kb_only``.
          develop: forwarded to local ``-COMPILE``.
          poll_interval: seconds between job-status checks.
          timeout: max seconds to wait for the runner build.
          skip_local_compile: if True, assume ``run/`` and ``kb/``
            already exist under the analyzer dir.
        """
        # Import here so the rest of the package keeps working in
        # environments that don't have an `urllib`-friendly TLS stack.
        from . import cloud
        return cloud.cloud_compile(
            self, analyzer_name,
            dispatcher_url=dispatcher_url or cloud.DEFAULT_DISPATCHER_URL,
            kb_only=kb_only, analyzer_only=analyzer_only, develop=develop,
            poll_interval=poll_interval, timeout=timeout,
            skip_local_compile=skip_local_compile,
        )
    
    def input_text(self, analyzer_name: str, file_name: str) -> str:
        """Return the text from a file in the input directory."""
        file_path = Path(self.analyzer_path) / analyzer_name / "input" / file_name
        if not file_path.is_file():
            raise EngineException(
                f"File not found in input directory '{file_path}'"
            )
        with open(file_path, "rt", encoding="utf-8") as file:
            text = file.read()
        return text
    
    def set_analyzers_folder(self, analyzer_name: str):
        """Set analyzers directory path."""
        self.analyzer_path = analyzer_name

    def copy_library_analyzers(self, to_dir: str, overwrite: bool=True):
        """Copy the library files to a directory."""
        copy_it = True

        if os.path.exists(to_dir):
            if overwrite:
                rmtree(to_dir)
            else:
                copy_it = False

        if copy_it:
            copytree(
                Path(__file__).parent / "analyzers", Path(to_dir)
            )
        self.analyzer_path = str(to_dir)


engine = Engine()


def set_working_folder(working_folder: Optional[str] = None, initialize: bool = False):
    """Reinitialize the NLP++ engine with a different working folder.

    Args:

      working_folder(str): Working folder to use, or `None` to use the
                           current working directory.
      initialize(bool): Initialize the new working folder with the built-in
                        analyzers and data.  (Optional, default=False)
    """
    global engine
    if working_folder is None:
        working_folder = getcwd()
    engine = Engine(Path(working_folder), initialize=initialize)


def copy_library_analyzers(analyzer_folder_path: str, overwrite=True):
    """Run the analyzer named on the input string."""
    engine.copy_library_analyzers(analyzer_folder_path, overwrite)


def set_analyzers_folder(analyzer_folder_path: str):
    """Run the analyzer named on the input string."""
    engine.set_analyzers_folder(analyzer_folder_path)


def analyze(text: str, parser: str = "parse-en-us", develop: bool = False,
            compiled: bool = False) -> str:
    """Run the analyzer named on the input string.

    If ``compiled=True``, the engine loads the analyzer's compiled
    shared libraries (``bin/run.<ext>`` and ``bin/kb.<ext>``) instead of
    running interpreted.  See :func:`compile` for producing those.
    """
    return engine.analyze(text, parser, develop, compiled).output_text


def compile(analyzer: str = "parse-en-us", develop: bool = False,
            kb_only: bool = False, analyzer_only: bool = False):
    """Generate C++ source files for the named analyzer.

    Wraps :meth:`Engine.compile`.  The generated trees land under
    ``<analyzer>/run/`` and ``<analyzer>/kb/`` inside the engine's
    working folder (or just ``kb/`` for ``kb_only``, or just ``run/``
    for ``analyzer_only``); they still need to be built into shared
    libraries before :func:`analyze` can load them with
    ``compiled=True``.
    """
    return engine.compile(analyzer, develop, kb_only, analyzer_only)


def cloud_compile(analyzer: str = "parse-en-us",
                  dispatcher_url: Optional[str] = None,
                  kb_only: bool = False,
                  analyzer_only: bool = False,
                  develop: bool = False,
                  poll_interval: float = 2.0,
                  timeout: float = 30 * 60,
                  skip_local_compile: bool = False):
    """Compile an analyzer end-to-end via the public nlp-compile-service.

    Wraps :meth:`Engine.cloud_compile` — see that method for the full
    docstring.  After this call returns, ``analyze(..., compiled=True)``
    will pick up the staged shared libraries from the analyzer's
    ``bin/`` directory.
    """
    return engine.cloud_compile(
        analyzer, dispatcher_url=dispatcher_url, kb_only=kb_only,
        analyzer_only=analyzer_only, develop=develop,
        poll_interval=poll_interval, timeout=timeout,
        skip_local_compile=skip_local_compile,
    )


def input_text(analyzer_name: str, file_name: str):
    """Return the text from a file in the input directory."""
    return engine.intput_text(analyzer_name, file_name)