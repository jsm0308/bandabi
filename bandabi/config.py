"""Configuration utilities.

- Fail fast on missing files / invalid structure.
- Keep config mutation explicit and localized.
"""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import yaml


class ConfigError(ValueError):
    """Raised when configuration is missing or invalid."""


def load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        obj = yaml.safe_load(f)
    if obj is None:
        return {}
    if not isinstance(obj, dict):
        raise ConfigError(f"YAML root must be a mapping (dict). Got: {type(obj).__name__} @ {path}")
    return obj


def save_yaml(obj: Dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, allow_unicode=True, sort_keys=False)


def save_json(obj: Any, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def short_hash(obj: Dict[str, Any]) -> str:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:8]


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(base)

    def rec(a: Dict[str, Any], b: Dict[str, Any]) -> None:
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(a.get(k), dict):
                rec(a[k], v)
            else:
                a[k] = v

    rec(out, override)
    return out


def deep_set(cfg: Dict[str, Any], dotted_path: str, value: Any) -> None:
    keys = dotted_path.split(".")
    cur: Dict[str, Any] = cfg
    for k in keys[:-1]:
        nxt = cur.get(k)
        if nxt is None:
            nxt = {}
            cur[k] = nxt
        if not isinstance(nxt, dict):
            raise ConfigError(
                f"Cannot deep-set '{dotted_path}': '{k}' is not a dict (got {type(nxt).__name__})"
            )
        cur = nxt
    cur[keys[-1]] = value


def _coerce_scalar(v: Any) -> Any:
    """
    YAML에서 values를 문자열로 넣어도 최대한 의미있는 타입으로 변환.
    - "none"/"null" -> None
    - "true"/"false" -> bool
    - "1", "1.2" -> int/float
    - 그 외 -> 원문(str) 유지
    """
    if v is None:
        return None
    if isinstance(v, (int, float, bool)):
        return v
    if isinstance(v, str):
        s = v.strip()
        lo = s.lower()
        if lo in ("none", "null", "~"):
            return None
        if lo in ("true", "false"):
            return lo == "true"
        # int / float 시도
        try:
            if "." in s or "e" in lo:
                return float(s)
            return int(s)
        except Exception:
            return s
    return v


@dataclass(frozen=True)
class ExperimentSpec:
    exp_name: str
    param_path: str
    values: List[Any]   # ✅ float 고정 금지


def load_experiment_spec(path: str) -> ExperimentSpec:
    data = load_yaml(path)
    exp_name = str(data.get("exp_name") or "exp")
    param_path = str(data.get("param_path") or "")
    values = data.get("values")

    if not param_path:
        raise ConfigError(f"Missing 'param_path' in sweep config: {path}")
    if not isinstance(values, list) or not values:
        raise ConfigError(f"Missing or invalid 'values' in sweep config: {path}")

    vals = [_coerce_scalar(v) for v in values]
    return ExperimentSpec(exp_name=exp_name, param_path=param_path, values=vals)
