from fastapi import APIRouter, HTTPException
from app.services.disease_agent import analyze_disease_risk_with_grounding
from app.services.cache_manager import get_news_cache, update_news_cache

router = APIRouter(prefix="/api/news", tags=["News"])

@router.get("/")
def get_disease_news(disease: str):
    """
    LLM(Azure AI Agent)의 답변을 생성할 때 참고한 문서(Citations) 데이터를 추출하여 뉴스 피드로 제공합니다.
    속도 개선을 위해 캐싱을 사용합니다.
    """
    try:
        # 1. 캐시 확인
        cached = get_news_cache(disease)
        if cached and "data" in cached:
            # 캐시가 있으면 즉시 반환
            return cached["data"]
            
        # 2. 캐시가 없으면 LLM 호출 (약 10~15초 소요)
        agent_result = analyze_disease_risk_with_grounding(disease_keyword=disease)
        
        if "error" in agent_result:
            # 에러 발생 시 빈 배열 반환하여 프론트엔드가 죽지 않게 처리
            return []
            
        citations = agent_result.get("citations", [])
        
        # 3. 프론트엔드 포맷에 맞게 변환
        formatted_news = []
        for citation in citations:
            formatted_news.append({
                "title": citation.get("title", "관련 문서"),
                "url": citation.get("url", "#"),
                "description": "AI 에이전트가 답변을 위해 참고한 핵심 문서입니다.",
                "source": "AI Grounding Search",
                "date": "최신"
            })
            
        # 4. 캐시 저장
        update_news_cache(disease, formatted_news)
        
        return formatted_news
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
