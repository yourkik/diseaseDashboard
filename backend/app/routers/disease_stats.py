from fastapi import APIRouter, HTTPException
from typing import Optional
from app.services.kdca_service import fetch_kdca_region_status
from app.services.covid_service import fetch_covid_region_status, fetch_covid_period_spread
from app.services.ebola_service import fetch_ebola_region_status
from app.services.medical_service import get_regional_infrastructure
from datetime import datetime
import psycopg2
import os

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

@router.get("/years")
def get_available_years(disease: str):
    """
    실제 DB에 저장된 특정 질병의 데이터 연도 목록을 반환합니다.
    """
    try:
        api_disease_name = DISEASE_MAPPING.get(disease, disease)
        
        # 에볼라나 코로나는 DB가 아닌 실시간/글로벌 데이터이므로 현재 연도만 반환
        if api_disease_name == "에볼라바이러스병" or api_disease_name == "코로나바이러스감염증-19":
            return [str(datetime.now().year)]
            
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"), 
            port=os.getenv("DB_PORT", "5433"), 
            dbname=os.getenv("DB_NAME", "sentinel_db"), 
            user=os.getenv("DB_USER", "sentinel"), 
            password=os.getenv("DB_PASS", "sentinel_password")
        )
        cur = conn.cursor()
        
        if api_disease_name == "전체":
            cur.execute("SELECT DISTINCT EXTRACT(YEAR FROM date) FROM analytics.fact_infections ORDER BY 1 DESC")
        else:
            cur.execute("SELECT DISTINCT EXTRACT(YEAR FROM date) FROM analytics.fact_infections WHERE disease_name = %s ORDER BY 1 DESC", (api_disease_name,))
            
        rows = cur.fetchall()
        years = [str(int(r[0])) for r in rows if r[0] is not None]
        
        cur.close()
        conn.close()
        
        if not years:
            return [str(datetime.now().year)]
        return years
    except Exception as e:
        print(f"DB Error (/years): {e}")
        return [str(datetime.now().year)]

