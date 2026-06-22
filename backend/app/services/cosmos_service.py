import os
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

COSMOS_CONNECTION_STRING = os.getenv("COSMOS_DB_CONNECTION_STRING")
DATABASE_NAME = os.getenv("COSMOS_DB_DATABASE_NAME", "SentinelDB") # 사용자에 맞게 수정 가능

client = None
news_container = None
stats_container = None

if COSMOS_CONNECTION_STRING:
    try:
        client = CosmosClient.from_connection_string(COSMOS_CONNECTION_STRING)
        
        # NewsDB 데이터베이스 -> Items 컨테이너
        news_db = client.get_database_client("NewsDB")
        news_container = news_db.get_container_client("Items")
        
        # DiseaseDB 데이터베이스 -> DiseaseStats 컨테이너
        disease_db = client.get_database_client("DiseaseDB")
        stats_container = disease_db.get_container_client("DiseaseStats")
        
        print("Cosmos DB에 성공적으로 연결되었습니다.")
    except Exception as e:
        print(f"Cosmos DB 초기화 오류: {e}")

def get_latest_news_from_cosmos(disease: str = None, region: str = None, limit: int = 5):
    """
    Cosmos DB의 NewsDB 컨테이너에서 조건에 맞는 최신 뉴스를 가져옵니다.
    """
    if not news_container:
        return []
    
    query = "SELECT * FROM c WHERE 1=1"
    parameters = []
    
    if disease and disease != "전체":
        query += " AND CONTAINS(c.disease, @disease)"
        parameters.append({"name": "@disease", "value": disease})
        
    if region and region != "전국 공통":
        query += " AND (CONTAINS(c.wide_region, @region) OR CONTAINS(c.detail_region, @region) OR c.wide_region = '전국 공통' OR NOT IS_DEFINED(c.wide_region))"
        parameters.append({"name": "@region", "value": region[:2]}) # 예: 서울특별시 -> 서울
        
    query += " ORDER BY c.published_at DESC OFFSET 0 LIMIT @limit"
    parameters.append({"name": "@limit", "value": limit})
    
    try:
        items = list(news_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return items
    except exceptions.CosmosHttpResponseError as e:
        print(f"NewsDB 조회 에러: {e.message}")
        return []

def get_all_disease_stats():
    """
    Cosmos DB의 DiseaseStats 컨테이너에서 모든 EWS(조기 경보) 데이터를 가져옵니다.
    """
    if not stats_container:
        return []
    
    try:
        query = "SELECT * FROM c"
        items = list(stats_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        return items
    except exceptions.CosmosHttpResponseError as e:
        print(f"DiseaseStats 조회 에러: {e.message}")
        return []

def get_disease_stats_by_region(sido_code: str):
    """
    특정 지역의 EWS(조기 경보) 데이터를 가져옵니다.
    """
    if not stats_container:
        return None
    
    try:
        query = "SELECT * FROM c WHERE c.sido_code = @sido_code"
        parameters = [{"name": "@sido_code", "value": str(sido_code)}]
        
        items = list(stats_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return items[0] if items else None
    except exceptions.CosmosHttpResponseError as e:
        print(f"DiseaseStats 지역 조회 에러: {e.message}")
        return None
