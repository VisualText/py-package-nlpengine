"""Cloud-compile orchestration for NLP++ analyzers.

Mirrors the flow used by the vscode-nlp extension (see
``src/compile.ts:compileCppOnCloud`` in https://github.com/VisualText/vscode-nlp):

1. Run the engine's ``-COMPILE`` step locally to produce ``run/`` and
   ``kb/`` C++ trees under the analyzer directory.
2. Stage those trees plus an auto-generated ``StdAfx.h`` stub and a
   manifest JSON into a tarball.
3. POST the tarball to the nlp-compile-service dispatcher
   (``${dispatcher_url}/build``).
4. Poll ``${dispatcher_url}/jobs/<id>`` until the GitHub-Actions runner
   finishes the build.
5. Download the resulting shared library and stage it as
   ``<analyzer>/bin/run.<ext>`` (and ``<analyzer>/bin/kb.<ext>`` for the
   full-analyzer path) so ``engine.analyze(text, name, compiled=True)``
   finds it.

Pure stdlib — no `requests` dependency.  Multipart upload is built by
hand against the well-defined multipart/form-data wire format.

The default dispatcher URL is the same Cloudflare Worker the vscode-nlp
extension talks to, but callers can override per-call.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import platform
import shutil
import sys
import tarfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

LOGGER = logging.getLogger("NLPPlus.cloud")

DEFAULT_DISPATCHER_URL = (
    "https://nlp-compile-dispatcher.dehilster.workers.dev"
)

# Cloudflare's browser-integrity check (the worker sits behind it) rejects
# urllib's default `Python-urllib/3.x` UA with HTTP 403 / error code 1010.
# Identify ourselves clearly so the worker accepts the request and so the
# server-side logs can attribute traffic. Engine version is filled in
# lazily on first call (it requires the bindings module).
_USER_AGENT = "NLPPlus (Python urllib)"


def _user_agent() -> str:
    """Return the User-Agent string, lazily including the engine version.

    Kept lazy so this module can be imported (and tested) without the
    compiled bindings being available — useful for the platform-key /
    sha-helper unit tests.
    """
    global _USER_AGENT
    if "/" not in _USER_AGENT:
        try:
            from . import bindings as _bindings  # type: ignore
            _USER_AGENT = (
                f"NLPPlus/{_bindings.engine_version()} (Python urllib)"
            )
        except Exception:
            pass
    return _USER_AGENT

# Auto-generated header that the engine's -COMPILE output expects.  Each
# generated pass*.cpp begins with `#include "StdAfx.h"`; cmake on the
# runner force-includes this file too via /FI on MSVC and -include on
# gcc/clang.  Same stub vscode-nlp writes.
_STDAFX_STUB = (
    '// Auto-generated stub. Engine-generated .cpp files include '
    '"StdAfx.h" by convention.\n'
    '#pragma once\n'
    '#ifdef _WIN32\n'
    '#ifndef WIN32_LEAN_AND_MEAN\n'
    '#define WIN32_LEAN_AND_MEAN\n'
    '#endif\n'
    '#ifndef NOMINMAX\n'
    '#define NOMINMAX\n'
    '#endif\n'
    '#include <windows.h>\n'
    '#include <tchar.h>\n'
    '#endif\n'
    '#include "my_tchar.h"\n'
)


class CloudCompileError(RuntimeError):
    """Raised when the cloud-compile pipeline fails to produce an artifact.

    Wraps both HTTP-layer failures (dispatcher unreachable, 4xx/5xx, job
    timeout) and runner-side build failures (compile errors surfaced via
    the dispatcher's ``errors`` artifact).
    """


def cloud_platform_key() -> str:
    """Return the runner label the dispatcher routes to for this host.

    Mirrors ``compile.ts:cloudPlatformKey``.  These strings are the
    inputs accepted by ``compile-analyzer.yml`` in nlp-compile-service.
    """
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos-arm64" if platform.machine() == "arm64" else "macos-x86_64"
    if sys.platform.startswith("linux"):
        # /etc/os-release is the portable identifier across distros.
        # Fall back to "linux-latest" if we can't parse a version we know.
        try:
            with open("/etc/os-release", "rt") as fh:
                osr = fh.read()
            for line in osr.splitlines():
                if line.startswith("VERSION_ID="):
                    v = line.split("=", 1)[1].strip().strip('"')
                    if v == "20.04":
                        return "linux-20.04"
                    if v == "22.04":
                        return "linux-22.04"
                    break
        except OSError:
            pass
        return "linux-latest"
    raise CloudCompileError(
        f"Unsupported platform for cloud compile: {sys.platform}"
    )


def shared_library_ext() -> str:
    """File extension the dispatcher's artifact comes back as."""
    if sys.platform.startswith("win"):
        return ".dll"
    if sys.platform == "darwin":
        return ".dylib"
    return ".so"


def _stage_payload(analyzer_dir: Path, stage_dir: Path, kb_only: bool,
                   analyzer_only: bool = False) -> None:
    """Copy run/ + kb/ trees and write the StdAfx.h stub into stage_dir.

    Skips run/ when ``kb_only=True``; skips kb/ when ``analyzer_only=True``.
    Only `.cpp` and `.h` files are copied — the dispatcher's emit-cmake.sh
    globs both and the engine emits per-pass headers alongside the .cpp
    files.
    """
    if kb_only:
        subdirs = ["kb"]
    elif analyzer_only:
        subdirs = ["run"]
    else:
        subdirs = ["run", "kb"]
    any_source = False
    for sub in subdirs:
        src = analyzer_dir / sub
        if not src.is_dir():
            continue
        dst = stage_dir / sub
        dst.mkdir(parents=True, exist_ok=True)
        for fname in os.listdir(src):
            low = fname.lower()
            if not (low.endswith(".cpp") or low.endswith(".h")):
                continue
            shutil.copyfile(src / fname, dst / fname)
            any_source = True
    if not any_source:
        raise CloudCompileError(
            f"No generated .cpp/.h files found under {analyzer_dir}. "
            f"Did you call engine.compile() first?"
        )
    (stage_dir / "StdAfx.h").write_text(_STDAFX_STUB, encoding="utf-8")


def _make_tarball(stage_dir: Path, tar_path: Path) -> None:
    """Pack stage_dir contents (without the stage_dir itself) into tar.gz."""
    with tarfile.open(tar_path, "w:gz") as tar:
        for entry in sorted(os.listdir(stage_dir)):
            tar.add(stage_dir / entry, arcname=entry)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _post_multipart(
    url: str, manifest: dict, tar_path: Path
) -> Tuple[int, bytes]:
    """POST a manifest+payload pair as multipart/form-data using urllib.

    Building this by hand avoids adding `requests` (and its transitive
    deps) as a runtime requirement.  The format is straightforward
    enough that a hand-rolled writer is about 20 lines.
    """
    boundary = "----nlpplus-" + uuid.uuid4().hex
    crlf = b"\r\n"
    parts: list[bytes] = []

    # manifest field
    parts.append(("--" + boundary).encode())
    parts.append(crlf)
    parts.append(
        b'Content-Disposition: form-data; name="manifest"' + crlf
    )
    parts.append(b"Content-Type: application/json" + crlf)
    parts.append(crlf)
    parts.append(json.dumps(manifest).encode("utf-8"))
    parts.append(crlf)

    # payload field
    parts.append(("--" + boundary).encode())
    parts.append(crlf)
    parts.append(
        b'Content-Disposition: form-data; name="payload"; '
        b'filename="payload.tar.gz"' + crlf
    )
    parts.append(b"Content-Type: application/gzip" + crlf)
    parts.append(crlf)
    with open(tar_path, "rb") as fh:
        parts.append(fh.read())
    parts.append(crlf)

    # closing boundary
    parts.append(("--" + boundary + "--").encode())
    parts.append(crlf)

    body = b"".join(parts)
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": (
                "multipart/form-data; boundary=" + boundary
            ),
            "Content-Length": str(len(body)),
            "User-Agent": _user_agent(),
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _poll_job(
    dispatcher_url: str,
    job_id: str,
    poll_interval: float,
    timeout: float,
) -> dict:
    """GET /jobs/<id> until status is 'done' or 'failed' (or timeout)."""
    deadline = time.monotonic() + timeout
    url = dispatcher_url.rstrip("/") + "/jobs/" + job_id
    last_status: Optional[str] = None
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": _user_agent()}
            )
            with urllib.request.urlopen(req) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raise CloudCompileError(
                f"Polling /jobs/{job_id} returned HTTP {exc.code}: "
                f"{exc.read()!r}"
            ) from exc
        status = payload.get("status")
        if status != last_status:
            LOGGER.info("cloud-compile job %s: %s", job_id, status)
            last_status = status
        if status == "done":
            return payload
        if status == "failed":
            errors = payload.get("errors") or payload.get("error") or payload
            raise CloudCompileError(
                f"Cloud build failed for job {job_id}: {errors!r}"
            )
        time.sleep(poll_interval)
    raise CloudCompileError(
        f"Cloud build for job {job_id} did not finish within "
        f"{timeout:.0f}s"
    )


