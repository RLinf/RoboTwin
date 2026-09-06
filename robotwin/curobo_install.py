"""Owned installer for the pinned ``cuRobo @ d64c4b`` runtime planner.

cuRobo is the motion planner used by ``CuroboPlanner`` (the default
``planner_backend`` for the RoboTwin eval runtime). It is intentionally NOT
declared as a normal dependency in ``pyproject.toml`` because its build
contract cannot be expressed through package metadata alone. This module is
the minimal special logic that owns that contract; run it after installing
the ``[robotwin]`` extra::

    uv pip install -e ".[robotwin]" --torch-backend=cu128
    robotwin-install-curobo

Why cuRobo is not a normal pyproject dependency (Round 2 / Phase 5)
------------------------------------------------------------------
Two build-time facts make a plain ``"curobo @ git+..."`` dependency unworkable:

1. ``--no-build-isolation`` is required (build-time). cuRobo's
   ``[build-system] requires`` lists ``torch`` *unpinned*. Under uv's default
   build isolation the build backend fetches a fresh torch (a CPU / wrong-CUDA
   wheel) into the isolated env and compiles cuRobo's CUDA extensions against
   *that* torch, producing an ABI mismatch at runtime. ``--no-build-isolation``
   makes the build reuse the already-installed ``torch==2.7.1+cu128`` so the
   CUDA kernels link against the runtime torch. ``--no-build-isolation`` is a
   uv install flag, not a package-metadata field, so it cannot ride on a plain
   dependency declaration.

2. ``setuptools_scm`` version detection needs git tags (build-time). cuRobo
   versions itself with ``setuptools_scm`` (``[tool.setuptools_scm]``). uv's
   git fetch for a ``git+...@<commit>`` dependency fetches only the commit ref
   (``+<sha>:refs/commit/<sha>``), not the tag history, so ``setuptools_scm``
   cannot derive a version and the build fails. The workaround is
   ``SETUPTOOLS_SCM_PRETEND_VERSION=0.7.0`` in the build environment, which —
   like the flag above — is an environment setting that cannot be expressed in
   ``pyproject.toml`` dependencies.

Both are build-environment settings with no package-metadata equivalent, so
cuRobo stays a post-install step owned by this entrypoint rather than a
declared dependency. (Compare Phase 3's ``apply-lerobot-slim``: lerobot is
also not a normal dependency, but for a *resolver* reason — version conflicts
— whereas cuRobo is blocked purely by its *build* contract.)

Why ``--no-deps`` (re-verified, Round 2 / Phase 5)
--------------------------------------------------
The original contract kept ``--no-deps`` with a vague rationale ("may upgrade
scipy 1.10.1 -> 1.17"). The Phase 5 resolver re-check corrected this:

* cuRobo pins ``scipy>=1.7.0`` and ``torch>=1.10``; the runtime already pins
  ``scipy==1.10.1`` and ``torch==2.7.1``, both of which *satisfy* cuRobo's
  bounds. A dry-run resolving cuRobo's full dep set against the runtime pins
  holds ``scipy`` at ``1.10.1`` and resolves cleanly (69 packages, no
  conflict). So ``--no-deps`` is NOT required to prevent a scipy upgrade —
  that was never the real risk.

``--no-deps`` is nevertheless retained, for a different, verified reason:
cuRobo's full dep tree pulls packages its planner path does not import
(``numpy-quaternion``, ``scikit-image``, ``networkx``, ``pybind11``, ...).
The Round 1 parity run installed cuRobo with ``--no-deps`` and the planner
matched the candidate (position/velocity/final EEF), proving those extras are
not on the planner path. ``--no-deps`` therefore keeps the runtime lean
without affecting planner behaviour — it is a leanness decision, not a
version-conflict avoidance.

Fail-closed
-----------
The exact upstream commit is hardcoded; the installer will refuse to build a
different cuRobo. If the build fails (e.g. CUDA toolkit / torch mismatch), the
non-zero exit propagates so an install script aborts instead of silently
shipping a broken planner.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass

__all__ = ["CUROBO_SPEC", "CUROBO_SHA", "SETUPTOOLS_SCM_PRETEND_VERSION", "install_curobo", "main"]

# The exact upstream cuRobo commit previously vendored by the RoboTwin runtime.
# Do not change without re-running planner parity (position/velocity/final EEF
# must match the candidate baseline).
CUROBO_SHA = "d64c4b005459db10c5dd867d8b30a87d5bda9bdb"
CUROBO_SPEC = f"curobo @ git+https://github.com/NVlabs/curobo.git@{CUROBO_SHA}"

# cuRobo versions itself with setuptools_scm; uv's git fetch does not fetch the
# tag history, so pretend the version to let the build proceed.
SETUPTOOLS_SCM_PRETEND_VERSION = "0.7.0"


@dataclass
class CuroboInstallReport:
    command: list[str]
    returncode: int
    note: str = ""

    def as_line(self) -> str:
        return (
            f"[curobo-install] {' '.join(self.command)} -> rc={self.returncode}"
            + (f" - {self.note}" if self.note else "")
        )


def _find_uv() -> str:
    uv = shutil.which("uv")
    if uv is not None:
        return uv
    # Fall back to the uv that may live alongside the current interpreter.
    candidate = os.path.join(os.path.dirname(sys.executable), "uv")
    if os.path.exists(candidate):
        return candidate
    raise FileNotFoundError(
        "uv not found on PATH or next to the interpreter; install uv first "
        "(https://docs.astral.sh/uv/) before running robotwin-install-curobo."
    )


def install_curobo(uv: str | None = None) -> CuroboInstallReport:
    """Install the pinned cuRobo with the build contract above.

    Runs ``uv pip install --no-build-isolation --no-deps <cuRobo spec>`` with
    ``SETUPTOOLS_SCM_PRETEND_VERSION`` set, so cuRobo's CUDA extensions compile
    against the installed ``torch==2.7.1+cu128`` and its version is derivable.
    """

    uv_bin = uv or _find_uv()
    cmd = [uv_bin, "pip", "install", "--no-build-isolation", "--no-deps", CUROBO_SPEC]
    env = os.environ.copy()
    env["SETUPTOOLS_SCM_PRETEND_VERSION"] = SETUPTOOLS_SCM_PRETEND_VERSION
    result = subprocess.run(cmd, env=env)
    note = (
        "built with --no-build-isolation (CUDA exts link against installed "
        f"torch) and SETUPTOOLS_SCM_PRETEND_VERSION={SETUPTOOLS_SCM_PRETEND_VERSION}"
    )
    return CuroboInstallReport(command=cmd, returncode=result.returncode, note=note)


def main() -> int:
    """Console-script entry: install the pinned cuRobo and report."""

    report = install_curobo()
    print(report.as_line())
    if report.returncode:
        print(
            f"\ncuRobo install failed (rc={report.returncode}). This is usually a "
            "build-time issue: ensure torch==2.7.1+cu128 is installed in this venv "
            "(--torch-backend=cu128) and a compatible CUDA toolkit is on PATH so "
            "the CUDA extensions compile. See robotwin/curobo_install.py docstring.",
            file=sys.stderr,
        )
    return report.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
