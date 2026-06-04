import json
from app.services.ingestion import fetch_kdca_stats
from app.services.disease_agent import get_disease_map_data_from_agent
from app.services.cache_manager import get_disease_cache, update_disease_cache

def get_hybrid_map_data(disease_keyword, force_update=False):
    """
    1. 캐시(cache) 확인: 최근 검색 기록이 있으면 해당 데이터와 시간 반환 (강제 갱신 제외)
    2. KDCA API 등에서 정량 데이터를 수집
    3. 수집된 데이터를 AI Agent에 전달 (이전 분석 데이터 및 시간이 존재하면 증분 검색)
    4. AI Agent가 실제 데이터 + 빙 검색 뉴스를 기반으로 JSON 분석 결과를 갱신 반환
    """
    
    # 1. 캐시 확인
    cached_info = get_disease_cache(disease_keyword)
    last_updated = None
    previous_data = None
    
    if cached_info:
        if not force_update:
            # 강제 업데이트가 아니면 바로 캐시된 데이터 리턴
            return {
                "status": "success",
                "disease": disease_keyword,
                "data": cached_info["data"],
                "last_updated": cached_info["last_updated"],
                "cached": True
            }
        # 강제 업데이트인 경우, 이전 데이터를 에이전트에 넘겨주어 증분 갱신 유도
        last_updated = cached_info["last_updated"]
        previous_data = cached_info["data"]
        
    # 2. 정량 데이터 수집
    base_data_str = ""
    if disease_keyword in ["코로나19", "코로나"]:
        try:
            stats = fetch_kdca_stats()
            items = stats.get("items", []) if isinstance(stats, dict) else stats
            base_data_str = json.dumps(items, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to fetch KDCA stats: {e}")
            base_data_str = "No API data available."
    else:
        base_data_str = f"No direct quantitative API available for {disease_keyword}. Rely on news grounding."
        
    # 3. AI Agent를 통해 하이브리드 JSON 분석 데이터 생성 (증분 반영)
    result_json = get_disease_map_data_from_agent(
        disease_keyword, 
        base_data_str=base_data_str,
        last_updated=last_updated,
        previous_data=previous_data
    )
    
    # 에러가 발생한 경우 예외 처리
    if isinstance(result_json, dict) and "error" in result_json:
        return {"status": "error", "message": result_json["error"], "data": []}
        
    # 4. 성공적으로 가져오면 캐시 업데이트
    update_disease_cache(disease_keyword, result_json)
    
    # 업데이트 직후 캐시 정보를 다시 로드해서 리턴
    new_cached_info = get_disease_cache(disease_keyword)
    
    return {
        "status": "success",
        "disease": disease_keyword,
        "data": new_cached_info["data"],
        "last_updated": new_cached_info["last_updated"],
        "cached": False
    }
