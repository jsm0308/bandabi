# src/io_utils.py
# 역할: (1) yaml/json 로드/세이브 (2) config 병합 (3) config 내부 값(경로) 덮어쓰기
# runner.py가 실험을 돌릴 때 매번 사용하는 유틸 모음

import os
import json
import yaml
import hashlib
import datetime
from copy import deepcopy


def load_yaml(path: str) -> dict:
    """YAML 파일을 dict로 로드"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(obj: dict, path: str) -> None:
    """dict를 YAML로 저장"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(obj, f, allow_unicode=True, sort_keys=False)


def save_json(obj, path: str) -> None:
    """객체를 JSON으로 저장"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def ensure_dir(path: str) -> None:
    """폴더 없으면 생성"""
    os.makedirs(path, exist_ok=True)


def deep_set(cfg: dict, path: str, value):
    """
    cfg 내부를 점(.) 경로로 찾아가서 값을 덮어쓴다.
    예: deep_set(cfg, "time_model.speed_multiplier", 1.1)
    """
    keys = path.split(".")
    cur = cfg
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


def now_tag() -> str:
    """runs 폴더 이름에 붙일 시간 태그"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def short_hash(obj: dict) -> str:
    """설정 dict의 해시(짧게)"""
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:8]


def merge_base_scenario(base: dict, scenario: dict) -> dict:
    """
    base.yaml + scenario.yaml 병합
    - scenario가 base를 덮어쓴다(override)
    """
    out = deepcopy(base)

    def rec(a, b):
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(a.get(k), dict):
                rec(a[k], v)
            else:
                a[k] = v

    rec(out, scenario)
    return out
