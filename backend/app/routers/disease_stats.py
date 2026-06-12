from fastapi import APIRouter, HTTPException
from typing import Optional
from app.services.kdca_service import fetch_kdca_region_status, fetch_kdca_period_spread
from app.services.covid_service import fetch_covid_region_status, fetch_covid_period_spread
from app.services.ebola_service import fetch_ebola_region_status
from datetime import datetime

DISEASE_MAPPING = {
    "한타바이러스": "신증후군출혈열",
    "에볼라": "에볼라바이러스병",
    "코로나19": "코로나바이러스감염증-19" # 추후 코로나 전용 API 연동 전까지 대비
}

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
def get_map_status(disease: str, year: Optional[str] = None):
    """
    현황 파악 (Choropleth Map): 특정 질병의 각 지역별 확진자 수와 10만명당 발생률을 반환합니다.
    """
    try:
        # 질병명 매핑
        api_disease_name = DISEASE_MAPPING.get(disease, disease)
        
        # 년도가 주어지지 않으면 오늘 기준 연도 사용 (최근 데이터 목적)
        if not year:
            year = str(datetime.now().year)

        # 에볼라 분기
        if api_disease_name == "에볼라바이러스병":
            return fetch_ebola_region_status()

        # 코로나19의 경우 별도 서비스 라우팅
        if api_disease_name == "코로나바이러스감염증-19":
            count_data = fetch_covid_region_status(year=year)
            rate_data = count_data # 코로나 API에서 발생률 미제공 시 예외 처리
        else:
            # 발생수 데이터 수집
            count_data = fetch_kdca_region_status(year=year, search_type="1")
            # 10만명당 발생률 데이터 수집
            rate_data = fetch_kdca_region_status(year=year, search_type="2")
        
        count_items = count_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        rate_items = rate_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        # 프론트엔드가 쓰기 편하게 데이터 병합
        result = {}
        
        for item in count_items:
            if item.get("icdNm") == api_disease_name and item.get("sidoCd") != "00":
                sido = item.get("sidoNm")
                result[sido] = {
                    "region": sido,
                    "count": safe_int(item.get("resultVal", 0)),
                    "period": item.get("stdDay", f"{year}년 누적 데이터") # 코로나 API의 기준일자나 기본 연도 문자열 전달
                }
                
        for item in rate_items:
            if item.get("icdNm") == api_disease_name and item.get("sidoCd") != "00":
                sido = item.get("sidoNm")
                if sido in result:
                    result[sido]["rate"] = safe_float(item.get("resultVal", 0))
                    
        return list(result.values())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spread")
def get_map_spread(disease: str, year: Optional[str] = None, period_type: str = "2"):
    """
    전파 지도 (Time-series Animation): 특정 질병의 최근 12개월 추이를 반환합니다.
    """
    try:
        api_disease_name = DISEASE_MAPPING.get(disease, disease)
        
        if not year:
            current_year = datetime.now().year
        else:
            current_year = int(year)
            
        # 에볼라 분기: 확산 추이는 현재 JSON에 월별 시계열이 부족하므로 빈 딕셔너리 반환
        if api_disease_name == "에볼라바이러스병":
            return {}

        # 최근 데이터를 얻기 위해 올해와 작년 데이터를 모두 가져옴
        spread_data = []
        # 코로나19인 경우 분기
        if api_disease_name == "코로나바이러스감염증-19":
            spread_data = fetch_covid_period_spread(start_year=str(current_year-1), end_year=str(current_year))
        else:
            spread_data.extend(fetch_kdca_period_spread(start_year=str(current_year-1), end_year=str(current_year-1), period_type=period_type))
            spread_data.extend(fetch_kdca_period_spread(start_year=str(current_year), end_year=str(current_year), period_type=period_type))
        
        timeline_result = {}
        
        for item in spread_data:
            if item.get("icdNm") == api_disease_name:
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

@router.get("/total")
def get_total_stats(disease: str, year: Optional[str] = None):
    """
    전국 통합 지표: 특정 질병의 전국 누적 확진자 수, 10만 명당 발생률, 월별 발생 추이를 반환합니다.
    """
    try:
        api_disease_name = DISEASE_MAPPING.get(disease, disease)
        
        if not year:
            year = str(datetime.now().year)

        # 에볼라 등 국내 데이터가 없는 경우의 기본값
        if api_disease_name == "에볼라바이러스병":
            return {
                "disease": disease,
                "year": year,
                "total_count": 0,
                "incidence_rate": 0.0,
                "monthly_trend": []
            }

        total_count = 0
        incidence_rate = 0.0
        monthly_trend = []

        # 코로나19 데이터 처리 (현재 로컬 COVID 서비스 사용)
        if api_disease_name == "코로나바이러스감염증-19":
            count_data = fetch_covid_region_status(year=year)
            count_items = count_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            for item in count_items:
                if item.get("sidoNm") in ["합계", "전국"] or item.get("sidoCd") == "00":
                    total_count = safe_int(item.get("resultVal", 0))
                    
            spread_data = fetch_covid_period_spread(start_year=year, end_year=year)
            for item in spread_data:
                if item.get("sidoNm") in ["합계", "전국"] or item.get("sidoCd") == "00":
                    monthly_trend.append({
                        "period": item.get("period"),
                        "count": safe_int(item.get("resultVal", 0))
                    })
        else:
            # KDCA 전수감시 데이터 처리 (sidoCd == "00" 이 전국 합계)
            count_data = fetch_kdca_region_status(year=year, search_type="1")
            rate_data = fetch_kdca_region_status(year=year, search_type="2")
            
            count_items = count_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if isinstance(count_items, dict): count_items = [count_items]
            rate_items = rate_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if isinstance(rate_items, dict): rate_items = [rate_items]
            
            for item in count_items:
                if item.get("icdNm") == api_disease_name and item.get("sidoCd") == "00":
                    total_count = safe_int(item.get("resultVal", 0))
            
            for item in rate_items:
                if item.get("icdNm") == api_disease_name and item.get("sidoCd") == "00":
                    incidence_rate = safe_float(item.get("resultVal", 0))
                    
            # 월별 추이 데이터 수집
            spread_data = fetch_kdca_period_spread(start_year=year, end_year=year, period_type="2")
            for item in spread_data:
                if item.get("icdNm") == api_disease_name and item.get("sidoCd") == "00":
                    monthly_trend.append({
                        "period": item.get("period"),
                        "count": safe_int(item.get("resultVal", 0))
                    })

        # 기간(월) 기준으로 오름차순 정렬
        monthly_trend.sort(key=lambda x: x["period"])

        return {
            "disease": disease,
            "year": year,
            "total_count": total_count,
            "incidence_rate": incidence_rate,
            "monthly_trend": monthly_trend
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
