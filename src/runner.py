# runner.py
# (입구) scenario+sweep -> runs 생성 + leaderboard.csv 생성
import os
import pandas as pd

from .io_utils import load_yaml, merge_base_scenario, deep_set, ensure_dir, now_tag, short_hash, save_yaml
from .pipeline import run as run_pipeline
print("[RUNNER] started")

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="configs/base.yaml")
    p.add_argument("--scenario", default="configs/scenarios/seoul_allgu_v1.yaml")
    p.add_argument("--sweep", default="configs/sweeps/phase1_time_mult.yaml")
    args = p.parse_args()

    base = load_yaml(args.base)
    scen = load_yaml(args.scenario)
    sweep = load_yaml(args.sweep)

    cfg0 = merge_base_scenario(base, scen)

    print("[RUNNER] start")
    print("[RUNNER] base:", args.base)
    print("[RUNNER] scenario:", args.scenario)
    print("[RUNNER] sweep:", args.sweep)

    exp_tag = f"{sweep.get('exp_name','exp')}_{now_tag()}"
    exp_dir = os.path.join(cfg0["paths"]["run_root"], exp_tag)
    ensure_dir(exp_dir)
    print("[RUNNER] exp_dir:", exp_dir)


    rows = []
    for v in sweep["values"]:
        cfg = dict(cfg0)  # shallow OK since deep_set only touches nested dict; but safer:
        import copy
        cfg = copy.deepcopy(cfg0)
        deep_set(cfg, sweep["param_path"], v)

        var_id = f"v_{v:.2f}"
        out_dir = os.path.join(exp_dir, var_id)
        ensure_dir(out_dir)

        # 저장: 최종 적용된 config
        save_yaml(cfg, os.path.join(out_dir, "config_resolved.yaml"))

        kpis = run_pipeline(cfg, out_dir)
        kpis["variant"] = var_id
        kpis["param_path"] = sweep["param_path"]
        kpis["param_value"] = v
        rows.append(kpis)

    lb = pd.DataFrame(rows)
    # KPI 중 핵심만 위로
    key_cols = ["variant","param_path","param_value",
                "pickup_late_mean","pickup_late_p95","pickup_on_time_rate",
                "center_late_mean","center_late_p95","center_on_time_rate",
                "ride_time_mean","ride_time_p95",
                "vehicles_used","total_travel_time","runtime_total_sec"]
    for c in key_cols:
        if c not in lb.columns:
            lb[c] = None
    lb = lb[key_cols + [c for c in lb.columns if c not in key_cols]]

    lb.to_csv(os.path.join(exp_dir, "leaderboard.csv"), index=False, encoding="utf-8-sig")
    print(f"[DONE] {exp_dir}/leaderboard.csv 생성 완료")

if __name__ == "__main__":
    main()

