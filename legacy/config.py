# config.py 내용 여기 붙여넣기
# config.py

import os

# 센터 CSV 경로 (Colab 기준 예시)
CENTERS_CSV = "centers.xlsx"

# 결과 저장 폴더
RESULT_DIR = "results"
os.makedirs(RESULT_DIR, exist_ok=True)

# 더미 수요 설정
DUMMY_CFG = {
    "n_requests": 120,            # 전체 승객 수
    "wheel_ratio": 0.25,          # 휠체어 비율
    "timeslots": ["10:00", "12:00", "16:00", "18:00"],
    "seed": 42,
    "radius_min_km": 0.5,
    "radius_max_km": 3.0,
}

# 버스 설정
GEN_CAPACITY = 10        # 일반차량 1대당 정원
WC_CAPACITY = 4          # 휠체어 차량 1대당 정원
MAX_GEN_PER_SLOT = 3     # 센터-타임슬롯당 GEN 최대 대수
MAX_WC_PER_SLOT = 2      # 센터-타임슬롯당 WC 최대 대수

# OSM 그래프 범위 (서울 전체 말고 여유 bbox 사용 가능)
OSM_PLACE = "Seoul, South Korea"

# 결과 HTML 파일 이름
MAP_HTML = os.path.join(RESULT_DIR, "bandabi_minimal_map.html")
