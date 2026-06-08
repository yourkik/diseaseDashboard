import asyncio
from datetime import datetime
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.disease_agent import analyze_disease_risk_with_grounding
from app.services.cache_manager import update_insights_cache

# 분석할 핵심 질병 목록
DISEASES = ['수두', '백일해', '유행성이하선염', '코로나19', '에볼라', '한타바이러스']

async def refresh_all_insights():
    """모든 질병에 대해 AI 리포트를 갱신합니다."""
    
    # 새벽 시간대(02:00 ~ 06:00)에는 API 비용 절감을 위해 실행을 건너뜁니다.
    current_hour = datetime.now().hour
    if 2 <= current_hour < 6:
        print(f"[Scheduler] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 새벽 휴식 시간(02:00~06:00)이므로 AI 수집을 건너뜁니다.")
        return

    print(f"[Scheduler] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 1시간 주기 AI 질병 리포트 자동 생성(Pre-warming)을 시작합니다.")
    
    for disease in DISEASES:
        try:
            print(f"[Scheduler] '{disease}' AI 분석 중...")
            
            # 동기 함수이므로 asyncio.to_thread로 래핑하거나 그냥 호출 (FastAPI에선 백그라운드 블로킹 주의, 여기선 to_thread 사용)
            agent_result = await asyncio.to_thread(analyze_disease_risk_with_grounding, disease)
            
            if "error" in agent_result:
                print(f"[Scheduler] '{disease}' 에러 발생: {agent_result['error']}")
                continue
                
            ai_analysis = agent_result.get("ai_analysis", "")
            
            # 클리닝 (기호 제거 및 HTML 파싱 방해 요소 제거)
            ai_analysis = re.sub(r'^```(html)?\s*', '', ai_analysis)
            ai_analysis = re.sub(r'\s*```$', '', ai_analysis)
            ai_analysis = re.sub(r'【.*?】', '', ai_analysis)
            
            citations = agent_result.get("citations", [])
            seen_urls = set()
            formatted_citations = []
            for citation in citations:
                url = citation.get("url", "#")
                if url not in seen_urls:
                    seen_urls.add(url)
                    formatted_citations.append({
                        "title": citation.get("title", "관련 문서"),
                        "url": url,
                    })
                    
            result_data = {
                "analysis": ai_analysis,
                "citations": formatted_citations
            }
            
            # 캐시 업데이트
            update_insights_cache(disease, result_data)
            print(f"[Scheduler] '{disease}' 캐시 업데이트 완료.")
            
        except Exception as e:
            print(f"[Scheduler] '{disease}' 처리 중 예기치 않은 오류: {e}")
            
        # Rate Limit 우회를 위해 질병 사이 30초 대기
        await asyncio.sleep(30)
        
    print(f"[Scheduler] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 모든 질병 자동 분석 완료.")

# 스케줄러 인스턴스 (main.py에서 사용)
scheduler = AsyncIOScheduler()

def start_scheduler():
    """스케줄러를 시작하고 Job을 등록합니다."""
    # 매 정시(hour=*)마다 실행 (1시간 간격)
    scheduler.add_job(refresh_all_insights, 'cron', minute=0)
    scheduler.start()
    print("[Scheduler] AI Insight Auto-refresh Job 등록 완료 (매 시간 정각 동작).")

def stop_scheduler():
    """스케줄러를 안전하게 종료합니다."""
    scheduler.shutdown()
    print("[Scheduler] 스케줄러가 종료되었습니다.")
