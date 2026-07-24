"""
CI / Local Gate Test: Verify No Undefined Names (F821) or Compilation Errors exist in the codebase.

Runs:
1. `python -m compileall` (excluding archive/, .venv/, .git/)
2. `ruff check --select F821` (or pyflakes) across the repository (excluding archive/, .venv/, .git/)

Fails if ANY undefined name or syntax compilation error is detected.
"""
import ast
import compileall
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent


def test_compileall_no_errors():
    """Verify python -m compileall reports zero syntax or import compilation errors."""
    rx_pattern = re.compile(r".*(archive|\.venv|\.git|\.pytest_cache).*")
    success = compileall.compile_dir(
        dir=str(PROJECT_ROOT),
        maxlevels=10,
        quiet=1,
        rx=rx_pattern,
    )
    assert success, "compileall failed! One or more Python modules failed compilation."


def test_pyflakes_no_undefined_names():
    """Verify pyflakes / ruff F821 reports zero undefined name findings."""
    ruff_bin = shutil.which("ruff")
    if ruff_bin:
        cmd = [
            ruff_bin,
            "check",
            "--select",
            "F821",
            "--exclude",
            "archive/*,.venv/*,.git/*,.pytest_cache/*",
            str(PROJECT_ROOT),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"F821 Undefined Name Check Failed!\nOutput:\n{res.stdout}\nErrors:\n{res.stderr}"
    else:
        pyflakes_bin = shutil.which("pyflakes") or [sys.executable, "-m", "pyflakes"]
        if isinstance(pyflakes_bin, str):
            pyflakes_bin = [pyflakes_bin]
        cmd = pyflakes_bin + [str(PROJECT_ROOT)]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        f821_lines = [
            line for line in (res.stdout + res.stderr).splitlines()
            if "undefined name" in line and not any(ignored in line for ignored in ["archive", ".venv", ".git"])
        ]
        assert not f821_lines, f"Pyflakes F821 findings detected:\n" + "\n".join(f821_lines)

