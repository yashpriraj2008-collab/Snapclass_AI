"""
Compatibility package.

This repo’s application code lives in `snapclass/src`, but some tooling (like
Pylance/Pyright) may try to resolve imports from a top-level `src` package.

By extending `__path__` to include `snapclass/src`, imports such as
`src.screens.pricing` will resolve correctly.
"""

from __future__ import annotations

from pathlib import Path

# Directory structure:
#   repo_root/
#     src/                <-- this file
#     snapclass/src/      <-- real modules
_this_dir = Path(__file__).resolve().parent
_snapclass_src = _this_dir.parent / "snapclass" / "src"

# Make this a "package" that can load submodules from snapclass/src.
# (Python will search __path__ entries for subpackages like `screens`.)
if _snapclass_src.exists():
    __path__.append(str(_snapclass_src))  # type: ignore[name-defined]
