"""
Per-call-site runtime attribution (``X-Swfte-Callsite``).

The header is sent only when:

* an explicit ``callsite="cs_<24 hex>"`` is passed to an artifact-invoking
  method (it always wins), or
* no ``callsite`` is passed, ``SWFTE_CALLSITE_STACK=1`` is set, the runtime is
  not production, and the local caller map written by ``swfte scan`` has an
  entry for the calling ``path:line``.

Nothing else ever sends it. Invalid ids are never sent. Only the precomputed
id leaves the process: no file contents, paths or env values are transmitted.
"""

import json
import os
import re
import sys
import warnings
from typing import Dict, Optional

HEADER = "X-Swfte-Callsite"

_ID_RE = re.compile(r"cs_[0-9a-f]{24}")
_PKG_DIR = os.path.dirname(os.path.realpath(__file__))
_PROD_ENV_VARS = ("SWFTE_ENV", "ENV", "PYTHON_ENV")
_production_warned = False


def is_valid_callsite(value: object) -> bool:
    """True when ``value`` is exactly ``cs_`` followed by 24 lowercase hex characters."""
    return isinstance(value, str) and _ID_RE.fullmatch(value) is not None


def _is_production() -> bool:
    return any(os.environ.get(name) == "production" for name in _PROD_ENV_VARS)


def _warn_production_once() -> None:
    global _production_warned
    if _production_warned:
        return
    _production_warned = True
    warnings.warn(
        "SWFTE_CALLSITE_STACK is ignored in production; pass callsite= explicitly instead.",
        RuntimeWarning,
        stacklevel=4,
    )


def _callers_path() -> str:
    explicit = os.environ.get("SWFTE_CODEMAP_CALLERS")
    if explicit:
        return explicit
    return os.path.join(os.getcwd(), ".swfte", "codemap", "callers.json")


def _load_caller_map() -> Optional[Dict[str, object]]:
    try:
        with open(_callers_path(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("version") != 1:
        return None
    root, entries = data.get("root"), data.get("entries")
    if not isinstance(root, str) or not root or not isinstance(entries, dict):
        return None
    return data


def _outside_frame():
    """The first stack frame whose file is not inside the swfte package."""
    frame = sys._getframe(1)
    while frame is not None:
        filename = os.path.realpath(frame.f_code.co_filename)
        if not (filename == _PKG_DIR or filename.startswith(_PKG_DIR + os.sep)):
            return frame
        frame = frame.f_back
    return None


def _from_stack() -> Optional[str]:
    caller_map = _load_caller_map()
    if caller_map is None:
        return None
    frame = _outside_frame()
    if frame is None:
        return None
    filename = frame.f_code.co_filename
    if filename.startswith("<"):  # <stdin>, <string>, frozen modules
        return None
    root = os.path.realpath(str(caller_map["root"]))
    try:
        rel = os.path.relpath(os.path.realpath(filename), root)
    except ValueError:  # different drive on Windows
        return None
    if rel == os.pardir or rel.startswith(os.pardir + os.sep) or os.path.isabs(rel):
        return None
    key = f"{rel.replace(os.sep, '/')}:{frame.f_lineno}"
    found = caller_map["entries"].get(key)  # type: ignore[union-attr]
    return found if is_valid_callsite(found) else None


def resolve_callsite(callsite: Optional[str] = None) -> Optional[str]:
    """
    Decide the call-site id for one artifact invocation, or ``None`` for no header.

    Must be called from the public SDK method the user called, so the first frame
    outside the package is the user's call.
    """
    if callsite is not None:
        return callsite if is_valid_callsite(callsite) else None
    if os.environ.get("SWFTE_CALLSITE_STACK") != "1":
        return None
    if _is_production():
        _warn_production_once()
        return None
    return _from_stack()


def callsite_headers(callsite: Optional[str]) -> Optional[Dict[str, str]]:
    """Extra request headers for an already-resolved id (``None`` when there is none)."""
    return {HEADER: callsite} if callsite else None
