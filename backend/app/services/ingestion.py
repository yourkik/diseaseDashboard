import os
import requests
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()

KDCA_API_KEY = os.getenv("KDCA_API_KEY")
BING_SEARCH_API_KEY = os.getenv("BING_SEARCH_API_KEY")

def fetch_kdca_stats():
    """
    공공데이터포털(질병관리청) 코로나19/감염병 발생 동향 API 호출
    """
    if not KDCA_API_KEY or KDCA_API_KEY == "your_kdca_api_key_here":
        # API Key가 없을 경우 Mock Data 반환 (개발 편의용)
        return {
            "resultCode": "00",
            "resultMsg": "NORMAL SERVICE.",
            "items": [
                {"stateDt": "20240529", "stateTime": "00:00", "decideCnt": "15034", "deathCnt": "12", "region": "Seoul"}
            ]
        }
        
    url = "http://apis.data.go.kr/1352000/ODMS_COVID_04/callCovid04Api"
    params = {'serviceKey': KDCA_API_KEY, 'pageNo': '1', 'numOfRows': '10', 'apiType': 'JSON'}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_bing_news(query="감염병 OR 코로나 OR 독감"):
    """
    Bing News Search API를 호출하여 최신 국내외 뉴스 수집
    """
    if not BING_SEARCH_API_KEY or BING_SEARCH_API_KEY == "your_bing_api_key_here":
        raise Exception("Bing API Key is missing")
        
    search_url = "https://api.bing.microsoft.com/v7.0/news/search"
    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_API_KEY}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML", "mkt": "ko-KR"}
    
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def fetch_gdelt_news(query="disease OR virus OR outbreak"):
    """
    무료 오픈소스인 GDELT Project API를 호출하여 글로벌 뉴스 수집 (API Key 불필요)
    Bing API 실패 시 Fallback 또는 병행 데이터 소스로 활용
    """
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "timespan": "24h",
        "maxrecords": "10"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Bing API 응답 포맷과 유사하게 맞추기 위한 정제
        articles = data.get("articles", [])
        formatted_news = []
        for art in articles:
            formatted_news.append({
                "name": art.get("title", "No Title"),
                "url": art.get("url", ""),
                "description": "GDELT 데이터 발췌 기사입니다.", # GDELT는 본문 요약을 제공하지 않는 경우가 많음
                "datePublished": art.get("seendate", ""),
                "source": "GDELT"
            })
        return {"value": formatted_news}
    except Exception as e:
        print(f"GDELT API Error: {e}")
        return {"value": []}

def get_integrated_news(query="감염병 OR 코로나 OR 독감", gdelt_query="disease OR virus OR outbreak"):
    """
    Bing API와 GDELT API를 병행(Parallel) 혹은 대체(Fallback) 방식으로 통합 호출
    """
    news_results = []
    
    # 1. Bing API 시도
    if BING_SEARCH_API_KEY and BING_SEARCH_API_KEY != "your_bing_api_key_here":
        try:
            bing_data = fetch_bing_news(query)
            for item in bing_data.get("value", []):
                item['source'] = 'Bing'
                news_results.append(item)
        except Exception as e:
            print(f"Bing API 실패 (Fallback으로 넘어감): {e}")
    else:
        print("Bing API Key가 없어 GDELT로만 뉴스를 수집합니다.")
        
    # 2. Bing 결과가 없거나 부족할 경우, 혹은 항상 병행할 경우 GDELT 호출
    # 병행 수집을 원하므로 GDELT도 함께 수집하여 리스트에 병합
    gdelt_data = fetch_gdelt_news(gdelt_query)
    news_results.extend(gdelt_data.get("value", []))
    
    # 만약 둘 다 실패해서 결과가 0개라면 Mock Data 반환
    if not news_results:
        print("모든 API 수집 실패, Mock Data를 반환합니다.")
        return {
            "value": [
                {"name": "[모의] 올 겨울 독감 유행 조짐...", "description": "전국적으로 독감 환자 급증.", "source": "Mock"}
            ]
        }
        
    return {"value": news_results[:15]} # 최대 15개 최신 기사 반환
