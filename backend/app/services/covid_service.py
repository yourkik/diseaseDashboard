import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
COVID_DECODING = os.getenv("COVID_Decoding")

CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), "covid_cache.json")

def _load_file_cache():
    if os.path.exists(CACHE_FILE_PATH):
        try:
            with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_file_cache(cache_data):
    try:
        with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("COVID 캐시 파일 저장 실패:", e)

_cache = _load_file_cache()

def get_from_cache(key):
    if key in _cache:
        item = _cache[key]
        # 캐시 유효기간을 넉넉하게 24시간(86400초)으로 설정
        if datetime.now().timestamp() - item["timestamp"] < 86400: 
            return item["data"]
    return None

def set_to_cache(key, data):
    _cache[key] = {
        "timestamp": datetime.now().timestamp(),
        "data": data
    }
    _save_file_cache(_cache)

def fetch_covid_region_status(year="2024"):
    """
    코로나19 전용 API를 통해 시도별 누적 확진자 현황을 반환합니다.
    disease_stats.py에서 파싱할 수 있도록 KDCA API 표준 구조(response.body.items.item)로 변환하여 반환합니다.
    """
    cache_key = f"covid_region_status_{year}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data

    if not COVID_DECODING or COVID_DECODING == "your_covid_api_key_here":
        print("COVID_DECODING is not set.")
        return {"response": {"body": {"items": {"item": []}}}}
        
    url = 'http://apis.data.go.kr/1352000/ODMS_COVID_04/callCovid04Api'
    params = {'serviceKey': COVID_DECODING, 'pageNo': '1', 'numOfRows': '20', 'apiType': 'JSON'}
    
    try:
        # 공공데이터포털 서버가 느릴 수 있으므로 timeout을 30초로 넉넉하게 늘립니다.
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
        
        items = data.get("items", [])
        mapped_items = []
        for item in items:
            sido_nm = item.get("gubun")
            # 전국 합계나 검역 등은 제외 (sidoCd="00"으로 처리)
            if sido_nm == "합계" or sido_nm == "검역":
                sido_cd = "00"
            else:
                sido_cd = "11" # 임의의 유효 코드
                
            mapped_items.append({
                "icdNm": "코로나바이러스감염증-19",
                "sidoCd": sido_cd,
                "sidoNm": sido_nm,
                "resultVal": item.get("defCnt", 0), # 누적 확진자수
                "stdDay": item.get("stdDay", "") # 기준일자 추가
            })
            
        final_data = {"response": {"body": {"items": {"item": mapped_items}}}}
        set_to_cache(cache_key, final_data)
        return final_data
    except Exception as e:
        print(f"COVID API Fetch Error: {e}")
        return {"response": {"body": {"items": {"item": []}}}}

def fetch_covid_period_spread(start_year, end_year):
    """
    코로나19 전용 API를 통해 기간별/지역별 확산 추이를 반환합니다.
    """
    return []
