from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import requests
import psycopg2
import json
import os

# DB 연결 정보 (Docker PostgreSQL)
DB_HOST = "localhost"
DB_PORT = "5433"
DB_NAME = "sentinel_db"
DB_USER = "sentinel"
DB_PASS = "sentinel_password"

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def extract_and_load_kdca():
    """KDCA 질병 확산 현황 API를 호출하여 raw_data 스키마에 적재"""
    API_KEY = os.getenv("EIDAPIS_Decoding", "test_key") # 실제 환경에서는 Variable 활용 권장
    BASE_URL = "https://apis.data.go.kr/1790387/EIDAPIService/Region"
    
    # 1. API Extract (서울, 경기 예시)
    regions = {'01': '서울', '08': '경기'}
    raw_results = []
    
    for sido_cd, sido_nm in regions.items():
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 1000,
            "resType": "2",
            "searchType": "1",
            "searchYear": "2026",
            "searchSidoCd": sido_cd
        }
        try:
            res = requests.get(BASE_URL, params=params, verify=False, timeout=10)
            if res.status_code == 200:
                raw_results.append({
                    "region_name": sido_nm,
                    "raw_json": json.dumps(res.json(), ensure_ascii=False)
                })
        except Exception as e:
            print(f"Error fetching {sido_nm}: {e}")

    # 2. PostgreSQL Load (raw_data schema)
    if not raw_results:
        print("수집된 데이터가 없습니다.")
        return

    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    
    # 원본 테이블 생성 (없을 경우)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_data.kdca_region_status (
            id SERIAL PRIMARY KEY,
            region_name VARCHAR(50),
            raw_payload JSONB,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 데이터 적재
    for item in raw_results:
        cur.execute(
            "INSERT INTO raw_data.kdca_region_status (region_name, raw_payload) VALUES (%s, %s)",
            (item['region_name'], item['raw_json'])
        )
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Successfully loaded {len(raw_results)} records into raw_data.kdca_region_status")

with DAG(
    'kdca_etl_pipeline',
    default_args=default_args,
    description='KDCA 데이터 수집 및 dbt 변환 파이프라인',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    # Task 1: Extract & Load
    t1_extract_load = PythonOperator(
        task_id='extract_load_kdca_api',
        python_callable=extract_and_load_kdca,
    )

    # Task 2: Transform (dbt run)
    t2_dbt_run = BashOperator(
        task_id='dbt_run_transform',
        bash_command='cd "d:/학업 관련 파일/자료 모음/dataSchool/3차 프로젝트/diseaseDashboard/disease_dbt" && dbt run --profiles-dir .',
    )

    # 의존성 설정
    t1_extract_load >> t2_dbt_run
