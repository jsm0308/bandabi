# Bandabi

서울시 장애인 체육시설 이동을 가정한 셔틀 수요·배차·경로 실험 파이프라인입니다. 설정 파일 하나로 시나리오와 알고리즘 변형을 반복 실행하고, 실험별 KPI와 경로 결과를 같은 형식으로 남깁니다.

## 무엇을 검증하는 프로젝트인가

장애인 체육 프로그램은 이용자의 위치와 이동 지원 요구가 제각각입니다. Bandabi는 다음 질문을 재현 가능한 시뮬레이션으로 바꿉니다.

- 휠체어 이용자를 포함한 요청을 한정된 차량에 어떻게 배정할 것인가
- 배차·클러스터링·경로 개선 방식에 따라 정시 도착률과 이동시간이 얼마나 달라지는가
- 수요와 도로 시간의 불확실성이 커져도 같은 방식이 유지되는가

## 현재 버전에서 달라진 점

초기 버전은 한 번 실행해 경로 지도를 만드는 프로토타입이었습니다. 현재 버전은 실험을 비교하고 다시 실행할 수 있도록 구조를 바꿨습니다.

| 초기 프로토타입 | 현재 Bandabi |
| --- | --- |
| 코드 내부에서 조건 변경 | YAML 설정으로 기준·시나리오·스윕 분리 |
| 단일 경로 결과 | 변형별 leaderboard와 KPI 생성 |
| 결과 파일 형식이 고정되지 않음 | events, routes, metrics 계약 명시 |
| 휴리스틱 구현 확인 중심 | 정시 도착률·대기·이동시간 비교 중심 |

초기 구현은 [legacy](legacy) 폴더에 보존했습니다.

## 빠른 실행

Python 3.10 이상에서 의존성을 설치한 뒤 실행합니다.

~~~bash
pip install -e .
python -m bandabi \
  --base configs/base.yaml \
  --scenario configs/scenarios/seoul_allgu_v1.yaml \
  --sweep configs/sweeps/phase1_time_mult.yaml
~~~

설치한 명령으로도 같은 작업을 실행할 수 있습니다.

~~~bash
bandabi-run \
  --base configs/base.yaml \
  --scenario configs/scenarios/seoul_allgu_v1.yaml \
  --sweep configs/sweeps/phase1_time_mult.yaml
~~~

## 산출물 계약

각 실험은 runs/<exp_tag>/ 아래에 저장됩니다.

- leaderboard.csv: 변형별 KPI 요약
- <variant>/config_resolved.yaml: 실제 적용된 최종 설정
- <variant>/events.csv: 요청 단위 약속·실제 시간
- <variant>/routes.csv: 차량별 경로와 시간
- <variant>/metrics.csv: 단일 변형 KPI

자세한 데이터 형식은 [data_contract.md](docs/data_contract.md)와 [route_stop_v1.md](docs/contracts/route_stop_v1.md)에 정리했습니다.

## 코드 구조

- bandabi/: 현재 코어 패키지와 CLI
- configs/: 기준 설정, 시나리오, 알고리즘 스윕
- routing/: constructive, local search, tabu, genetic 모듈
- scripts/: 도로 그래프·정류장·지도·엣지 케이스 생성
- apps/dev_ui/: 실험 결과를 확인하는 개발 UI
- tests/: 파이프라인 스모크 테스트
- legacy/: 초기 경로 최적화 프로토타입

## 검증

~~~bash
pytest
~~~

CI에서도 같은 스모크 테스트를 실행합니다. 공개 저장소에는 가상환경, 실행 캐시, SQLite 개발 DB와 생성된 run 결과를 포함하지 않습니다.

## 프로젝트 이력

초기 경로 최적화 프로토타입을 바탕으로 2026년에 설정 기반 실험 파이프라인과 결과 계약을 추가했습니다. 2026년 8월에는 bandabi와 bandabi_v1으로 나뉘어 있던 공개 저장소를 현재 구조로 정리하고, 가상환경 8천여 파일과 생성 산출물을 Git 추적에서 제거했습니다. 정리 작업에는 Codex를 사용했습니다.
