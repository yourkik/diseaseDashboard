import os
import time
import requests
import urllib3
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
API_KEY = os.getenv("EIDAPIS_Decoding")
BASE_URL = "https://apis.data.go.kr/1790387/EIDAPIService"

CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), "kdca_cache.json")

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
        print("캐시 파일 저장 실패:", e)

# 간단한 인메모리 캐시 (만료시간 1시간) + 로컬 파일 캐시 연동
_cache = _load_file_cache()

def get_from_cache(key):
    if key in _cache:
        # 영구 저장 모드: timestamp 기반 만료를 사용하지 않거나 넉넉하게 둠 (여기선 24시간으로 늘림)
        item = _cache[key]
        if datetime.now().timestamp() - item["timestamp"] < 86400: # 24시간
            return item["data"]
    return None

def set_to_cache(key, data):
    _cache[key] = {
        "timestamp": datetime.now().timestamp(),
        "data": data
    }
    _save_file_cache(_cache)

def fetch_kdca_region_status(year="2023", search_type="1"):
    """
    17개 시도별 연간 감염병 발생 현황을 수집합니다.
    """
    cache_key = f"region_status_{year}_{search_type}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data

    # 질병관리청 고유 지역 코드
    SIDO_MAPPING = {
        '01': '서울', '02': '부산', '03': '대구', '04': '인천', 
        '05': '광주', '06': '대전', '07': '울산', '08': '경기', 
        '09': '강원', '10': '충북', '11': '충남', '12': '전북', 
        '13': '전남', '14': '경북', '15': '경남', '16': '제주', '17': '세종'
    }

    url = f"{BASE_URL}/Region"
    all_items = []

    for sido_cd, sido_nm in SIDO_MAPPING.items():
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 10000,
            "resType": "2",
            "searchType": search_type,
            "searchYear": year,
            "searchSidoCd": sido_cd
        }
        try:
            response = requests.get(url, params=params, verify=False, timeout=5)
            if response.status_code != 200: continue
            data = response.json()
            if data.get("response", {}).get("header", {}).get("resultCode") != "00": continue
            
            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            # 단일 객체로 반환될 경우 리스트로 변환
            if isinstance(items, dict):
                items = [items]
            
            # 지역 이름 강제 태깅 (KDCA의 sidoNm이 비정상적일 경우 대비)
            for item in items:
                item["sidoNm"] = sido_nm
                item["sidoCd"] = sido_cd
                all_items.append(item)
        except:
            continue

    final_data = {"response": {"body": {"items": {"item": all_items}}}}
    set_to_cache(cache_key, final_data)
    return final_data

def fetch_kdca_period_spread(start_year="2023", end_year="2023", period_type="2"):
    """
    전파 지도용: 월별(2)/주별(3) 확진자 추이를 전국 모든 지역에 대해 가져옵니다.
    """
    cache_key = f"period_spread_{start_year}_{end_year}_{period_type}"
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data

    # 질병관리청 고유 지역 코드
    SIDO_MAPPING = {
        '01': '서울', '02': '부산', '03': '대구', '04': '인천', 
        '05': '광주', '06': '대전', '07': '울산', '08': '경기', 
        '09': '강원', '10': '충북', '11': '충남', '12': '전북', 
        '13': '전남', '14': '경북', '15': '경남', '16': '제주', '17': '세종'
    }
    
    spread_data = []
    
    for sido_cd, sido_nm in SIDO_MAPPING.items():
        url = f"{BASE_URL}/PeriodBasic"
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 10000,
            "resType": "2",
            "searchPeriodType": period_type,
            "searchStartYear": start_year,
            "searchEndYear": end_year,
            "searchSidoCd": sido_cd
        }
        try:
            res = requests.get(url, params=params, verify=False, timeout=5)
            if res.status_code != 200:
                continue
            p_data = res.json()
            # DATATYPE_PARAMETER_ERROR 등 에러 응답이면 패스
            if p_data.get("response", {}).get("header", {}).get("resultCode") != "00":
                continue
                
            p_items = p_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            
            # 수신된 데이터가 있으면 결과 리스트에 지역명을 태깅하여 추가
            for p_item in p_items:
                p_item["sidoNm"] = sido_nm
                p_item["sidoCd"] = sido_cd
                spread_data.append(p_item)
        except Exception as e:
            continue

    set_to_cache(cache_key, spread_data)
    return spread_data
