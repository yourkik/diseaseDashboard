# app/services/mobility_service.py

import random
from datetime import datetime, timedelta

def get_weekly_mobility_data(year: int):
    """
    한국도로공사 및 통신사 유동인구 기반 지역별 주간 이동량 (추정 시뮬레이션 데이터)
    Power BI의 Fact_Mobility 테이블로 활용됩니다.
    
    Returns:
        list: [{"region": "서울", "week": "2023-W01", "traffic_volume": 1250000}, ...]
    """
    regions = [
        "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
        "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"
    ]
    
    # Base traffic multipliers by region size/activity
    base_traffic = {
        "서울": 1500000, "경기": 2000000, "부산": 800000, "인천": 700000,
        "대구": 500000, "경남": 600000, "경북": 550000, "충남": 450000,
        "전남": 400000, "전북": 380000, "충북": 350000, "강원": 400000,
        "광주": 300000, "대전": 320000, "울산": 250000, "제주": 150000, "세종": 100000
    }
    
    mobility_data = []
    
    # 주차별 계절성(Seasonality) 부여 (예: 휴가철, 명절에 이동량 증가)
    for week in range(1, 53):
        week_str = f"{year}-W{week:02d}"
        
        # 계절성 가중치 계산
        seasonal_multiplier = 1.0
        if week in [5, 6, 38, 39]: # 설날, 추석 부근
            seasonal_multiplier = 1.4
        elif 30 <= week <= 34: # 여름 휴가철
            seasonal_multiplier = 1.25
        elif 50 <= week <= 52: # 연말
            seasonal_multiplier = 1.15
            
        for region in regions:
            base = base_traffic[region]
            
            # 약간의 노이즈 추가 (±10%)
            noise = random.uniform(0.9, 1.1)
            
            volume = int(base * seasonal_multiplier * noise)
            
            # 제주는 명절/휴가철에 더 큰 폭발적 증가
            if region == "제주" and seasonal_multiplier > 1.1:
                volume = int(volume * 1.3)
                
            mobility_data.append({
                "region": region,
                "week": week_str,
                "traffic_volume": volume
            })
            
    return mobility_data
