# 🦠 Epidemic Surveillance Dashboard (우리 동네 감염병 브리핑)

**AI 기반 실시간 감염병 확산 분석 및 지역별 위험도 지도 시각화 대시보드**입니다.
질병관리청(KDCA) 공공데이터포털의 정량적인 확진자 통계와, **Azure AI Agent (Bing Grounding)** 기반의 정성적인 최신 뉴스 분석 데이터를 하이브리드(Hybrid) 방식으로 결합하여 제공합니다.

---

## ✨ 핵심 기능 (Features)

1. **하이브리드 데이터 파이프라인 (Hybrid Data Aggregator)**
   - **정량 데이터**: 질병관리청 공공데이터 API를 통해 정확한 누적/일일 확진자 수를 수집합니다. (예: 코로나19)
   - **정성 데이터**: 통계가 미비한 질병(예: 독감, 뎅기열)의 경우, Azure AI Agent가 실시간 빙 검색(Bing Search) 뉴스를 바탕으로 지역별 위험도(High/Medium/Low)와 확산 방향을 추론합니다.
   - **유연한 렌더링**: 확진자 데이터 유무에 따라 지도 상에 보여줄 UI(버블 크기 및 색상)를 유동적으로 결정합니다.
2. **Azure Maps 기반 확산 시각화 (Interactive Map)**
   - **버블 마커 (Bubble Layer)**: 감염자 규모에 비례한 크기와 위험도 기반 색상(Red/Orange/Green)으로 지역별 위험을 직관적으로 표기합니다.
   - **확산 벡터 (Line Layer)**: AI가 분석한 지역 간 전파 방향(Spread Vectors)을 애니메이션 라인으로 시각화합니다.
3. **최신 RAG(Retrieval-Augmented Generation) 융합**
   - 최신 뉴스를 접지(Grounding)하여 AI 모델(GPT-4o)의 환각을 방지하고 신뢰도 높은 예방 행동 지침을 제공합니다.

---

## 🏗️ 시스템 아키텍처 (Architecture)

- **Frontend**: Next.js (React), Azure Maps SDK (웹 시각화)
- **Backend**: FastAPI (Python), Uvicorn (서버 구동)
- **AI & Cloud (Azure)**: 
  - Azure AI Foundry (AI Project, Agents API v1.0.0)
  - Azure OpenAI (`gpt-4o` 배포 모델)
  - Bing Search v7 (Grounding Tool)

---

## 🚀 시작하기 (Getting Started)

### 1. 환경 변수 설정
`backend/.env` 파일을 생성하고 아래 값들을 채워 넣습니다.
```env
# Azure AI Project 연동
PROJECT_ENDPOINT="https://[YOUR_ENDPOINT].services.ai.azure.com/api/projects/[YOUR_PROJECT_NAME]"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
BING_CONNECTION_NAME="GroundingBingSearch"

# 공공 데이터 연동 (옵션)
KDCA_API_KEY="your_api_key_here"
```
*(참고: Azure 리소스는 `DefaultAzureCredential`을 통해 로컬 Azure CLI `az login` 계정의 권한을 상속받습니다. 별도의 API Key 없이 보안이 유지됩니다.)*

### 2. 백엔드(Backend) 실행
FastAPI 서버를 구동합니다. 가상환경 내에 설치된 모듈을 안정적으로 실행하기 위해 모듈 방식으로 실행합니다.
```bash
cd backend
myenv\Scripts\activate
# Uvicorn 서버 실행 (포트: 8000)
python -m uvicorn app.main:app --reload
```

### 3. 프론트엔드(Frontend) 실행
Next.js 앱을 구동합니다.
```bash
cd frontend
npm install
npm run dev
```
이후 브라우저에서 `http://localhost:3000` 에 접속하여 대시보드를 확인합니다.

---

## 📂 프로젝트 구조 (Directory Structure)

```text
diseaseDashboard/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 진입점 및 API 라우팅 (CORS 포함)
│   │   └── services/
│   │       ├── disease_agent.py   # Azure AI Agent 생성 및 JSON 분석 로직
│   │       ├── map_aggregator.py  # 공공 API와 AI 데이터의 Hybrid 병합 로직
│   │       └── ingestion.py       # 공공데이터포털/GDELT 등 외부 데이터 수집
│   └── requirements.txt
└── frontend/
    ├── src/app/
    │   ├── page.js                # 메인 대시보드 UI (질병 드롭다운, 통계 요약)
    │   └── mapAzure.js            # Azure Maps 렌더링 및 데이터 Fetching 컴포넌트
    └── package.json
```

---

## 📝 라이선스 및 기여 (License & Contributing)

이 프로젝트는 Data School 3차 프로젝트(팀 5)의 결과물입니다. 
추가 기여를 원하시는 팀원분들은 Pull Request를 생성해 주시기 바랍니다!
