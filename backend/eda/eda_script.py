import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 상위 디렉토리(backend)를 모듈 경로에 추가하여 app.services.ingestion을 불러올 수 있게 합니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ingestion import fetch_kdca_disease_contents, fetch_kdca_stats, get_integrated_news

# 한글 폰트 설정 (Windows 기준 'Malgun Gothic', Mac은 'AppleGothic')
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def run_eda():
    print("=== [1] 데이터 수집 시작 ===")
    
    print("\n1. 질병관리청 콘텐츠 API 데이터 수집 중...")
    contents_res = fetch_kdca_disease_contents()
    contents_data = contents_res.get("data", [])
    df_contents = pd.DataFrame(contents_data)
    
    print("\n2. 질병관리청 감염병 발생 동향 수집 중...")
    stats_res = fetch_kdca_stats()
    stats_items = stats_res.get("items", []) if isinstance(stats_res, dict) else []
    df_stats = pd.DataFrame(stats_items)
    
    print("\n3. 감염병 뉴스 데이터 수집 중...")
    news_res = get_integrated_news()
    news_items = news_res.get("value", []) if isinstance(news_res, dict) else []
    df_news = pd.DataFrame(news_items)

    print("\n=== [2] 데이터 저장 ===")
    os.makedirs("data", exist_ok=True)
    
    if not df_contents.empty:
        df_contents.to_csv("data/kdca_contents.csv", index=False, encoding='utf-8-sig')
        print(f"- kdca_contents.csv 저장 완료 (데이터 길이: {len(df_contents)})")
    
    if not df_stats.empty:
        df_stats.to_csv("data/kdca_stats.csv", index=False, encoding='utf-8-sig')
        print(f"- kdca_stats.csv 저장 완료 (데이터 길이: {len(df_stats)})")
        
    if not df_news.empty:
        df_news.to_csv("data/integrated_news.csv", index=False, encoding='utf-8-sig')
        print(f"- integrated_news.csv 저장 완료 (데이터 길이: {len(df_news)})")

    print("\n=== [3] 간단한 EDA (탐색적 데이터 분석) 결과 ===")
    
    # 1. 콘텐츠 데이터 확인
    print("\n[질병관리청 콘텐츠 데이터 미리보기]")
    if not df_contents.empty:
        print(df_contents[['id', 'name']].head())
    else:
        print("콘텐츠 데이터가 없습니다.")

    # 2. 뉴스 소스 분포 시각화
    print("\n[뉴스 소스별 비율 확인]")
    if not df_news.empty and 'source' in df_news.columns:
        source_counts = df_news['source'].value_counts()
        print(source_counts)
        
        plt.figure(figsize=(8, 5))
        sns.barplot(x=source_counts.index, y=source_counts.values, palette='viridis')
        plt.title("뉴스 소스별 기사 수")
        plt.xlabel("소스")
        plt.ylabel("기사 수")
        plt.tight_layout()
        plt.savefig("data/news_source_distribution.png")
        print("-> data/news_source_distribution.png 로 그래프 저장 완료")
    else:
        print("시각화할 뉴스 데이터가 없습니다.")

    print("\nEDA 스크립트 실행이 완료되었습니다. 결과 파일은 'data' 폴더를 확인해주세요!")

if __name__ == "__main__":
    run_eda()
