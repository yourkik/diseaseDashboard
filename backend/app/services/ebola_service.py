import json
import os
from collections import defaultdict

def fetch_ebola_region_status():
    """
    hdx_ebola_verified_20260605d_111708.json 파일을 읽어서 지역별 확진자 수와 사망자 수를 집계합니다.
    """
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'hdx_ebola_verified_20260605d_111708.json'))
    
    if not os.path.exists(file_path):
        return {}

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 지역별로 데이터 집계
    # cases_confirmed 총합을 count로 사용하고, deaths_suspected 총합을 부가 정보로 사용
    region_stats = defaultdict(lambda: {"region": "", "count": 0, "deaths": 0})
    
    for row in data:
        region = row.get("region_name")
        if not region:
            continue
            
        indicator = row.get("indicator_type", "")
        value = int(row.get("cases_value", 0))
        
        region_stats[region]["region"] = region
        
        if indicator == "cases_confirmed":
            region_stats[region]["count"] += value
        elif indicator == "deaths_suspected" or indicator == "deaths_confirmed":
            region_stats[region]["deaths"] += value

    return dict(region_stats)
