from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd


def _ensure_routes_stops(variant_dir: Path) -> Path:
    # routes_stops.csv가 없으면 routes.csv(stops_json)로 만들도록 의존
    stops = variant_dir / "routes_stops.csv"
    if stops.exists():
        return stops

    # 동일 폴더에 build_routes_stops.py가 이미 만들어준다고 가정하지만,
    # 안전하게 없으면 여기서 fallback은 안 함(원하면 여기서도 생성 로직 추가 가능)
    return stops


def _severity(events: pd.DataFrame, criterion: str) -> pd.Series:
    # 이벤트 단위 severity 계산
    if events.empty:
        return pd.Series(dtype=float)

    if criterion == "center_late":
        s = (events["center_actual_min"] - events["center_promise_min"]).astype(float)
        return s.where(s > 0, 0.0)

    if criterion == "pickup_late":
        s = (events["pickup_actual_min"] - events["pickup_promise_min"]).astype(float)
        return s.where(s > 0, 0.0)

    if criterion == "ride_time":
        # “승차 시간이 긴 요청”
        return events["ride_time_min"].astype(float)

    raise ValueError(f"Unknown criterion: {criterion}")


def build_edge_cases_for_variant(variant_dir: Path, *, criterion: str, top_n: int) -> Path:
    events_csv = variant_dir / "events.csv"
    out_json = variant_dir / "edge_cases.json"
    stops_csv = _ensure_routes_stops(variant_dir)

    if not events_csv.exists():
        raise FileNotFoundError(events_csv)

    ev = pd.read_csv(events_csv)
    if ev.empty:
        payload = {"version": 1, "criterion": criterion, "top_n": top_n, "items": []}
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_json

    ev = ev.copy()
    ev["severity"] = _severity(ev, criterion)

    top = ev.sort_values("severity", ascending=False).head(top_n)

    # 지도 점프용 보강: vehicle_id + stop_seq로 stop 좌표/타입 merge
    if stops_csv.exists():
        st = pd.read_csv(stops_csv)
        if not st.empty:
            top = top.merge(
                st[["vehicle_id", "stop_seq", "stop_type", "lat", "lon"]],
                on=["vehicle_id", "stop_seq"],
                how="left",
            )
    else:
        top["stop_type"] = "pickup"
        top["lat"] = top.get("pickup_lat")
        top["lon"] = top.get("pickup_lon")

    items = []
    for rank, row in enumerate(top.itertuples(index=False), start=1):
        d = row._asdict()
        items.append(
            {
                "rank": rank,
                "severity": float(d.get("severity", 0.0)),
                "vehicle_id": str(d.get("vehicle_id", "")),
                "stop_seq": int(d.get("stop_seq", -1)),
                "stop_type": str(d.get("stop_type", "")) or "pickup",
                "request_ids": [str(d.get("request_id", ""))],
                "reason": criterion,
                "map_hint": {
                    "lat": None if pd.isna(d.get("lat")) else float(d.get("lat")),
                    "lon": None if pd.isna(d.get("lon")) else float(d.get("lon")),
                },
            }
        )

    payload = {"version": 1, "criterion": criterion, "top_n": top_n, "items": items}
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_json


def iter_experiments(runs_dir: Path, prefix: str | None) -> list[Path]:
    exps = [p for p in runs_dir.iterdir() if p.is_dir() and not p.name.startswith("_")]
    if prefix:
        exps = [p for p in exps if p.name.startswith(prefix)]
    return sorted(exps)


def iter_variants(exp_dir: Path) -> list[Path]:
    return sorted([p for p in exp_dir.iterdir() if p.is_dir() and p.name.startswith("v_")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", default="runs")
    ap.add_argument("--exp-tag", default="", help="특정 exp만")
    ap.add_argument("--prefix", default="base18__", help="exp-tag 비었을 때 처리할 exp prefix")
    ap.add_argument("--criterion", default="center_late", choices=["center_late", "pickup_late", "ride_time"])
    ap.add_argument("--top-n", type=int, default=30)
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        raise FileNotFoundError(runs_dir)

    if args.exp_tag:
        exp_dirs = [runs_dir / args.exp_tag]
    else:
        exp_dirs = iter_experiments(runs_dir, args.prefix if args.prefix else None)

    total = 0
    written = 0

    for exp_dir in exp_dirs:
        if not exp_dir.exists():
            continue
        for vdir in iter_variants(exp_dir):
            total += 1
            try:
                out = build_edge_cases_for_variant(vdir, criterion=args.criterion, top_n=args.top_n)
                print(f"[ok] {out}")
                written += 1
            except Exception as e:
                print(f"[skip] {vdir} ({e})")

    print(f"[done] variants processed={total}, edge_cases written={written}")


if __name__ == "__main__":
    main()
