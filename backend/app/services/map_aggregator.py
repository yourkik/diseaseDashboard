import json
from app.services.ingestion import fetch_kdca_stats
from app.services.disease_agent import get_disease_map_data_from_agent

def get_hybrid_map_data(disease_keyword):
    """
    1. KDCA API 등에서 정량 데이터를 수집
    2. 수집된 데이터를 문자열(JSON)로 변환하여 AI Agent에 전달
    3. AI Agent가 실제 데이터 + 빙 검색 뉴스를 기반으로 JSON 분석 결과(위험도, 전파경로 등)를 반환
    """
    
    # 1. 정량 데이터 수집
    # 현재 fetch_kdca_stats()는 주로 코로나19 또는 전반적 통계를 가져옴
    base_data_str = ""
    if disease_keyword in ["코로나19", "코로나"]:
        try:
            stats = fetch_kdca_stats()
            # items 배열만 추출 (가독성을 위해 데이터 압축)
            items = stats.get("items", []) if isinstance(stats, dict) else stats
            base_data_str = json.dumps(items, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to fetch KDCA stats: {e}")
            base_data_str = "No API data available."
    else:
        # 다른 질병에 대해서는 현재 전용 확진자 API가 연결되지 않음
        base_data_str = f"No direct quantitative API available for {disease_keyword}. Rely on news grounding."
        
    # 2. AI Agent를 통해 하이브리드 JSON 분석 데이터 생성
    result_json = get_disease_map_data_from_agent(disease_keyword, base_data_str=base_data_str)
    
    # 에러가 발생한 경우 예외 처리
    if isinstance(result_json, dict) and "error" in result_json:
        return {"status": "error", "message": result_json["error"], "data": []}
        
    # 3. 반환
    return {
        "status": "success",
        "disease": disease_keyword,
        "data": result_json
    }
