"""Python extension for NLP++ text analysis engine.

Basic usage:

    import NLPPlus
    xml = NLPPlus.analyze("This is some text to be parsed")
    print(xml)

"""

import json
import logging
from shutil import copytree
from tempfile import TemporaryDirectory
from os import PathLike, getcwd
from pathlib import Path
from typing import Optional, Any

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
    def __init__(
        self,
        working_folder: Optional[PathLike] = None,
        verbose: bool = False,
        initialize: bool = False,
    ):
        if working_folder is None:
            self.tmpdir = TemporaryDirectory(prefix="NLPPlus-")
            self.working_folder = Path(self.tmpdir.name)
            initialize = True
        else:
            self.tmpdir = None
            self.working_folder = Path(working_folder)
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

    def analyze(self, text: str, analyzer_name: str) -> Results:
        """Analyze text with the named analyzer."""
        outdir = self.working_folder / "analyzers" / analyzer_name / "output"
        outtext = self.engine.analyze(analyzer_name, text)
        return Results(outtext, outdir)


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


def analyze(str: str, parser: str = "parse-en-us"):
    """Run the analyzer named on the input string."""
    return engine.analyze(str, parser).output_text
