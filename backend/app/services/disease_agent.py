import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import BingGroundingTool

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")
DISEASE_ANALYZER_AGENT_ID = os.getenv("DISEASE_ANALYZER_AGENT_ID")
MAP_ANALYZER_AGENT_ID = os.getenv("MAP_ANALYZER_AGENT_ID")

def analyze_disease_risk_with_grounding(disease_keyword="독감"):
    if not PROJECT_ENDPOINT:
        return {"error": "Azure 파라미터가 설정되지 않았습니다 (.env 확인)"}
        
    try:
        project_client = AIProjectClient(
            endpoint=PROJECT_ENDPOINT,
            credential=DefaultAzureCredential()
        )
        
        if not DISEASE_ANALYZER_AGENT_ID:
            return {"error": "DISEASE_ANALYZER_AGENT_ID 환경변수가 없습니다."}
        
        thread = project_client.agents.threads.create()
        
        prompt = f"""
당신은 통계 분석 봇입니다. 최신 뉴스를 검색하여 한국의 '{disease_keyword}' 관련 동향을 아래 3가지 항목으로 구조화하여 추출해 주세요.

주의: 주관적인 해석이나 조언을 절대 추가하지 마세요. 오직 언론에 보도된 숫자, 발표된 팩트, 공식 기관의 안내사항만 그대로 요약해야 합니다.

1. 최근 언론 보도 요약 (최근 확진자 수 변화, 주요 발생 지역 등 기사에 보도된 팩트)
2. 기사에 나타난 주요 동향 (사회적/집단 감염 여부 등 동향)
3. 보도된 방역 당국의 당부사항 (기사에서 안내하는 보건 권고사항)

응답은 반드시 아래와 같은 HTML 구조로만 작성해 주세요 (마크다운 ```html 등을 쓰지 말고 순수 HTML 태그만 반환할 것):
<h3>📈 최근 언론 보도 요약</h3>
<p>...</p>
<h3>📰 기사에 나타난 주요 동향</h3>
<p>...</p>
<h3>📢 보도된 방역 당국의 당부사항</h3>
<ul>
  <li>...</li>
</ul>
"""
        message = project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        run = project_client.agents.runs.create_and_process(
            thread_id=thread.id, 
            agent_id=DISEASE_ANALYZER_AGENT_ID
        )
        
        if run.status == "failed":
            return {"error": f"Agent 실행 실패: {run.last_error}"}
            
        messages_list = list(project_client.agents.messages.list(thread_id=thread.id))
        latest_msg = messages_list[0]
        
        content_text = ""
        citations = []
        
        for content_item in latest_msg.content:
            if hasattr(content_item, "text") and content_item.type == "text":
                content_text += content_item.text.value
                if hasattr(content_item.text, "annotations"):
                    for annotation in content_item.text.annotations:
                        if hasattr(annotation, "url_citation"):
                            citations.append({
                                "url": getattr(annotation.url_citation, "url", ""),
                                "title": getattr(annotation.url_citation, "title", "")
                            })
                            
        try:
            project_client.agents.threads.delete(thread.id)
        except Exception:
            pass

        return {
            "ai_analysis": content_text,
            "citations": citations
        }
        
    except Exception as e:
        return {"error": str(e)}

def get_disease_map_data_from_agent(disease_keyword, base_data_str="", last_updated=None, previous_data=None):
    if not PROJECT_ENDPOINT:
        return {"error": "Azure 파라미터가 설정되지 않았습니다."}
        
    try:
        import json
        project_client = AIProjectClient(
            endpoint=PROJECT_ENDPOINT,
            credential=DefaultAzureCredential()
        )
        
        if not MAP_ANALYZER_AGENT_ID:
            return {"error": "MAP_ANALYZER_AGENT_ID 환경변수가 없습니다."}
        
        thread = project_client.agents.threads.create()
        
        incremental_prompt = ""
        if last_updated and previous_data:
            incremental_prompt = f"""
            
[증분 검색(Incremental Search) 지시사항]
- 가장 최근 분석 시간은 '{last_updated}' 였습니다.
- 빙 검색(Bing Search)을 사용할 때, 반드시 '{last_updated}' 이후에 작성되거나 발행된 최신 뉴스만 집중적으로 검색하세요.
- 이전 상태 데이터는 다음과 같습니다:
{json.dumps(previous_data, ensure_ascii=False)}
- 새로운 확산 동향이나 유의미한 위험도 변화가 없다면 이전 상태 데이터를 그대로 유지하세요. 변화가 있다면 반영하여 전체 JSON 배열을 반환하세요.
            """

        prompt = f'''최근 한국의 {disease_keyword} 유행 관련 최신 뉴스를 찾아보고, 각 지역별(서울, 경기, 부산 등) 위험도(High, Medium, Low) 및 전파 방향을 분석하세요.{incremental_prompt}

다음은 공공 API를 통해 수집된 실제 통계 데이터입니다. 데이터가 있는 경우 이를 최대한 참고하세요:
{base_data_str}

반환할 JSON 구조 예시:
[
  {{
    "name": "서울",
    "coordinates": [126.9780, 37.5665],
    "cases": 120, // 위 통계 데이터에 없으면 null 처리
    "risk_level": "High"
  }},
  {{
    "name": "경기",
    "coordinates": [127.2089, 37.2751],
    "cases": null,
    "risk_level": "Medium",
    "spread_to": ["인천", "충남"] // 여기서 다른 지역으로 확산세가 뚜렷할 경우에만 배열로 추가
  }}
]
반드시 위 구조의 JSON 배열만 전체로 반환하세요.'''
        message = project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        run = project_client.agents.runs.create_and_process(
            thread_id=thread.id, 
            agent_id=MAP_ANALYZER_AGENT_ID
        )
        
        if run.status == "failed":
            return {"error": f"Agent 실행 실패: {run.last_error}"}
            
        messages_list = list(project_client.agents.messages.list(thread_id=thread.id))
        latest_msg = messages_list[0]
        
        content_text = ""
        for content_item in latest_msg.content:
            if hasattr(content_item, "text") and content_item.type == "text":
                content_text += content_item.text.value
                
        content_text = content_text.strip()
        if content_text.startswith("`json"):
            content_text = content_text[7:]
        if content_text.startswith("`"):
            content_text = content_text[3:]
        if content_text.endswith("`"):
            content_text = content_text[:-3]
            
        try:
            project_client.agents.threads.delete(thread.id)
        except Exception:
            pass

        return json.loads(content_text.strip())
        
    except Exception as e:
        return {"error": str(e)}
