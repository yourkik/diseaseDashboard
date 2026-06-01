from fastapi import FastAPI
from dotenv import load_dotenv
import os

# 서비스 레이어 임포트
from app.services.ingestion import fetch_kdca_stats, get_integrated_news, fetch_kdca_disease_contents

# .env 환경변수 로드
load_dotenv()

app = FastAPI(
    title="Disease Dashboard API",
    description="감염병 수집, RAG 전처리 및 프론트엔드 서빙을 위한 백엔드 API",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Sentinel Dashboard API is running."}

@app.get("/api/health")
def health_check():
    """백엔드 서버 및 DB 연결 상태 헬스체크용 엔드포인트"""
    return {"status": "ok", "db_connected": False} # DB 연동 후 True로 변경 예정

@app.get("/api/data/stats")
def get_disease_stats():
    """공공데이터포털 기반 확진자 통계 반환"""
    data = fetch_kdca_stats()
    return data

@app.get("/api/data/news")
def get_disease_news():
    """Bing API 및 GDELT API 기반 감염병 통합 뉴스 반환"""
    data = get_integrated_news()
    return data

@app.get("/api/data/contents")
def get_disease_contents():
    """질병관리청 건강정보/감염병 콘텐츠 반환"""
    data = fetch_kdca_disease_contents()
    return data

