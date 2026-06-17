import sys
import os
import json
import psycopg2
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.services.kdca_service import (
    fetch_kdca_region_status,
    fetch_kdca_age_status,
    fetch_kdca_gender_status,
    fetch_kdca_period_region
)

DB_HOST = 'localhost'
DB_PORT = '5433'
DB_NAME = 'sentinel_db'
DB_USER = 'sentinel'
DB_PASS = 'sentinel_password'

# 이전 캐시 파일 삭제 (항상 최신 데이터를 강제로 받아오기 위함)
cache_file = os.path.join(os.getcwd(), 'backend', 'app', 'services', 'kdca_cache.json')
if os.path.exists(cache_file):
    os.remove(cache_file)

def safe_int(val):
    if not val: return 0
    if isinstance(val, str): val = val.replace(",", "")
    try: return int(val)
    except: return 0

def create_raw_tables(cur):
    queries = [
        """
        CREATE TABLE IF NOT EXISTS raw_data.kdca_region_status (
            id SERIAL PRIMARY KEY,
            region_name VARCHAR(100),
            raw_payload JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS raw_data.kdca_age_status (
            id SERIAL PRIMARY KEY,
            raw_payload JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS raw_data.kdca_gender_status (
            id SERIAL PRIMARY KEY,
            raw_payload JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS raw_data.kdca_period_status (
            id SERIAL PRIMARY KEY,
            raw_payload JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]
    for q in queries:
        cur.execute(q)

def run_full_etl():
    print("🚀 [Phase 1] 데이터베이스에서 최신 연도 확인 중...")
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    
    create_raw_tables(cur)
    
    # DB에 적재된 최신 데이터의 연도 확인
    try:
        cur.execute("""
            SELECT MAX(CAST(item->>'stdDay' AS DATE))
            FROM raw_data.kdca_region_status,
            jsonb_array_elements(raw_payload#>'{response,body,items,item}') AS item
            WHERE raw_payload#>'{response,body,items,item}' IS NOT NULL
        """)
        result = cur.fetchone()
        latest_year = result[0].year if result and result[0] else 2023
    except Exception as e:
        print(f"연도 조회 실패, 기본값(2023) 사용: {e}")
        latest_year = 2023
        conn.rollback()
        
    current_year = datetime.now().year
    # 과거 연도는 확정되어 변하지 않으므로 제외하고, 항상 현재 연도(올해)의 데이터만 수집합니다.
    years_to_fetch = [str(current_year)]
    print(f"✅ 수집 대상 연도: {years_to_fetch}")

    print("🚀 [Phase 1.5] KDCA 다중 엔드포인트 수집을 시작합니다...")
    
    kdca_region_items = []
    kdca_age_items = []
    kdca_gender_items = []
    
    for y in years_to_fetch:
        r_data = fetch_kdca_region_status(year=y)
        r_items = r_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(r_items, dict): r_items = [r_items]
        kdca_region_items.extend(r_items)

        a_data = fetch_kdca_age_status(year=y)
        a_items = a_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(a_items, dict): a_items = [a_items]
        kdca_age_items.extend(a_items)

        g_data = fetch_kdca_gender_status(year=y)
        g_items = g_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(g_items, dict): g_items = [g_items]
        kdca_gender_items.extend(g_items)

    print("🚀 [Phase 1.8] 시계열(기간별) 지역 데이터 수집 중...")
    # 기간별(월별) 수집 - 오직 현재 연도만 수집
    kdca_period_items = fetch_kdca_period_region(start_year=str(current_year), end_year=str(current_year), period_type="2")

    print(f"✅ 수집 완료: 지역({len(kdca_region_items)}), 연령({len(kdca_age_items)}), 성별({len(kdca_gender_items)}), 월별({len(kdca_period_items)})")

    # DB 적재
    # TRUNCATE 제거: 기존 데이터 보존 (Incremental Load)

    # Region은 지역별 묶음으로 넣기 (기존 파이프라인 호환성)
    region_payloads = {}
    for item in kdca_region_items:
        sidoNm = item.get("sidoNm")
        if sidoNm and sidoNm not in ["전국", "합계", "검역"] and item.get("sidoCd") != "00":
            if sidoNm not in region_payloads:
                region_payloads[sidoNm] = []
            
            val = safe_int(item.get("resultVal", 0))
            year = item.get("year", "2023")[:4]
            region_payloads[sidoNm].append({
                "icdNm": item.get("icdNm"),
                "incDec": str(val),
                "defCnt": str(val),
                "deathCnt": "0",
                "stdDay": f"{year}-12-31" 
            })

    for region, items in region_payloads.items():
        payload = {"response": {"body": {"items": {"item": items}}}}
        cur.execute('INSERT INTO raw_data.kdca_region_status (region_name, raw_payload) VALUES (%s, %s)', (region, json.dumps(payload, ensure_ascii=False)))

    # Age, Gender, Period는 통째로 넣기
    if kdca_age_items:
        cur.execute('INSERT INTO raw_data.kdca_age_status (raw_payload) VALUES (%s)', (json.dumps({"items": kdca_age_items}, ensure_ascii=False),))
    if kdca_gender_items:
        cur.execute('INSERT INTO raw_data.kdca_gender_status (raw_payload) VALUES (%s)', (json.dumps({"items": kdca_gender_items}, ensure_ascii=False),))
    if kdca_period_items:
        cur.execute('INSERT INTO raw_data.kdca_period_status (raw_payload) VALUES (%s)', (json.dumps({"items": kdca_period_items}, ensure_ascii=False),))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ 모든 Raw 데이터베이스 적재 완료!")

if __name__ == "__main__":
    run_full_etl()
