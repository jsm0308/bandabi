"""Compatibility shim for configuration & IO helpers.

Original helpers lived in src/io_utils.py.
They are now consolidated in bandabi.config.
"""

from bandabi.config import (
    ConfigError,
    deep_set,
    load_experiment_spec,
    load_yaml,
    merge_dicts,
    now_tag,
    save_json,
    save_yaml,
    short_hash,
)

# Backward-compatible alias
merge_base_scenario = merge_dicts

__all__ = [
    "ConfigError",
    "deep_set",
    "load_experiment_spec",
    "load_yaml",
    "merge_dicts",
    "merge_base_scenario",
    "now_tag",
    "save_json",
    "save_yaml",
    "short_hash",
]
