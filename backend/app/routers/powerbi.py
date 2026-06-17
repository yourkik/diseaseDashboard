# app/routers/powerbi.py

from fastapi import APIRouter, HTTPException
from app.services.medical_service import get_regional_infrastructure, get_demographic_age_real, get_demographic_gender_real
from app.services.mobility_service import get_weekly_mobility_data
from app.services.covid_service import fetch_covid_period_spread
from datetime import datetime
import psycopg2

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
        
        # 2. Fact_Demographics (Age and Gender)
        demographics_age = get_demographic_age_real()
        demographics_gender = get_demographic_gender_real()
        
        # 3. Fact_Mobility
        mobility = get_weekly_mobility_data(int(year))
        
        # 4. Fact_Infections (KDCA DB + COVID API 병합)
        infections = []
        
        # 일반 법정감염병 월별 데이터 (PostgreSQL dbt Fact 테이블에서 직접 조회)
        conn = psycopg2.connect(host="127.0.0.1", port="5433", dbname="sentinel_db", user="sentinel", password="sentinel_password")
        cur = conn.cursor()
        
        # DB에 존재하는 가장 최신 연도 확인 ('계' 등 예외 문자열 제외)
        cur.execute("SELECT MAX(SUBSTRING(period_str, 1, 4)) FROM analytics.fact_spread_timeline WHERE period_str LIKE '20%'")
        max_year_row = cur.fetchone()
        db_max_year = max_year_row[0] if max_year_row and max_year_row[0] else str(datetime.now().year)
        
        # 요청한 연도(현재 2026년 등)가 DB의 최신 연도보다 크면 최신 연도로 강제 조정
        if year > db_max_year:
            year = db_max_year

        # 해당 연도의 데이터만 가져오기 (period_str: "2023년 01월" 형태)
        cur.execute("""
            SELECT period_str, region_name, disease_name, total_cases
            FROM analytics.fact_spread_timeline
            WHERE period_str LIKE %s
        """, (f"{year}년%",))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        for period, region, disease, count in rows:
            if region != "합계" and region != "전국":
                infections.append({
                    "Date": period,
                    "Region": region,
                    "Disease": disease,
                    "Count": count
                })
                    
        # 코로나19 월별 데이터 (코로나 DB 연동 전까지 API 사용)
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
            "Fact_Demographics_Age": demographics_age,
            "Fact_Demographics_Gender": demographics_gender,
            "Fact_Mobility": mobility,
            "Fact_Infections": infections
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
