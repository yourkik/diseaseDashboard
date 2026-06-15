# app/services/medical_service.py

def get_regional_infrastructure():
    """
    통계청(KOSIS) 및 심평원 기반의 시도별 인구 및 의료 인프라 (2023 기준 추정치)
    Power BI의 Dim_Region 테이블로 활용됩니다.
    """
    return [
        {"region": "서울", "population": 9400000, "elderly_ratio": 17.6, "total_beds": 88000},
        {"region": "부산", "population": 3300000, "elderly_ratio": 21.4, "total_beds": 69000},
        {"region": "대구", "population": 2360000, "elderly_ratio": 18.5, "total_beds": 38000},
        {"region": "인천", "population": 2960000, "elderly_ratio": 15.6, "total_beds": 33000},
        {"region": "광주", "population": 1430000, "elderly_ratio": 15.5, "total_beds": 40000},
        {"region": "대전", "population": 1440000, "elderly_ratio": 16.1, "total_beds": 24000},
        {"region": "울산", "population": 1110000, "elderly_ratio": 14.8, "total_beds": 14000},
        {"region": "세종", "population": 380000,  "elderly_ratio": 10.6, "total_beds": 3000},
        {"region": "경기", "population": 13580000, "elderly_ratio": 14.7, "total_beds": 133000},
        {"region": "강원", "population": 1530000, "elderly_ratio": 22.8, "total_beds": 17000},
        {"region": "충북", "population": 1590000, "elderly_ratio": 19.9, "total_beds": 19000},
        {"region": "충남", "population": 2120000, "elderly_ratio": 20.6, "total_beds": 26000},
        {"region": "전북", "population": 1770000, "elderly_ratio": 23.2, "total_beds": 36000},
        {"region": "전남", "population": 1810000, "elderly_ratio": 25.2, "total_beds": 41000},
        {"region": "경북", "population": 2590000, "elderly_ratio": 23.8, "total_beds": 46000},
        {"region": "경남", "population": 3270000, "elderly_ratio": 19.5, "total_beds": 60000},
        {"region": "제주", "population": 670000,  "elderly_ratio": 17.1, "total_beds": 5000},
    ]

def get_demographic_infection_weights():
    """
    질병별 연령/성별 감염 가중치 (API 미지원에 따른 역학 시뮬레이션 용도)
    Power BI의 Fact_Demographics 테이블로 활용됩니다.
    """
    return {
        "수두": [
            {"age_group": "0-9세", "gender": "M", "weight": 0.45},
            {"age_group": "0-9세", "gender": "F", "weight": 0.40},
            {"age_group": "10-19세", "gender": "M", "weight": 0.05},
            {"age_group": "10-19세", "gender": "F", "weight": 0.05},
            {"age_group": "20세 이상", "gender": "M", "weight": 0.02},
            {"age_group": "20세 이상", "gender": "F", "weight": 0.03},
        ],
        "코로나19": [
            {"age_group": "0-19세", "gender": "M", "weight": 0.08},
            {"age_group": "0-19세", "gender": "F", "weight": 0.07},
            {"age_group": "20-59세", "gender": "M", "weight": 0.30},
            {"age_group": "20-59세", "gender": "F", "weight": 0.35},
            {"age_group": "60세 이상", "gender": "M", "weight": 0.10},
            {"age_group": "60세 이상", "gender": "F", "weight": 0.10},
        ]
    }