@router.get("/status")
def get_map_status(disease: str, year: Optional[str] = None):
    """
    현황 파악 (Choropleth Map): PostgreSQL DW의 analytics.fact_infections 테이블을 쿼리하여 반환 (초고속 응답)
    """
    try:
        # 질병명 매핑
        api_disease_name = DISEASE_MAPPING.get(disease, disease)
        
        result = []
        try:
            # DB 연동 (실제 운영 시에는 SQLAlchemy Connection Pool 등을 사용)
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "127.0.0.1"), 
                port=os.getenv("DB_PORT", "5433"), 
                dbname=os.getenv("DB_NAME", "sentinel_db"), 
                user=os.getenv("DB_USER", "sentinel"), 
                password=os.getenv("DB_PASS", "sentinel_password")
            )
            cur = conn.cursor()
            
            if api_disease_name == "전체":
                if year and year != "전체":
                    query = """
                        SELECT region_name, SUM(max_cum), SUM(max_new) 
                        FROM (
                            SELECT region_name, disease_name, MAX(cumulative_cases) as max_cum, MAX(total_new_cases) as max_new
                            FROM analytics.fact_infections 
                            WHERE EXTRACT(YEAR FROM date) = %s
                            GROUP BY region_name, disease_name
                        ) sub
                        GROUP BY region_name
                    """
                    params = [year]
                else:
                    query = """
                        SELECT region_name, SUM(max_cum), SUM(max_new) 
                        FROM (
                            SELECT region_name, disease_name, MAX(cumulative_cases) as max_cum, MAX(total_new_cases) as max_new
                            FROM analytics.fact_infections 
                            GROUP BY region_name, disease_name
                        ) sub
                        GROUP BY region_name
                    """
                    params = []
            else:
                query = """
                    SELECT region_name, MAX(cumulative_cases), MAX(total_new_cases) 
                    FROM analytics.fact_infections 
                    WHERE disease_name = %s 
                """
                params = [api_disease_name]
                
                if year and year != "전체":
                    query += " AND EXTRACT(YEAR FROM date) = %s "
                    params.append(year)
                    
                query += " GROUP BY region_name "
                
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            
            # 기간 문자열 구하기 (DB의 날짜가 연말(12-31)로 뭉뚱그려져 있으므로 동적으로 예쁘게 포맷팅)
            period_str = "DB 최신 누적 데이터"
            try:
                date_q = "SELECT DISTINCT EXTRACT(YEAR FROM date) FROM analytics.fact_infections"
                date_params = []
                filters = []
                if api_disease_name != "전체":
                    filters.append("disease_name = %s")
                    date_params.append(api_disease_name)
                    
                if filters:
                    date_q += " WHERE " + " AND ".join(filters)
                    
                cur.execute(date_q, tuple(date_params))
                date_rows = cur.fetchall()
                if date_rows:
                    max_year = int(max([r[0] for r in date_rows if r[0]]))
                    current_year = datetime.now().year
                    
                    if max_year == current_year:
                        # 현재 연도면 1월 1일부터 오늘까지
                        period_str = f"{max_year}-01-01 ~ {datetime.now().strftime('%Y-%m-%d')}"
                    else:
                        # 과거 연도면 1월 1일부터 12월 31일까지
                        period_str = f"{max_year}-01-01 ~ {max_year}-12-31"
            except Exception as e:
                print(f"Failed to get dates: {e}")
            
            # 지역별 인구 데이터 가져오기 (비율 계산용)
            infrastructure = get_regional_infrastructure()
            pop_map = {item["region"]: item["population"] for item in infrastructure}
            
            for row in rows:
                region = row[0]
                count = row[1] if row[1] else 0
                
                # 발생률 계산: (확진자 수 / 인구) * 100,000
                pop = pop_map.get(region, 0)
                rate = round((count / pop) * 100000, 2) if pop > 0 else 0.0
                
                # 프론트엔드가 요구하는 형식에 맞추어 변환
                result.append({
                    "region": region,
                    "count": count,
                    "new_cases": row[2] if row[2] else 0,
                    "period": period_str,
                    "rate": rate
                })
                
            cur.close()
            conn.close()
        except Exception as db_err:
            print(f"[System] DB 연결 실패 (Fallback API 사용): {db_err}")
            
        # 만약 DB에 연결 실패했거나 아직 진짜 데이터가 수집되지 않았다면 기존 API 코드로 실시간 조회 (Fallback)
        if not result:
            print(f"[System] DB에 {api_disease_name} 데이터가 없습니다. 실시간 API를 호출합니다.")
            
            if not year:
                year = str(datetime.now().year)

            if api_disease_name == "전체":
                print("[System] '전체' 데이터 실시간 Fallback은 지원하지 않습니다. (빈 배열 반환)")
                return []

            if api_disease_name == "에볼라바이러스병":
                return fetch_ebola_region_status()

            if api_disease_name == "코로나바이러스감염증-19":
                count_data = fetch_covid_region_status(year=year)
                rate_data = count_data 
            else:
                count_data = fetch_kdca_region_status(year=year, search_type="1")
                rate_data = fetch_kdca_region_status(year=year, search_type="2")
            
            count_items = count_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            rate_items = rate_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            
            fallback_result = {}
            for item in count_items:
                if item.get("icdNm") == api_disease_name and item.get("sidoCd") != "00":
                    sido = item.get("sidoNm")
                    fallback_result[sido] = {
                        "region": sido,
                        "count": safe_int(item.get("resultVal", 0)),
                        "period": item.get("stdDay", f"{year}년 누적 실시간 데이터")
                    }
                    
            for item in rate_items:
                if item.get("icdNm") == api_disease_name and item.get("sidoCd") != "00":
                    sido = item.get("sidoNm")
                    if sido in fallback_result:
                        fallback_result[sido]["rate"] = safe_float(item.get("resultVal", 0))
                        
            return list(fallback_result.values())

        return result
        
    except Exception as e:
        print(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spread")
def get_map_spread(disease: str, year: Optional[str] = None, period_type: str = "2"):
    """
    전파 지도 (Time-series Animation): PostgreSQL에서 최근 6개월 치의 시계열 추이를 반환합니다.
    """
    try:
        api_disease_name = DISEASE_MAPPING.get(disease, disease)
        
        # 에볼라 분기: 확산 추이는 현재 DB에 없으므로 빈 딕셔너리 반환
        if api_disease_name == "에볼라바이러스병" or api_disease_name == "코로나바이러스감염증-19":
            return {}

        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "127.0.0.1"), 
                port=os.getenv("DB_PORT", "5433"), 
                dbname=os.getenv("DB_NAME", "sentinel_db"), 
                user=os.getenv("DB_USER", "sentinel"), 
                password=os.getenv("DB_PASS", "sentinel_password")
            )
            cur = conn.cursor()
            
            if api_disease_name == "전체":
                query = """
                    SELECT period_str, region_name, SUM(total_cases)
                    FROM analytics.fact_spread_timeline
                """
                params = []
                if year and year != "전체":
                    query += " WHERE period_str LIKE %s "
                    params.append(f"{year}%")
                query += " GROUP BY period_str, region_name ORDER BY period_str ASC "
                cur.execute(query, tuple(params))
            else:
                query = """
                    SELECT period_str, region_name, total_cases
                    FROM analytics.fact_spread_timeline
                    WHERE disease_name = %s
                """
                params = [api_disease_name]
                if year and year != "전체":
                    query += " AND period_str LIKE %s "
                    params.append(f"{year}%")
                query += " ORDER BY period_str ASC "
                cur.execute(query, tuple(params))
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as db_err:
            print(f"[System] DB 연결 실패 (/spread): {db_err}")
            return {}
        
        timeline_result = {}
        for period, region, count in rows:
            if period not in timeline_result:
                timeline_result[period] = []
            timeline_result[period].append({
                "region": region,
                "count": count
            })
            
        # 연도가 지정된 경우 슬라이싱 없이 전체 기간을 보여주고,
        # 연도 지정이 없다면(전체 조회시) 가장 최근 6개월만 슬라이싱
        sorted_periods = sorted(timeline_result.keys())
        if year and year != "전체":
            recent_periods = sorted_periods
        else:
            recent_periods = sorted_periods[-6:] if len(sorted_periods) > 6 else sorted_periods
        
        sorted_timeline = {k: timeline_result[k] for k in recent_periods}
        return sorted_timeline
        
    except Exception as e:
        print(f"DB Error (Spread): {e}")
        return {}

