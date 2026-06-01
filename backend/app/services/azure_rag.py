import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import BingGroundingTool

load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")

def analyze_disease_risk_with_grounding(disease_keyword="독감"):
    if not PROJECT_ENDPOINT:
        return {"error": "Azure 파라미터가 설정되지 않았습니다. (.env 확인)"}
        
    try:
        # 최신 2.1.0 SDK 방식
        project_client = AIProjectClient(
            endpoint=PROJECT_ENDPOINT,
            credential=DefaultAzureCredential()
        )
        
        # 빙 검색 연결 가져오기
        bing_connection = project_client.connections.get(BING_CONNECTION_NAME)
        conn_id = bing_connection.id
        
        # 에이전트 생성
        agent = project_client.agents.create_agent(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            name="sentinel-disease-analyzer",
            instructions="당신은 감염병 대시보드의 실시간 위험도 분석 AI입니다. 웹 검색 도구를 적극 활용하여 최신 뉴스를 기반으로 위험도를 분석해 주세요. 답변에는 반드시 출처를 포함해야 합니다.",
            tools=[BingGroundingTool(connection_id=conn_id)]
        )
        
        # 쓰레드 및 메시지 생성
        thread = project_client.agents.create_thread()
        message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=f"최근 한국의 {disease_keyword} 유행 관련 최신 뉴스를 찾아보고 위험도를 분석한 뒤 리포트를 작성해줘."
        )
        
        # 에이전트 실행
        run = project_client.agents.create_and_process_run(
            thread_id=thread.id, 
            agent_id=agent.id
        )
        
        if run.status == "failed":
            return {"error": f"Agent 실행 실패: {run.last_error}"}
            
        messages = project_client.agents.list_messages(thread_id=thread.id)
        latest_msg = messages.data[0]
        
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
