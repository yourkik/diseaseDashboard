from fastapi import APIRouter, HTTPException
from app.services.ingestion import get_integrated_news

router = APIRouter(prefix="/api/news", tags=["News"])

@router.get("/")
def get_disease_news(disease: str):
    """
    특정 질병에 대한 최신 뉴스(Bing Search API 기반)를 가져옵니다.
    """
    try:
        # 뉴스 검색 쿼리: 질병명 + 관련 키워드
        query = f"{disease} (감염 OR 바이러스 OR 확진 OR 예방)"
        gdelt_query = f"{disease} OR virus OR disease"
        
        # ingestion.py의 get_integrated_news 함수를 활용하여 Bing 실패 시 GDELT로 Fallback
        news_data = get_integrated_news(query=query, gdelt_query=gdelt_query)
        
        news_items = news_data.get("value", [])
        
        # 프론트엔드에서 쓰기 편하게 데이터 정제
        formatted_news = []
        for item in news_items:
            formatted_news.append({
                "title": item.get("name"),
                "url": item.get("url"),
                "description": item.get("description"),
                "source": item.get("provider", [{}])[0].get("name", "Bing News"),
                "date": item.get("datePublished")
            })
            
        return formatted_news
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
