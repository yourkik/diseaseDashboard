# 감염병 대시보드 프로젝트 사용 가이드 (User Guide)

본 문서는 질병관리청 및 통합 감염병 데이터를 다루는 **감염병 대시보드 프로젝트**의 실행 및 사용 방법을 안내합니다. 프로젝트는 크게 세 부분(EDA 스크립트, Backend, Frontend)으로 나뉘어져 있습니다.

---

## 1. EDA (탐색적 데이터 분석) 파트
Azure 연결 없이 질병관리청 서버 등에서 데이터를 바로 추출하고 분석해볼 수 있는 독립적인 스크립트입니다.

1. **사전 준비**: 
   - `backend/.env` 파일에 `KDCA_CONTENT_TOKEN` (질병관리청 건강정보 토큰) 등의 키를 입력합니다.
   - 패키지 설치: `backend` 폴더에서 `pip install -r requirements.txt` 실행
2. **데이터 추출 실행**: 
   ```bash
   cd backend
   python eda/eda_script.py
   ```
3. **결과 확인**:
   - `backend/eda/data/` 폴더 내에 데이터가 CSV로 추출됩니다. (`kdca_contents.csv`, `kdca_stats.csv`, `integrated_news.csv` 등)
   - 이 CSV 데이터를 활용하여 Jupyter Notebook 등에서 머신러닝이나 추가 분석을 자유롭게 진행할 수 있습니다.

---

## 2. Backend (FastAPI 서버)
데이터를 가져와 프론트엔드로 전달해주는 역할을 하는 백엔드 서버입니다.

1. **사전 준비**:
   - 패키지 설치: `pip install -r requirements.txt`
   - `.env` 파일 세팅 확인
2. **서버 실행**:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
3. **API 명세서 확인**:
   - 브라우저에서 `http://127.0.0.1:8000/docs` 에 접속하시면 사용 가능한 API 목록을 쉽게 테스트할 수 있습니다.

---

## 3. Frontend (Next.js 웹 애플리케이션)
사용자에게 보여지는 대시보드 화면입니다. 백엔드와 연동하여 동작합니다.

1. **사전 준비**:
   - 패키지 설치: `frontend` 폴더에서 `npm install` 실행
2. **개발 서버 실행**:
   ```bash
   cd frontend
   npm run dev
   ```
3. **웹 접속**:
   - 브라우저에서 `http://localhost:3000` 에 접속하여 화면을 확인합니다.
   - `KdcaContents.js` 컴포넌트 등을 통해 백엔드(`/api/data/contents`)의 데이터를 불러와 보여줄 수 있습니다.

---

## 💡 개발 팁 (Troubleshooting)

- **백엔드 SSL 에러 발생 시**: 파이썬의 보안 정책 때문에 질병관리청 구형 서버와 충돌하는 경우가 있습니다. 이를 방지하기 위해 `backend/app/services/ingestion.py` 에 `CustomSSLAdapter`가 이미 적용되어 있으니 코드를 참고해 주세요.
- **깃(Git) 업로드 방지**: 개인 정보인 `.env`나 용량이 큰 `eda/data/` 내의 csv 파일들은 `.gitignore`에 등록되어 자동으로 GitHub에 올라가지 않도록 설정되어 있습니다. 안심하고 데이터를 추출하세요!
