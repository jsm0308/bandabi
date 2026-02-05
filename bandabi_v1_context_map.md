# Bandabi V1 Project Context Map

> **File Name**: `bandabi_v1_context_map.md`
> **Purpose**: AI 에이전트(Cursor, Windsurf, Trae 등)를 위한 프로젝트 구조 및 규약 정의서
> **Last Updated**: 2026-02-06

## 1. Project Architecture (Map)

### 📂 Directory Structure
bandabi_v1/
├── .ai/ # AI Agent Instructions (Rules)
├── apps/
│   └── dev_ui/ # [Frontend] Next.js Dashboard for experiment viz
│       ├── src/lib/ # Data types & API Clients
│       └── components/ # UI Components
├── bandabi/ # [Core Engine] Python Simulation Package
│   ├── routing/ # TSP & Path finding logic
│   ├── cli.py # Entry point
│   ├── config.py # Configuration Schema (Spec)
│   ├── demand.py # Demand generation
│   ├── pipeline.py # Main Simulation Loop
│   └── road_network.py # OSMnx Wrapper
├── configs/ # YAML Scenarios & Sweeps
├── scripts/ # Automation Harness (verify.sh, loop.sh)
└── pyproject.toml # Python Dependencies & Tool Config


## 2. Core Harness (The Law)

### 🚨 Verification Rules
모든 코드는 커밋 전 다음 스크립트를 통과해야 함.
- **Execution**: `./scripts/verify.sh` (Mac/Linux) or `verify.ps1` (Win)
- **Sequence**:
  1. `Lint` (ESLint + Ruff)
  2. `Typecheck` (TSC + Mypy/Pyright)
  3. `Test` (Vitest + Pytest)

### 🤖 AI Agent Behavior (.ai)
- **Refactor Loop**: 검증 실패 시 `scripts/ai_refactor_loop.sh`를 통해 스스로 수정 시도.
- **Context**: 대용량 파일은 읽지 말고 이 맵 파일(`bandabi_v1_context_map.md`)을 먼저 참조할 것.

## 3. Key Data Contracts (Interface)

### 🐍 Backend Models (Python)
**`bandabi/config.py`**
- `ExperimentSpec`: 실험 정의 (exp_name, param_path, values)
- `DemandConfig`: 수요 생성 설정 (wheel_ratio, radius_km)

**`bandabi/pipeline.py`**
- **Input**: `cfg` (Dict), `out_dir` (Path)
- **Output**: `KPIs` (Dict), `events.csv`, `routes.csv`, `map_data.json`

### ⚛️ Frontend Types (TypeScript)
**`apps/dev_ui/src/lib/runs.ts`**
- `ExperimentInfo`: 실험 메타데이터 (ID, Variants 목록)
- `VariantArtifacts`: 시각화 데이터 (Metrics, Routes, GeoJSON)

---

## 4. Environment Configurations (Critical)

### ⚙️ Python Config (`pyproject.toml`)
```toml
# PASTE CONTENT HERE
⚙️ TypeScript Config (tsconfig.json)
JSON
// PASTE CONTENT HERE