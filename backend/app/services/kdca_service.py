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
            # KDCA API는 특정 지역을 요청해도 항상 '00(전국)' 합계 데이터를 맨 위에 같이 반환함.
            for item in items:
                # 전국 데이터는 무시하고, 실제 요청한 지역의 데이터만 사용
                if item.get("sidoCd") == "00":
                    continue
                # 실제 데이터의 sidoNm/sidoCd를 강제 태깅하여 일관성 유지
                item["sidoNm"] = sido_nm
                item["sidoCd"] = sido_cd
                all_items.append(item)
        except:
            continue

    final_data = {"response": {"body": {"items": {"item": all_items}}}}
    set_to_cache(cache_key, final_data)
    return final_data

def fetch_kdca_gender_status(year="2024", search_type="1"):
    cache_key = f"gender_status_{year}_{search_type}"
    cached_data = get_from_cache(cache_key)
    if cached_data: return cached_data
    
    url = f"{BASE_URL}/Gender"
    params = {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 10000, "resType": "2", "searchType": search_type, "searchYear": year}
    try:
        res = requests.get(url, params=params, verify=False, timeout=10)
        data = res.json()
        set_to_cache(cache_key, data)
        return data
    except Exception as e:
        return {}

def fetch_kdca_age_status(year="2024", search_type="1"):
    cache_key = f"age_status_{year}_{search_type}"
    cached_data = get_from_cache(cache_key)
    if cached_data: return cached_data
    
    url = f"{BASE_URL}/Age"
    params = {"serviceKey": API_KEY, "pageNo": 1, "numOfRows": 10000, "resType": "2", "searchType": search_type, "searchYear": year}
    try:
        res = requests.get(url, params=params, verify=False, timeout=10)
        data = res.json()
        set_to_cache(cache_key, data)
        return data
    except Exception as e:
        return {}

def fetch_kdca_period_region(start_year="2023", end_year="2024", period_type="2"):
    """
    월별(2) 지역 확산 데이터. KDCA는 PeriodBasic에서 지역 구분을 제공하지 않으므로,
    전국 월별 데이터를 가져온 뒤, 해당 연도의 실제 지역별 누적 확진자 비율(가중치)을
    계산하여 월별 수치를 지역별로 비례 배분합니다.
    """
    cache_key = f"period_region_{start_year}_{end_year}_{period_type}_weighted"
    cached_data = get_from_cache(cache_key)
    if cached_data: return cached_data
    
    spread_data = []
    years = range(int(start_year), int(end_year) + 1)
    
    for year in years:
        year_str = str(year)
        
        # 1. 해당 연도의 지역별 실제 누적 데이터 가져오기 (가중치 계산용)
        region_data_response = fetch_kdca_region_status(year=year_str, search_type="1")
        region_items = region_data_response.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if isinstance(region_items, dict): region_items = [region_items]
        
        disease_region_weights = {} # { "수두": {"서울": 0.2, "경기": 0.3}, ... }
        disease_total_annual = {}   # { "수두": 10000, ... }
        
        for r_item in region_items:
            sido_nm = r_item.get("sidoNm")
            icd_nm = r_item.get("icdNm")
            sido_cd = r_item.get("sidoCd")
            
            raw_val = str(r_item.get("resultVal", 0)).replace(",", "").replace("-", "0")
            try:
                val = int(raw_val)
            except:
                val = 0
            
            if sido_nm and sido_nm not in ["합계", "전국", "검역"] and sido_cd != "00" and val > 0:
                if icd_nm not in disease_total_annual:
                    disease_total_annual[icd_nm] = 0
                    disease_region_weights[icd_nm] = {}
                
                disease_total_annual[icd_nm] += val
                disease_region_weights[icd_nm][sido_nm] = val
                
        # 가중치(비율)로 변환
        for icd_nm, regions_dict in disease_region_weights.items():
            total = disease_total_annual[icd_nm]
            for region, count in regions_dict.items():
                disease_region_weights[icd_nm][region] = count / total if total > 0 else 0

        # 2. 해당 연도의 전국 월별 통계 가져오기
        url = f"{BASE_URL}/PeriodBasic"
        params = {
            "serviceKey": API_KEY,
            "pageNo": 1,
            "numOfRows": 10000,
            "resType": "2",
            "searchPeriodType": period_type,
            "searchStartYear": year_str,
            "searchEndYear": year_str,
        }
        
        try:
            res = requests.get(url, params=params, verify=False, timeout=15)
            if res.status_code != 200: continue
            p_data = res.json()
            if p_data.get("response", {}).get("header", {}).get("resultCode") != "00": continue
                
            p_items = p_data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if isinstance(p_items, dict): p_items = [p_items]
            
            # 3. 월별 전국 총합을 지역별 가중치로 분배
            for p_item in p_items:
                icd_nm = p_item.get("icdNm")
                period = p_item.get("period")
                raw_monthly = str(p_item.get("resultVal", 0)).replace(",", "").replace("-", "0")
                try:
                    monthly_total = int(raw_monthly)
                except:
                    monthly_total = 0
                
                if monthly_total > 0 and icd_nm in disease_region_weights:
                    weights = disease_region_weights[icd_nm]
                    for sido_nm, weight in weights.items():
                        allocated_val = int(round(monthly_total * weight))
                        if allocated_val > 0:
                            spread_data.append({
                                "period": period,
                                "icdNm": icd_nm,
                                "sidoNm": sido_nm,
                                "sidoCd": "mapped", # 식별용
                                "resultVal": str(allocated_val)
                            })
        except Exception as e:
            print(f"PeriodBasic Fetch Error: {e}")
            continue

    set_to_cache(cache_key, spread_data)
    return spread_data
