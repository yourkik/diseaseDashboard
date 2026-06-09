import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import BingGroundingTool

env_path = Path('D:/학업 관련 파일/자료 모음/dataSchool/3차 프로젝트/diseaseDashboard/backend/.env')
load_dotenv(dotenv_path=env_path)

PROJECT_ENDPOINT = os.getenv('PROJECT_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')
BING_CONNECTION_NAME = os.getenv('BING_CONNECTION_NAME')

if PROJECT_ENDPOINT:
    project_client = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential()
    )
    
    bing_connection = project_client.connections.get(BING_CONNECTION_NAME)
    conn_id = bing_connection.id

    agent_disease = project_client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name='sentinel-disease-analyzer-permanent',
        instructions='당신은 언론 보도 데이터를 분석하여 객관적인 동향(Trend) 통계를 추출하는 데이터 사이언티스트 AI입니다. 대시보드 시각화를 위해 기사 본문에 언급된 통계적 팩트(수치, 발표 내용)만 있는 그대로 요약하세요. 답변은 반드시 출처를 포함해야 하며, 프론트엔드에서 직접 렌더링할 수 있도록 Markdown 대신 기본 HTML 태그(<h3>, <ul>, <li>, <p>, <strong>)만 사용하여 구조화해 주세요.',
        tools=BingGroundingTool(connection_id=conn_id).definitions
    )

    agent_map = project_client.agents.create_agent(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        name='sentinel-map-analyzer-permanent',
        instructions='당신은 감염병 대시보드 지도 시각화용 데이터를 생성하는 AI입니다. 검색 결과와 사용자 제공 데이터를 종합하여 반드시 JSON 배열 형식으로만 응답하세요. 백틱(```)이나 추가 텍스트 없이 오직 유효한 JSON 배열만 출력해야 합니다.',
        tools=BingGroundingTool(connection_id=conn_id).definitions
    )
    
    with open(env_path, 'a', encoding='utf-8') as f:
        f.write(f'\nDISEASE_ANALYZER_AGENT_ID="{agent_disease.id}"')
        f.write(f'\nMAP_ANALYZER_AGENT_ID="{agent_map.id}"\n')
        
    print(f'DISEASE_ANALYZER_AGENT_ID: {agent_disease.id}')
    print(f'MAP_ANALYZER_AGENT_ID: {agent_map.id}')
