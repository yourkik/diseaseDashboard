
  create view "sentinel_db"."analytics"."stg_kdca_period__dbt_tmp"
    
    
  as (
    -- stg_kdca_period.sql
-- 원본 JSON 데이터 파싱 (시계열 월별/주별 통계)



WITH raw_extracted AS (
    SELECT
        id as raw_id,
        created_at as loaded_at,
        jsonb_array_elements(raw_payload->'items') AS item
    FROM "sentinel_db"."raw_data"."kdca_period_status"
),
parsed_json AS (
    SELECT
        raw_id,
        loaded_at,
        (item->>'period')::text AS period_str,
        (item->>'sidoNm')::text AS region_name,
        (item->>'sidoCd')::text AS region_cd,
        (item->>'icdNm')::text AS disease_name,
        NULLIF(REPLACE((item->>'resultVal')::text, ',', ''), '')::integer AS result_val
    FROM raw_extracted
    WHERE (item->>'icdNm')::text IN ('수두', '백일해', '유행성이하선염')
),
deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER(PARTITION BY period_str, region_name, disease_name ORDER BY loaded_at DESC, raw_id DESC) as rn
    FROM parsed_json
)

SELECT
    period_str,
    region_name,
    region_cd,
    disease_name,
    result_val
FROM deduped
WHERE rn = 1
  );