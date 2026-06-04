import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import BingGroundingTool

load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")

def analyze_disease_risk_with_grounding(disease_keyword="?낃컧"):
    if not PROJECT_ENDPOINT:
        return {"error": "Azure ?뚮씪誘명꽣媛 ?ㅼ젙?섏? ?딆븯?듬땲?? (.env ?뺤씤)"}
        
    try:
        # AI Foundry v2 SDK: Connection String ?먮뒗 Endpoint URL??endpoint ?뚮씪誘명꽣???섍퉩?덈떎.
        project_client = AIProjectClient(
            endpoint=PROJECT_ENDPOINT,
            credential=DefaultAzureCredential()
        )
        
        # 鍮?寃???곌껐 媛?몄삤湲?        bing_connection = project_client.connections.get(BING_CONNECTION_NAME)
        conn_id = bing_connection.id
        
        # ?먯씠?꾪듃 ?앹꽦
        agent = project_client.agents.create_agent(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            name="sentinel-disease-analyzer",
            instructions="?뱀떊? 媛먯뿼蹂???쒕낫?쒖쓽 ?ㅼ떆媛??꾪뿕??遺꾩꽍 AI?낅땲?? ??寃???꾧뎄瑜??곴레 ?쒖슜?섏뿬 理쒖떊 ?댁뒪瑜?湲곕컲?쇰줈 ?꾪뿕?꾨? 遺꾩꽍??二쇱꽭?? ?듬??먮뒗 諛섎뱶??異쒖쿂瑜??ы븿?댁빞 ?⑸땲??",
            tools=BingGroundingTool(connection_id=conn_id).definitions
        )
        
        # ?곕젅??諛?硫붿떆吏 ?앹꽦
        thread = project_client.agents.threads.create()
        message = project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"理쒓렐 ?쒓뎅??{disease_keyword} ?좏뻾 愿??理쒖떊 ?댁뒪瑜?李얠븘蹂닿퀬 ?꾪뿕?꾨? 遺꾩꽍????由ы룷?몃? ?묒꽦?댁쨾."
        )
        
        # ?먯씠?꾪듃 ?ㅽ뻾
        run = project_client.agents.runs.create_and_process(
            thread_id=thread.id, 
            agent_id=agent.id
        )
        
        if run.status == "failed":
            return {"error": f"Agent ?ㅽ뻾 ?ㅽ뙣: {run.last_error}"}
            
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
        
        bing_connection = project_client.connections.get(BING_CONNECTION_NAME)
        conn_id = bing_connection.id
        
        agent = project_client.agents.create_agent(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            name="sentinel-map-analyzer",
            instructions="당신은 감염병 대시보드 지도 시각화용 데이터를 생성하는 AI입니다. 검색 결과와 사용자 제공 데이터를 종합하여 반드시 JSON 배열 형식으로만 응답하세요. 백틱(```)이나 추가 텍스트 없이 오직 유효한 JSON 배열만 출력해야 합니다.",
            tools=BingGroundingTool(connection_id=conn_id).definitions
        )
        
        thread = project_client.agents.threads.create()
        
        # 이전 데이터 유무에 따른 동적 프롬프트 생성
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
            agent_id=agent.id
        )
        
        if run.status == "failed":
            return {"error": f"Agent 실행 실패: {run.last_error}"}
            
        messages_list = list(project_client.agents.messages.list(thread_id=thread.id))
        latest_msg = messages_list[0]
        
        content_text = ""
        for content_item in latest_msg.content:
            if hasattr(content_item, "text") and content_item.type == "text":
                content_text += content_item.text.value
                
        # 파싱 (백틱 제거 등)
        content_text = content_text.strip()
        if content_text.startswith("`json"):
            content_text = content_text[7:]
        if content_text.startswith("`"):
            content_text = content_text[3:]
        if content_text.endswith("`"):
            content_text = content_text[:-3]
            
        return json.loads(content_text.strip())
        
    except Exception as e:
        return {"error": str(e)}
