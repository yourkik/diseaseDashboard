-- fact_demographic_gender.sql
-- 질병별/성별 최신 발생 현황 (가장 최신 연도 기준)



WITH latest_year AS (
    SELECT disease_name, MAX(std_year) as max_year
    FROM "sentinel_db"."analytics"."stg_kdca_gender"
    WHERE result_val > 0
    GROUP BY disease_name
)

SELECT
    s.std_year,
    s.disease_name,
    s.gender,
    SUM(s.result_val) as total_cases
FROM "sentinel_db"."analytics"."stg_kdca_gender" s
JOIN latest_year ly ON s.disease_name = ly.disease_name AND s.std_year = ly.max_year
WHERE s.result_val > 0
GROUP BY s.std_year, s.disease_name, s.gender
ORDER BY s.disease_name, s.gender