@router.get("/total")
def get_total_stats(disease: str, year: Optional[str] = None):
    """
    전국 통합 지표: PostgreSQL에서 특정 질병의 전국 누적 확진자 수와 최근 6개월 추이를 반환합니다.
    """
    try:
        api_disease_name = DISEASE_MAPPING.get(disease, disease)
        
        if not year:
            year = str(datetime.now().year)

        if api_disease_name == "에볼라바이러스병" or api_disease_name == "코로나바이러스감염증-19":
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

        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "127.0.0.1"), 
                port=os.getenv("DB_PORT", "5433"), 
                dbname=os.getenv("DB_NAME", "sentinel_db"), 
                user=os.getenv("DB_USER", "sentinel"), 
                password=os.getenv("DB_PASS", "sentinel_password")
            )
            cur = conn.cursor()
            
            if api_disease_name == "전체":
                cur.execute("""
                    SELECT SUM(max_cum)
                    FROM (
                        SELECT region_name, disease_name, MAX(cumulative_cases) as max_cum
                        FROM analytics.fact_infections
                        GROUP BY region_name, disease_name
                    ) sub
                """)
                row = cur.fetchone()
                if row and row[0]:
                    total_count = int(row[0])
                    incidence_rate = round((total_count / 51000000) * 100000, 2)
                    
                cur.execute("""
                    SELECT period_str, SUM(total_cases)
                    FROM analytics.fact_spread_timeline
                    GROUP BY period_str
                    ORDER BY period_str ASC
                """)
            else:
                cur.execute("""
                    SELECT SUM(cumulative_cases)
                    FROM analytics.fact_infections
                    WHERE disease_name = %s
                """, (api_disease_name,))
                row = cur.fetchone()
                if row and row[0]:
                    total_count = int(row[0])
                    incidence_rate = round((total_count / 51000000) * 100000, 2)
                    
                # 월별 전국 합산 (조건에 맞는 연도만 필터링)
                query = """
                    SELECT period_str, SUM(total_cases)
                    FROM analytics.fact_spread_timeline
                    WHERE disease_name = %s
                """
                params = [api_disease_name]
                if year and year != "전체":
                    query += " AND period_str LIKE %s "
                    params.append(f"{year}%")
                query += " GROUP BY period_str ORDER BY period_str ASC "
                cur.execute(query, tuple(params))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            for period, count in rows:
                monthly_trend.append({
                    "period": period,
                    "count": count
                })
                
            # 연도 지정 시 전체 월 표시, 미지정 시 최근 6개월만
            if year and year != "전체":
                monthly_trend = monthly_trend
            else:
                monthly_trend = monthly_trend[-6:] if len(monthly_trend) > 6 else monthly_trend
        except Exception as db_err:
            print(f"[System] DB 연결 실패 (/total): {db_err}")

        return {
            "disease": disease,
            "year": year,
            "total_count": total_count,
            "incidence_rate": incidence_rate,
            "monthly_trend": monthly_trend
        }

    except Exception as e:
        print(f"DB Error (Total): {e}")
        return {
            "disease": disease,
            "year": year,
            "total_count": 0,
            "incidence_rate": 0.0,
            "monthly_trend": []
        }
