from fastapi import APIRouter, HTTPException
from typing import Optional
from app.services.kdca_service import fetch_kdca_region_status, fetch_kdca_period_spread

def safe_int(val):
    if not val: return 0
    if isinstance(val, str):
        val = val.replace(",", "")
    try: return int(val)
    except: return 0

def safe_float(val):
    if not val: return 0.0
    if isinstance(val, str):
        val = val.replace(",", "")
    try: return float(val)
    except: return 0.0

router = APIRouter(prefix="/api/stats/map", tags=["Map Stats"])

@router.get("/status")
def get_map_status(disease: str, year: str = "2023"):
    """
    현황 파악 (Choropleth Map): 특정 질병의 각 지역별 확진자 수와 10만명당 발생률을 반환합니다.
    """
    try:
        # 발생수 데이터 수집
        count_data = fetch_kdca_region_status(year=year, search_type="1")
        # 10만명당 발생률 데이터 수집
        rate_data = fetch_kdca_region_status(year=year, search_type="2")
        
        count_items = count_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        rate_items = rate_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        # 프론트엔드가 쓰기 편하게 데이터 병합
        result = {}
        
        for item in count_items:
            if item.get("icdNm") == disease and item.get("sidoCd") != "00":
                sido = item.get("sidoNm")
                result[sido] = {
                    "region": sido,
                    "count": safe_int(item.get("resultVal", 0))
                }
                
        for item in rate_items:
            if item.get("icdNm") == disease and item.get("sidoCd") != "00":
                sido = item.get("sidoNm")
                if sido in result:
                    result[sido]["rate"] = safe_float(item.get("resultVal", 0))
                    
        return list(result.values())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spread")
def get_map_spread(disease: str, year: str = "2023", period_type: str = "2"):
    """
    전파 지도 (Time-series Animation): 특정 질병의 월별(2)/주별(3) 확진자 추이를 반환합니다.
    """
    try:
        spread_data = fetch_kdca_period_spread(start_year=year, end_year=year, period_type=period_type)
        
        # 프론트엔드가 Timeline을 그리기 쉽게 { "2023년 01월": [지역별 데이터], ... } 형태로 그룹핑
        timeline_result = {}
        
        for item in spread_data:
            if item.get("icdNm") == disease:
                period = item.get("period") # "2023년 01월"
                if period not in timeline_result:
                    timeline_result[period] = []
                    
                timeline_result[period].append({
                    "region": item.get("sidoNm"),
                    "count": safe_int(item.get("resultVal", 0))
                })
                
        # 기간별(키)로 정렬하여 반환
        sorted_timeline = {k: timeline_result[k] for k in sorted(timeline_result.keys())}
        return sorted_timeline
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
