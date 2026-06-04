import os
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey, exceptions

# 1. Azure Cosmos DB 인증 인프라 정보 바인딩
URL = "https://team5-db.documents.azure.com:443/"
KEY = "w1WwzUWQvaaR8ohmVHWI4bFH7jqqHyZ8MPagBOVfuPUKsFx53iEM3R9WBcIePwcMZiTs9aP94E8eACDbnVJAMw=="
DATABASE_NAME = "DiseaseDB"
CONTAINER_NAME = "DiseaseStats"

try:
    # 클라이언트 인스턴스 초기화 및 엔드포인트 커넥션 확보
    client = CosmosClient(URL, credential=KEY)
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_NAME)
    print("Azure Cosmos DB에 연결되었습니다.")
except Exception as e:
    print(f"데이터베이스 연결에 실패했습니다...: {e}")

def load_ai_json_to_cosmos(region_code, disease_name, count, danger_level, news_summary=""):
    """
    아키텍처 2번 레벨의 Azure OpenAI JSON 추출 스펙을 완전하게 반영하여
    Cosmos DB NoSQL 컨테이너에 도큐먼트를 Bulk Insert 하는 파이프라인 함수입니다.
    """
    
    # 2. NoSQL 문서 구조화 (JSON 데이터 모델링)
    # Cosmos DB는 고유 식별자인 'id' 필드가 문자열 규격으로 반드시 필수 유입되어야 합니다.
    document_id = f"{region_code}_{disease_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    disease_document = {
        "id": document_id,
        "region": region_code,           # 분할 키(Partition Key)와 정확하게 일치해야 합니다. (예: 'SEOUL', 'GYEONGGI')
        "diseaseName": disease_name,     # 질병명 (예: '수두', '독감')
        "count": int(count),             # 확진자 집계 수치
        "dangerLevel": danger_level,     # AI 분석 기반 위험도 등급 (예: 'Level 2', '주의')
        "newsSummary": news_summary,     # RAG 기반 추출 뉴스 요약문
        "timestamp": datetime.utcnow().isoformat() + "Z" # ISO 8601 시간 규격
    }
    
    try:
        # 3. 도큐먼트 Upsert (데이터 삽입 및 무결성 확보)
        container.upsert_item(body=disease_document)
        print(f"[적재 완료] {region_code} 지역 - {disease_name} 데이터가 Cosmos DB에 저장되었습니다.")
        
        # 4. 아키텍처 4번 레이어 연동: 위험도 임계치 검사 후 알림 트리거 연계
        # 이 시점에서 확진자 수(count)나 위험도(dangerLevel)를 판별하여 후행 알림 인프라로 던집니다.
        if int(count) >= 500 or danger_level in ["경고", "danger", "Level 3"]:
            trigger_azure_logic_apps_alert(disease_document)
            
    except exceptions.CosmosHttpResponseError as e:
        print(f"Cosmos DB 적재 프로세스 중 예외 오류 발생: {e.message}")

def trigger_azure_logic_apps_alert(data_payload):
    """
    아키텍처 4번 서비스 제공 섹션의 [Azure Logic Apps: 보건소 자동 알림] 
    엔드포인트 인터페이스와 데이터 트랜잭션을 맺는 헬퍼 함수입니다.
    """
    print(f"🚨 [위험 임계치 초과 발생] 관할 보건소 알림 발송을 시작합니다.")
    print(f"✉️ Azure Logic Apps HTTP 트리거 엔드포인트로 페이로드 송신 프로세스 구동 가동.")
    # 실제 연동 시: requests.post(LOGIC_APPS_URL, json=data_payload)

# 실행 모의 테스트 예시
# load_ai_json_to_cosmos("GYEONGGI", "수두", 650, "Level 2", "경기도 내 수두 집단 감염 조짐 주의 보도")