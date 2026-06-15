# app/routers/powerbi.py

from fastapi import APIRouter, HTTPException
from app.services.medical_service import get_regional_infrastructure, get_demographic_infection_weights
from app.services.mobility_service import get_weekly_mobility_data
from app.services.kdca_service import fetch_kdca_period_spread
from app.services.covid_service import fetch_covid_period_spread
from datetime import datetime

router = APIRouter(prefix="/api/powerbi", tags=["Power BI Dataset"])

DISEASES = ["수두", "백일해", "유행성이하선염", "코로나바이러스감염증-19"]

def safe_int(val):
    if not val: return 0
    if isinstance(val, str): val = val.replace(",", "")
    try: return int(val)
    except: return 0

@router.get("/dataset")
def export_powerbi_dataset(year: str = None):
    """
    Power BI 연동을 위한 Star Schema 구조의 통합 데이터셋 반환
    """
    if not year:
        year = str(datetime.now().year)
        
    try:
        # 1. Dim_Region_Infrastructure
        regions = get_regional_infrastructure()
        
        # 2. Fact_Demographics
        demographics = get_demographic_infection_weights()
        
        # 3. Fact_Mobility
        mobility = get_weekly_mobility_data(int(year))
        
        # 4. Fact_Infections (KDCA + COVID API 병합)
        infections = []
        
        # 일반 법정감염병 월별 데이터
        kdca_data = fetch_kdca_period_spread(start_year=year, end_year=year, period_type="2")
        for item in kdca_data:
            icdNm = item.get("icdNm")
            if icdNm in DISEASES:
                sidoNm = item.get("sidoNm")
                # "00" (전국) 및 "기타" 등 제외, 순수 지역만
                if item.get("sidoCd") != "00" and sidoNm:
                    infections.append({
                        "Date": item.get("period"), # "2023년 01월"
                        "Region": sidoNm,
                        "Disease": "수두" if icdNm == "수두" else "백일해" if icdNm == "백일해" else "유행성이하선염",
                        "Count": safe_int(item.get("resultVal", 0))
                    })
                    
        # 코로나19 월별 데이터
        covid_data = fetch_covid_period_spread(start_year=year, end_year=year)
        for item in covid_data:
            sidoNm = item.get("sidoNm")
            if sidoNm and sidoNm not in ["합계", "전국", "검역"]:
                infections.append({
                    "Date": item.get("period"),
                    "Region": sidoNm,
                    "Disease": "코로나19",
                    "Count": safe_int(item.get("resultVal", 0))
                })

        return {
            "Dim_Region": regions,
            "Fact_Demographics": demographics,
            "Fact_Mobility": mobility,
            "Fact_Infections": infections
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
