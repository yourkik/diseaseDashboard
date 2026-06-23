# app/routers/powerbi.py

from fastapi import APIRouter, HTTPException
from app.services.medical_service import get_regional_infrastructure, get_demographic_age_real, get_demographic_gender_real
from datetime import datetime
import psycopg2
import os

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
        
        # 3. Fact_Mobility (DB에서 직접 조회)
        cur.execute("SELECT period_str, region_name, traffic_volume FROM analytics.fact_mobility WHERE period_str LIKE %s", (f"{year}년%",))
        mobility_rows = cur.fetchall()
        mobility = []
        for period, region, vol in mobility_rows:
            mobility.append({
                "region": region,
                "month": period,
                "traffic_volume": vol
            })
        
        # 4. Fact_Infections (KDCA DB)
        infections = []
        
        # 일반 법정감염병 월별 데이터 (PostgreSQL dbt Fact 테이블에서 직접 조회)
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"), 
            port=os.getenv("DB_PORT", "5433"), 
            dbname=os.getenv("DB_NAME", "sentinel_db"), 
            user=os.getenv("DB_USER", "sentinel"), 
            password=os.getenv("DB_PASS", "sentinel_password")
        )
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
        
        current_year = datetime.now().year
        current_month = datetime.now().month

        for period, region, disease, count in rows:
            if region != "합계" and region != "전국":
                # 미래 데이터(현재 연도의 미래 월) 필터링
                parts = period.split('년 ')
                if len(parts) == 2:
                    inf_y = int(parts[0])
                    inf_m = int(parts[1].replace('월', '').strip())
                    if inf_y == current_year and inf_m > current_month:
                        continue # 미래 월 데이터는 건너뜀
                        
                infections.append({
                    "Date": period,
                    "Region": region,
                    "Disease": disease,
                    "Count": count
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