def _download(url: str, dest: Path) -> None:
    """Stream-download `url` to `dest` (overwriting if exists)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    with urllib.request.urlopen(req) as resp:
        with open(dest, "wb") as out:
            shutil.copyfileobj(resp, out, length=1 << 16)


def _stage_artifact(
    artifact_url: str,
    analyzer_dir: Path,
    analyzer_name: str,
    kb_only: bool,
    analyzer_only: bool = False,
) -> Path:
    """Download the cloud artifact and stage it as the bin/ shared libs.

    The dispatcher returns ONE shared library per build (run+kb fused,
    kb-only, or analyzer-only).  We mirror the vscode-nlp extension's
    staging behaviour: drop it into ``<analyzer>/bin/`` as both
    ``run.<ext>`` and ``kb.<ext>`` for the full build (the engine's
    -COMPILED dlopens both from there), as ``kb.<ext>`` alone for
    ``kb_only``, or as ``run.<ext>`` alone for ``analyzer_only``
    (leaving any existing ``kb.<ext>`` in place).  Returns the bin/
    directory path.
    """
    ext = shared_library_ext()
    bin_dir = analyzer_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Stream to a single temp file first, then copy into place to avoid
    # leaving a half-written bin/run.<ext> if the network drops.
    tmp_artifact = bin_dir / ("_artifact_" + uuid.uuid4().hex + ext)
    try:
        _download(artifact_url, tmp_artifact)
        if kb_only:
            targets = [f"kb{ext}"]
        elif analyzer_only:
            targets = [f"run{ext}", f"runu{ext}"]
        else:
            # vscode-nlp also writes the "u" (unicode) variants on
            # Windows; mirror that so the engine's load_compiled finds
            # whichever name the build flavour expects.
            targets = [f"run{ext}", f"runu{ext}", f"kb{ext}", f"kbu{ext}"]
        for name in targets:
            shutil.copyfile(tmp_artifact, bin_dir / name)
    finally:
        try:
            tmp_artifact.unlink()
        except FileNotFoundError:
            pass
    return bin_dir


def cloud_compile(
    engine,  # type: ignore  # forward-declared to avoid circular import
    analyzer_name: str,
    dispatcher_url: str = DEFAULT_DISPATCHER_URL,
    kb_only: bool = False,
    analyzer_only: bool = False,
    develop: bool = False,
    poll_interval: float = 2.0,
    timeout: float = 30 * 60,
    skip_local_compile: bool = False,
) -> Path:
    """Compile an analyzer end-to-end via the nlp-compile-service cloud.

    Returns the analyzer's ``bin/`` directory containing the staged
    shared libraries.  After this returns, ``engine.analyze(text, name,
    compiled=True)`` will pick them up.

    Args:
      engine: an :class:`NLPPlus.Engine` instance (passed in to keep
        ``cloud.py`` decoupled from the import cycle).
      analyzer_name: name of the analyzer under
        ``engine.working_folder/analyzers/``.
      dispatcher_url: base URL of the nlp-compile-service Cloudflare
        Worker.  Default points at the public dehilster.workers.dev
        deployment that the vscode-nlp extension also uses.
      kb_only: if True, only the KB is compiled (``run/`` is skipped).
      analyzer_only: if True, only the analyzer rules are compiled
        (``kb/`` is skipped). Mutually exclusive with ``kb_only``.
      develop: forwarded to the local ``-COMPILE`` step.
      poll_interval: seconds between ``GET /jobs/<id>`` checks.
      timeout: max seconds to wait for the runner build before raising
        :class:`CloudCompileError`.  GitHub-Actions Windows free-tier
        queues can stall 5-10 minutes; the default 30-minute ceiling
        leaves room for that.
      skip_local_compile: if True, assume ``run/`` and ``kb/`` already
        exist under the analyzer dir (e.g. from a prior call to
        :meth:`Engine.compile`).  Useful if you want to re-package and
        re-submit without regenerating the .cpp.
    """
    if kb_only and analyzer_only:
        raise CloudCompileError(
            "kb_only and analyzer_only are mutually exclusive"
        )
    if not skip_local_compile:
        analyzer_dir = engine.compile(
            analyzer_name, develop=develop, kb_only=kb_only,
            analyzer_only=analyzer_only,
        )
    else:
        # Mirror Engine.compile's directory resolution without invoking
        # the engine.
        analyzer_dir = (
            Path(engine.analyzer_path)
            if engine.analyzer_path
            else engine.working_folder / "analyzers"
        ) / analyzer_name

    if not analyzer_dir.is_dir():
        raise CloudCompileError(
            f"Analyzer directory not found: {analyzer_dir}"
        )

    # Lazy import to avoid circular dependency at module-load time.
    from .bindings import engine_version  # type: ignore

    engine_ver = engine_version()
    platform_key = cloud_platform_key()

    import tempfile

    with tempfile.TemporaryDirectory(prefix="nlpplus-cloud-") as stage_str:
        stage_dir = Path(stage_str)
        _stage_payload(analyzer_dir, stage_dir, kb_only, analyzer_only)
        tar_path = stage_dir / "_payload.tar.gz"
        _make_tarball(stage_dir, tar_path)
        sources_hash = _sha256_file(tar_path)
        manifest = {
            "schemaVersion": 1,
            "engineVersion": engine_ver,
            "platform": platform_key,
            "analyzerName": analyzer_name,
            "kbOnly": kb_only,
            "analyzerOnly": analyzer_only,
            "sourcesHash": "sha256:" + sources_hash,
            "client": "NLPPlus",
        }
        LOGGER.info(
            "Uploading %s to %s (engine=%s platform=%s kb_only=%s)",
            analyzer_name, dispatcher_url, engine_ver, platform_key,
            kb_only,
        )
        status, body = _post_multipart(
            dispatcher_url.rstrip("/") + "/build", manifest, tar_path
        )
        if status >= 400:
            raise CloudCompileError(
                f"Dispatcher /build returned HTTP {status}: {body!r}"
            )
        submitted = json.loads(body)
        job_id = submitted.get("jobId")
        artifact_url = submitted.get("artifactUrl")
        if submitted.get("cached") and artifact_url:
            LOGGER.info(
                "Cache hit for sources_hash; reusing prior artifact"
            )
        else:
            if not job_id:
                raise CloudCompileError(
                    f"Dispatcher did not return a jobId: {submitted!r}"
                )
            polled = _poll_job(
                dispatcher_url, job_id, poll_interval, timeout
            )
            artifact_url = polled.get("artifactUrl")
            if not artifact_url:
                raise CloudCompileError(
                    f"Job {job_id} reported done but produced no "
                    f"artifactUrl: {polled!r}"
                )

    # tarball cleanup happens via TemporaryDirectory.__exit__; now stage
    # the artifact into the analyzer's bin/ dir.
    bin_dir = _stage_artifact(
        artifact_url, analyzer_dir, analyzer_name, kb_only, analyzer_only
    )
    LOGGER.info("Cloud compile output staged into %s", bin_dir)
    return bin_dir
