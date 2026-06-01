import os
import requests
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv

# 질병관리청 서버의 구형 SSL 연동을 위한 어댑터 설정
class CustomSSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = urllib3.util.ssl_.create_urllib3_context()
        # ssl.OP_LEGACY_SERVER_CONNECT 옵션 활성화 (서버의 구형 SSL 재협상 허용)
        ctx.options |= 0x4  
        kwargs['ssl_context'] = ctx
        return super(CustomSSLAdapter, self).init_poolmanager(*args, **kwargs)

# .env 파일에서 환경 변수를 불러옵니다.
load_dotenv()

KDCA_API_KEY = os.getenv("KDCA_API_KEY")
KDCA_CONTENT_TOKEN = os.getenv("KDCA_CONTENT_TOKEN")
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

def fetch_kdca_disease_contents():
    """
    질병관리청 API를 통해 요청받은 특정 감염병 ID들의 데이터를 가져옵니다.
    """
    target_ids = [
        {"id": "6680", "name": "급성호흡기바이러스감염증"},
        {"id": "5279", "name": "신증후군출혈열(한타바이러스감염증)"},
        {"id": "6257", "name": "해외여행 시 주의해야 할 감염병! 알려드리겠습니다!"},
        {"id": "6525", "name": "직업성 호흡기질환(직업성 감염성 폐질환)"},
        {"id": "6491", "name": "건막염(감염성 건막염)"},
        {"id": "6677", "name": "코로나바이러스감염증-19"}
    ]
    
    # TOKEN이 아직 설정되지 않은 경우 Mock Data 반환
    if not KDCA_CONTENT_TOKEN:
        print("KDCA_CONTENT_TOKEN이 설정되지 않아 Mock Data를 반환합니다.")
        return {
            "status": "success",
            "message": "Mock data returned because API Token is missing.",
            "data": target_ids
        }

    results = []
    base_url = "https://api.kdca.go.kr/api/provide/healthInfo"
    
    # SSL 오류 해결을 위해 Session에 Custom Adapter 연결
    session = requests.Session()
    session.mount('https://', CustomSSLAdapter())
    
    # 실제 API 연동 시
    for target in target_ids:
        try:
            params = {
                'TOKEN': KDCA_CONTENT_TOKEN.replace('&cntntsSn', '').strip(), # 만약 .env에 &cntntsSn이 붙어있다면 제거
                'cntntsSn': target["id"] # 키 이름을 id가 아닌 cntntsSn으로 수정
            }
            response = session.get(base_url, params=params, timeout=5)
            response.raise_for_status()
            
            # 질병관리청 API가 XML로 응답하므로 XML 파싱 추가
            import xml.etree.ElementTree as ET
            api_data = {}
            try:
                # 만약을 위해 JSON 시도
                api_data = response.json()
            except ValueError:
                # JSON 파싱 실패 시 XML로 파싱
                root = ET.fromstring(response.text)
                svc = root.find("svc")
                if svc is not None:
                    api_data["title"] = svc.findtext("CNTNTSSJ")
                    api_data["id"] = svc.findtext("CNTNTS_SN")
                    
                    content_list = []
                    cl_list = svc.find("cntntsClList")
                    if cl_list is not None:
                        for cl in cl_list.findall("cntntsCl"):
                            nm = cl.findtext("CNTNTS_CL_NM")
                            cn = cl.findtext("CNTNTS_CL_CN")
                            if nm and cn:
                                content_list.append(f"[{nm}]\n{cn}")
                    
                    api_data["full_text"] = "\n\n".join(content_list)
                else:
                    # 에러 메시지나 다른 형태일 경우
                    api_data["raw_xml"] = response.text[:500]
            
            results.append({
                "id": target["id"],
                "name": target["name"],
                "details": api_data
            })
        except Exception as e:
            print(f"Failed to fetch ID {target['id']}: {e}")
            # 에러 발생 시에도 기본 정보는 포함
            results.append({
                "id": target["id"],
                "name": target["name"],
                "error": str(e)
            })
            
    return {
        "status": "success",
        "data": results
    }
