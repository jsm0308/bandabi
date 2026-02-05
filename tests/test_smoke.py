import os
from copy import deepcopy

import pandas as pd

from bandabi.config import load_yaml, merge_dicts, deep_set
from bandabi.pipeline import run


def test_pipeline_smoke(tmp_path):
    base = load_yaml("configs/base.yaml")
    scen = load_yaml("configs/scenarios/seoul_allgu_v1.yaml")
    cfg = merge_dicts(base, scen)

    # keep test fast
    cfg.setdefault("demand", {})
    cfg["demand"]["n_requests_per_timeslot"] = 4
    cfg.setdefault("sim", {})
    cfg["sim"]["travel_time_noise_sigma"] = 0.0

    out_dir = tmp_path / "run"
    kpis = run(cfg, str(out_dir))

    assert os.path.exists(out_dir / "events.csv")
    assert os.path.exists(out_dir / "routes.csv")
    assert os.path.exists(out_dir / "metrics.csv")

    m = pd.read_csv(out_dir / "metrics.csv")
    assert "pickup_on_time_rate" in m.columns
    assert 0.0 <= float(m.loc[0, "pickup_on_time_rate"]) <= 1.0
