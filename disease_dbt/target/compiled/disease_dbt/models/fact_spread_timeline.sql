-- fact_spread_timeline.sql
-- 질병별/지역별 시계열 발생 현황 (Azure Map 애니메이션용)



SELECT
    period_str,
    disease_name,
    region_name,
    region_cd,
    SUM(result_val) as total_cases
FROM "sentinel_db"."analytics"."stg_kdca_period"
WHERE result_val > 0
GROUP BY period_str, disease_name, region_name, region_cd
ORDER BY period_str ASC, disease_name, region_name