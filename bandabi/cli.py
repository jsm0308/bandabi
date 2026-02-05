from __future__ import annotations

import argparse
import os
import re
from copy import deepcopy
from typing import Any, List

import pandas as pd

from .config import deep_set, load_experiment_spec, load_yaml, merge_dicts, now_tag, save_yaml
from .pipeline import run as run_pipeline


LEADERBOARD_KEY_COLS = [
    "variant",
    "param_path",
    "param_value",
    "pickup_late_mean",
    "pickup_late_p95",
    "pickup_on_time_rate",
    "center_late_mean",
    "center_late_p95",
    "center_on_time_rate",
    "ride_time_mean",
    "ride_time_p95",
    "vehicles_used",
    "total_travel_time",
    "runtime_total_sec",
    "pickup_late_max",
    "center_late_max",
    "ride_time_max",
    "total_travel_time_min",
]


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9_\-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "x"


def _fmt_variant_id(v: Any) -> str:
    # 기존 v_0.90 스타일 유지 + 문자열/None도 안전 처리
    if v is None:
        return "v_none"
    if isinstance(v, bool):
        return f"v_{str(v).lower()}"
    if isinstance(v, int):
        return f"v_{v:d}"
    if isinstance(v, float):
        return f"v_{v:.2f}"
    return f"v_{_slug(str(v))}"


def main(argv: List[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="bandabi-run", description="Run Bandabi simulation sweeps")
    p.add_argument("--base", action="append", default=["configs/base.yaml"])
    p.add_argument("--scenario", default="configs/scenarios/seoul_allgu_v1.yaml")
    p.add_argument("--sweep", default="configs/sweeps/phase1_time_mult.yaml")
    p.add_argument("--exp-tag", default=None)
    args = p.parse_args(argv)

    bases = [load_yaml(b) for b in args.base]
    base_merged = {}
    for b in bases:
        base_merged = merge_dicts(base_merged, b)

    scen = load_yaml(args.scenario)
    sweep = load_experiment_spec(args.sweep)

    cfg0 = merge_dicts(base_merged, scen)

    run_root = cfg0.get("paths", {}).get("run_root", "runs")
    exp_tag = args.exp_tag or f"{sweep.exp_name}_{now_tag()}"
    exp_dir = os.path.join(run_root, exp_tag)
    os.makedirs(exp_dir, exist_ok=True)

    rows = []
    for v in sweep.values:
        cfg = deepcopy(cfg0)
        deep_set(cfg, sweep.param_path, v)

        var_id = _fmt_variant_id(v)
        out_dir = os.path.join(exp_dir, var_id)
        os.makedirs(out_dir, exist_ok=True)

        save_yaml(cfg, os.path.join(out_dir, "config_resolved.yaml"))

        kpis = run_pipeline(cfg, out_dir)
        kpis["variant"] = var_id
        kpis["param_path"] = sweep.param_path
        kpis["param_value"] = "" if v is None else str(v)  # ✅ UI/CSV에서 안전
        rows.append(kpis)

    lb = pd.DataFrame(rows)

    for c in LEADERBOARD_KEY_COLS:
        if c not in lb.columns:
            lb[c] = None
    lb = lb[LEADERBOARD_KEY_COLS + [c for c in lb.columns if c not in LEADERBOARD_KEY_COLS]]

    lb.to_csv(os.path.join(exp_dir, "leaderboard.csv"), index=False, encoding="utf-8-sig")
    print(f"[DONE] {os.path.join(exp_dir, 'leaderboard.csv')} 생성 완료")


if __name__ == "__main__":
    main()
