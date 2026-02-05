# routes.csv (stop-level) v1

목적: Dev UI Map에서 "vehicle_id + stop_seq"로 정류장(Stop)을 정확히 찾아 하이라이트하기 위함.

## 필수 컬럼 (7)
| column | type | example | meaning |
|---|---:|---|---|
| vehicle_id | str | v12 | 차량 식별자 |
| stop_seq | int | 0 | 방문 순서(차량별 0..N-1) |
| stop_type | str | depot/pickup/dropoff/center | 정류장 유형 |
| request_ids | str | r12;r98 | 이 정류장에 묶인 요청들(없으면 빈 문자열) |
| lat | float | 37.498 | 위도 |
| lon | float | 127.027 | 경도 |
| timeslot | str | 08:30 | (선택처럼 보이지만, 디버깅에 너무 유용해서 v1에 포함 권장) |

NOTE:
- request_ids는 세미콜론(;) join
- depot/center는 request_ids=""
- stop_seq는 정렬로 만들지 말고 “실제 방문 순서”대로 append하며 증가
