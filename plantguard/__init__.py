"""Canonical PlantGuard package exposing modules housed under ``src``.

This shim keeps the long-standing ``src.*`` layout working while providing a
proper top-level package for distribution and external consumption.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys
from pathlib import Path
from typing import Final

_SRC_DIR: Final = Path(__file__).resolve().parent.parent / "src"
if _SRC_DIR.is_dir():
    src_path = str(_SRC_DIR)
    if src_path not in sys.path:
        sys.path.append(src_path)

_EXPORTS: Final = (
    "adapters_compat",
    "core",
    "data",
    "features",
    "training",
    "ui",
    "utils",
    "plantguard_bot",
)

__all__ = list(_EXPORTS)

for _name in _EXPORTS:
    try:
        module = importlib.import_module(f"src.{_name}")
    except ModuleNotFoundError:
        continue
    sys.modules[f"{__name__}.{_name}"] = module
    if _name not in globals():
        globals()[_name] = module

for _existing_name, _existing_module in list(sys.modules.items()):
    if _existing_name == "src" or not _existing_name.startswith("src."):
        continue
    _alias = f"{__name__}.{_existing_name[len('src.'):]}"
    sys.modules.setdefault(_alias, _existing_module)


class _SrcAliasLoader(importlib.abc.Loader):
    """Loader that reuses the corresponding ``src.*`` module."""

    def __init__(self, alias_name: str, target_name: str) -> None:
        self.alias_name = alias_name
        self.target_name = target_name

    def create_module(self, spec):  # type: ignore[override]
        return None  # Defer to default module creation semantics

    def exec_module(self, module):  # type: ignore[override]
        target_module = importlib.import_module(self.target_name)
        sys.modules[self.alias_name] = target_module


class _SrcAliasFinder(importlib.abc.MetaPathFinder):
    """Meta path finder wiring ``plantguard.*`` imports to ``src.*`` modules."""

    prefix: Final = "plantguard."
    target_prefix: Final = "src."

    def find_spec(self, fullname: str, path, target=None):  # type: ignore[override]
        if not fullname.startswith(self.prefix):
            return None
        if fullname in sys.modules:
            return None

        target_name = self.target_prefix + fullname[len(self.prefix) :]
        target_spec = importlib.util.find_spec(target_name)
        if target_spec is None:
            return None

        return importlib.util.spec_from_loader(
            fullname,
            _SrcAliasLoader(fullname, target_name),
            is_package=target_spec.submodule_search_locations is not None,
        )


if not any(isinstance(finder, _SrcAliasFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, _SrcAliasFinder())
