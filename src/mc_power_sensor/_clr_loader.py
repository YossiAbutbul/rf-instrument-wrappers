"""Locate and load Mini-Circuits `mcl_pm_NET45.dll` via pythonnet."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .exceptions import DLLLoadError

_DLL_NAME = "mcl_pm_NET45"
_DLL_FILE = f"{_DLL_NAME}.dll"

_DEFAULT_SEARCH_PATHS: tuple[Path, ...] = (
    Path(r"C:\Program Files\Mini-Circuits\Power_Meter"),
    Path(r"C:\Program Files (x86)\Mini-Circuits\Power_Meter"),
)

_usb_pm_type = None  # cached after first load


def _candidate_dirs() -> list[Path]:
    candidates: list[Path] = []

    env_dir = os.environ.get("MCL_PM_DLL_DIR")
    if env_dir:
        candidates.append(Path(env_dir))

    repo_dll = Path(__file__).resolve().parents[2] / "dll"
    candidates.append(repo_dll)

    candidates.extend(_DEFAULT_SEARCH_PATHS)
    return candidates


def _find_dll() -> Path:
    for d in _candidate_dirs():
        candidate = d / _DLL_FILE
        if candidate.is_file():
            return candidate
    searched = "\n  - ".join(str(d) for d in _candidate_dirs())
    raise DLLLoadError(
        f"{_DLL_FILE} not found. Download it from "
        "https://www.minicircuits.com/softwaredownload/pm.html and place it in "
        f"one of:\n  - {searched}\n"
        "Or set the MCL_PM_DLL_DIR environment variable."
    )


def load_usb_pm():
    """Return the `usb_pm` .NET type, loading the DLL if needed."""
    global _usb_pm_type
    if _usb_pm_type is not None:
        return _usb_pm_type

    dll_path = _find_dll()

    try:
        import clr  # type: ignore[import-not-found]
    except ImportError as exc:
        raise DLLLoadError(
            "pythonnet is not installed. Run: pip install pythonnet>=3.0.3"
        ) from exc

    dll_dir = str(dll_path.parent)
    if dll_dir not in sys.path:
        sys.path.append(dll_dir)

    try:
        clr.AddReference(_DLL_NAME)
    except Exception as exc:  # broad: pythonnet raises .NET exceptions
        raise DLLLoadError(f"Failed to load {dll_path}: {exc}") from exc

    try:
        from mcl_pm_NET45 import usb_pm  # type: ignore[import-not-found]
    except ImportError as exc:
        raise DLLLoadError(
            f"{_DLL_NAME} loaded but `usb_pm` class not found. "
            "DLL version mismatch?"
        ) from exc

    _usb_pm_type = usb_pm
    return usb_pm
