"""Packaged console entrypoint forwarding to CLI runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def main() -> int:
    cli_file = Path(__file__).resolve().parent.parent / "bin" / "fleet"
    spec = importlib.util.spec_from_file_location("fleet_cli", cli_file)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return int(mod.main())
