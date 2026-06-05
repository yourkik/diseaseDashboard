import os
from dotenv import load_dotenv

load_dotenv()
COVID_API_KEY = os.getenv("COVID_API_KEY")

def fetch_covid_region_status(year="2024"):
    """
    코로나19 전용 API를 통해 시도별 누적 확진자 현황을 반환합니다.
    추후 공공데이터포털(보건복지부 코로나19 API) 연동을 위해 예약된 함수입니다.
    현재는 키가 없거나 테스트 중일 때 빈 데이터를 반환합니다.
    """
    if not COVID_API_KEY or COVID_API_KEY == "your_covid_api_key_here":
        print("COVID_API_KEY is not set.")
        return {"response": {"body": {"items": {"item": []}}}}
        
    # 실제 API 연동 로직이 들어갈 곳
    return {"response": {"body": {"items": {"item": []}}}}

def fetch_covid_period_spread(start_year, end_year):
    """
    코로나19 전용 API를 통해 기간별/지역별 확산 추이를 반환합니다.
    """
    if not COVID_API_KEY or COVID_API_KEY == "your_covid_api_key_here":
        return []
        
    # 실제 API 연동 로직이 들어갈 곳
    return []
