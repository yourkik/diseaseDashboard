from fastapi import APIRouter, Query
from app.services.cosmos_service import get_latest_news_from_cosmos, get_all_disease_stats, get_disease_stats_by_region

router = APIRouter(
    prefix="/api/ews",
    tags=["Early Warning System (EWS)"]
)

@router.get("/status")
def get_ews_status(sido_code: str = None):
    """
    조기 경보 시스템(EWS) 데이터를 가져옵니다.
    sido_code가 주어지면 특정 지역의 데이터만 반환하고, 없으면 전국 데이터를 반환합니다.
    """
    if sido_code:
        data = get_disease_stats_by_region(sido_code)
        if data:
            return data
        return {"error": "해당 지역의 EWS 데이터를 찾을 수 없습니다."}
    
    return get_all_disease_stats()

@router.get("/news")
def get_ews_news(disease: str = Query(None, description="질병명 필터"), 
                 region: str = Query(None, description="지역명 필터"), 
                 limit: int = 5):
    """
    Cosmos DB에서 실시간 감염병 뉴스 데이터를 조회합니다.
    """
    items = get_latest_news_from_cosmos(disease=disease, region=region, limit=limit)
    return {"items": items}
