# Data Contract (runs/ 산출물 스키마)

> 목표: Dev UI / 분석 스크립트가 **runs 폴더만 보고도** 깨지지 않게 하기.

## 폴더 구조

```
runs/
  <exp_id>/
    leaderboard.csv
    <variant_id>/
      config_resolved.yaml
      metrics.csv
      events.csv
      routes.csv
      map_data.json        # (신규) 지도용 요약
      map.html             # (신규) 바로 열어보는 시각화
```

## leaderboard.csv (exp 레벨)

- 각 variant를 한 줄로 요약한 결과 테이블
- 최소 컬럼
  - `variant`
  - KPI 컬럼들: `pickup_late_p95`, `center_late_p95`, `ride_time_p95`, `vehicles_used`, `total_travel_time_min`, `runtime_total_sec` 등

## config_resolved.yaml (variant 레벨)

- 실험 실행 시점의 설정을 **완전히 resolve**한 스냅샷
- 재현 가능성의 핵심

## metrics.csv (variant 레벨)

- `metrics`라는 한 row 테이블(키-값)
- KPI 계산 결과를 저장

## routes.csv (variant 레벨)

- 차량별 route 요약
- 주요 컬럼(예시)
  - `vehicle_id`, `center_id`, `timeslot`, `bus_type`
  - `route_points` : 노드 인덱스 열(0=센터, 1..=pickup)
  - `route_time_min`, `total_distance_km`, `n_requests`
  - `stops_json` : 지도 시각화용 stop 리스트(JSON 문자열)

## events.csv (variant 레벨)

- 요청(승객) 이벤트 단위 로그
- 주요 컬럼(예시)
  - `vehicle_id`, `center_id`, `timeslot`, `bus_type`
  - `request_id`
  - `pickup_scheduled_min`, `pickup_actual_min`, `pickup_late_min`
  - `center_arrival_scheduled_min`, `center_arrival_actual_min`, `center_late_min`
  - `ride_time_min`
  - (신규) `node_idx`, `stop_seq`, `pickup_lat`, `pickup_lon`, `center_lat`, `center_lon`

## map_data.json / map.html (variant 레벨)

- `map_data.json`
  - `vehicles: [...]`
  - 각 차량의 `coords: [[lat, lon], ...]` 를 포함
- `map.html`
  - Leaflet 기반, 로컬에서 바로 열어 route를 눈으로 확인 가능

---

## 호환성 규칙

- **컬럼 추가는 허용(Backward compatible)**
- 컬럼 삭제/이름 변경은 **major breaking change**로 취급하고, UI/스크립트 동시 수정 필요
