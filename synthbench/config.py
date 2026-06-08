from __future__ import annotations

from pathlib import Path
from typing import Any


def _coerce(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    """Read the repo's simple config.yaml without external YAML dependencies."""
    cfg: dict[str, Any] = {}
    current_key: str | None = None
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line:
            continue
        if line.startswith("  - "):
            if current_key is None:
                raise ValueError("list item without parent key")
            if not isinstance(cfg.get(current_key), list):
                cfg[current_key] = []
            cfg.setdefault(current_key, []).append(_coerce(line[4:]))
            continue
        if line.startswith("  "):
            if current_key is None:
                raise ValueError("nested key without parent key")
            key, value = line.strip().split(":", 1)
            if not isinstance(cfg.get(current_key), dict):
                cfg[current_key] = {}
            cfg.setdefault(current_key, {})[key.strip()] = _coerce(value)
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            cfg[key] = _coerce(value)
            current_key = None
        else:
            cfg[key] = []
            current_key = key
    return cfg
