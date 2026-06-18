-- PostgreSQL 초기화 스크립트
-- 이 스크립트는 컨테이너가 처음 생성될 때 한 번만 실행됩니다.

-- Airflow가 데이터를 밀어넣을(Load) 원본 스키마 생성
CREATE SCHEMA IF NOT EXISTS raw_data;

-- dbt가 가공한 데이터(Star Schema)가 저장될 분석용 스키마 생성
CREATE SCHEMA IF NOT EXISTS analytics;

-- sentinel 사용자가 두 스키마에 접근할 수 있도록 권한 부여
GRANT ALL PRIVILEGES ON SCHEMA raw_data TO sentinel;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO sentinel;

-- 향후 생성될 테이블에 대한 기본 권한 설정
ALTER DEFAULT PRIVILEGES IN SCHEMA raw_data GRANT ALL ON TABLES TO sentinel;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT ALL ON TABLES TO sentinel;
