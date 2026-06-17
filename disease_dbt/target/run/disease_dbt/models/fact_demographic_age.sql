
  
    

  create  table "sentinel_db"."analytics"."fact_demographic_age__dbt_tmp"
  
  
    as
  
  (
    -- fact_demographic_age.sql
-- 질병별/연령별 최신 발생 현황 (가장 최신 연도 기준)



WITH latest_year AS (
    SELECT disease_name, MAX(std_year) as max_year
    FROM "sentinel_db"."analytics"."stg_kdca_age"
    WHERE result_val > 0
    GROUP BY disease_name
)

SELECT
    s.std_year,
    s.disease_name,
    s.age_range,
    SUM(s.result_val) as total_cases
FROM "sentinel_db"."analytics"."stg_kdca_age" s
JOIN latest_year ly ON s.disease_name = ly.disease_name AND s.std_year = ly.max_year
WHERE s.result_val > 0
GROUP BY s.std_year, s.disease_name, s.age_range
ORDER BY s.disease_name, s.age_range
  );
  