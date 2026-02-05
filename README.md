# Bandabi

파일 기반 실험 파이프라인 (simulation → runs/<exp>/... 결과물 생성).

## 빠른 실행

```bash
# sweep 실행
python -m bandabi --base configs/base.yaml \
  --scenario configs/scenarios/seoul_allgu_v1.yaml \
  --sweep configs/sweeps/phase1_time_mult.yaml

# 또는 스크립트로
bandabi-run --base configs/base.yaml --scenario configs/scenarios/seoul_allgu_v1.yaml --sweep configs/sweeps/phase1_time_mult.yaml
```

## 산출물(file contract)

각 실험은 아래 형태로 저장됩니다.

- `runs/<exp_tag>/leaderboard.csv` : variant별 KPI 요약
- `runs/<exp_tag>/<variant>/config_resolved.yaml` : 해당 variant의 최종 config
- `runs/<exp_tag>/<variant>/events.csv` : 요청 단위 이벤트(약속/실제 시간)
- `runs/<exp_tag>/<variant>/routes.csv` : 차량별 경로/시간 요약
- `runs/<exp_tag>/<variant>/metrics.csv` : 단일 variant KPI

## 코드 구조

- `bandabi/` : 현재 코어 패키지 (권장)
- `src/` : 레거시 호환 레이어 (기존 커맨드 유지용)
