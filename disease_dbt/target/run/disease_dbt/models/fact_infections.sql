
  
    

  create  table "sentinel_db"."analytics"."fact_infections__dbt_tmp"
  
  
    as
  
  (
    -- 지역별 감염병 통계 팩트 테이블
-- stg_kdca에서 파싱된 데이터를 집계 및 정제하여 최종 분석용 뷰 제공



WITH stg_data AS (
    SELECT * FROM "sentinel_db"."analytics"."stg_kdca"
),

aggregated AS (
    SELECT
        std_day AS date,
        region_name,
        disease_name,
        SUM(new_cases) AS total_new_cases,
        MAX(total_cases) AS cumulative_cases,
        MAX(total_deaths) AS cumulative_deaths
    FROM stg_data
    GROUP BY std_day, region_name, disease_name
)

SELECT
    date,
    region_name,
    disease_name,
    total_new_cases,
    cumulative_cases,
    cumulative_deaths
FROM aggregated
ORDER BY date DESC, disease_name, region_name
  );
  