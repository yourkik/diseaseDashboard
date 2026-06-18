-- raw_data 스키마의 데이터를 파싱하는 Staging 모델
-- JSONB 배열을 개별 행으로 확장(unnest)하여 필요한 컬럼만 추출

WITH raw_source AS (
    SELECT 
        id as raw_id,
        region_name,
        created_at as loaded_at,
        raw_payload
    FROM {{ source('raw', 'kdca_region_status') }}
),

parsed_json AS (
    SELECT
        raw_id,
        region_name,
        loaded_at,
        jsonb_array_elements(raw_payload#>'{response,body,items,item}') AS item
    FROM raw_source
    WHERE raw_payload#>'{response,body,items,item}' IS NOT NULL
),

deduped AS (
    SELECT
        raw_id,
        region_name,
        loaded_at,
        (item->>'icdNm')::text AS disease_name,
        (item->>'stdDay')::date AS std_day,
        (item->>'incDec')::int AS new_cases,
        (item->>'defCnt')::int AS total_cases,
        (item->>'deathCnt')::int AS total_deaths,
        ROW_NUMBER() OVER(
            PARTITION BY region_name, (item->>'icdNm')::text, (item->>'stdDay')::date 
            ORDER BY loaded_at DESC, raw_id DESC
        ) as rn
    FROM parsed_json
)

SELECT
    raw_id,
    region_name,
    loaded_at,
    disease_name,
    std_day,
    new_cases,
    total_cases,
    total_deaths
FROM deduped
WHERE rn = 1
