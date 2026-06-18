-- stg_kdca_age.sql
-- 원본 JSON 데이터 파싱 (연령별 통계)

{{ config(materialized='view') }}

WITH raw_extracted AS (
    SELECT
        id as raw_id,
        created_at as loaded_at,
        jsonb_array_elements(raw_payload->'items') AS item
    FROM {{ source('raw', 'kdca_age_status') }}
),
parsed_json AS (
    SELECT
        raw_id,
        loaded_at,
        (item->>'year')::text AS std_year,
        (item->>'ageRange')::text AS age_range,
        (item->>'icdNm')::text AS disease_name,
        NULLIF(REPLACE((item->>'resultVal')::text, ',', ''), '')::integer AS result_val
    FROM raw_extracted
    WHERE (item->>'icdNm')::text IN ('수두', '백일해', '유행성이하선염')
),
deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER(PARTITION BY std_year, age_range, disease_name ORDER BY loaded_at DESC, raw_id DESC) as rn
    FROM parsed_json
)

SELECT
    std_year,
    age_range,
    disease_name,
    result_val
FROM deduped
WHERE rn = 1
