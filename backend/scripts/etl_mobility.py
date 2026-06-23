import os
import sys
from dotenv import load_dotenv
import psycopg2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.mobility_service import get_monthly_mobility_data

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env')))

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'), 
        port=os.getenv('DB_PORT'), 
        dbname=os.getenv('DB_NAME'), 
        user=os.getenv('DB_USER'), 
        password=os.getenv('DB_PASS')
    )

def main():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. 테이블 생성
        create_table_query = """
        CREATE TABLE IF NOT EXISTS analytics.fact_mobility (
            period_str VARCHAR(20),
            region_name VARCHAR(50),
            traffic_volume INTEGER,
            PRIMARY KEY (period_str, region_name)
        );
        """
        cur.execute(create_table_query)
        conn.commit()
        print('[System] analytics.fact_mobility 테이블 생성 성공 (또는 이미 존재함)')
        
        # 2. 2025, 2026년 데이터 생성 후 삽입
        years_to_seed = [2025, 2026]
        for year in years_to_seed:
            print(f'[System] {year}년도 교통량 데이터 추출 시작...')
            data = get_monthly_mobility_data(year)
            
            delete_query = "DELETE FROM analytics.fact_mobility WHERE period_str LIKE %s"
            cur.execute(delete_query, (f'{year}년%',))
            
            insert_query = """
            INSERT INTO analytics.fact_mobility (period_str, region_name, traffic_volume)
            VALUES (%s, %s, %s)
            ON CONFLICT (period_str, region_name) DO UPDATE 
            SET traffic_volume = EXCLUDED.traffic_volume;
            """
            
            count = 0
            for item in data:
                cur.execute(insert_query, (item['month'], item['region'], item['traffic_volume']))
                count += 1
                
            print(f'[System] {year}년도 교통량 데이터 {count}건 DB 적재 완료!')
            
        conn.commit()
        cur.close()
        conn.close()
        print('[System] 모든 적재 작업이 완료되었습니다.')
        
    except Exception as e:
        print(f'Error during ETL: {e}')

if __name__ == "__main__":
    main()
