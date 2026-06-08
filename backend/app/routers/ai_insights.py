from fastapi import APIRouter, HTTPException
from app.services.disease_agent import analyze_disease_risk_with_grounding
from app.services.cache_manager import get_insights_cache, update_insights_cache
import re

router = APIRouter(prefix="/api/insights", tags=["Insights"])

@router.get("/")
def get_disease_insights(disease: str):
    """
    LLM(Azure AI Agent)을 사용하여 질병 확산 동향, 위험도, 예방 수칙을 포함하는 종합 리포트(HTML)와 참고 문헌(Citations)을 반환합니다.
    """
    try:
        # 1. 캐시 확인
        cached = get_insights_cache(disease)
        if cached and "data" in cached:
            result = cached["data"]
            result["last_updated"] = cached.get("last_updated")
            return result
            
        # 2. 캐시가 없으면 LLM 호출 (약 15초 소요)
        agent_result = analyze_disease_risk_with_grounding(disease_keyword=disease)
        
        if "error" in agent_result:
            return {"analysis": f"<p>AI 분석 중 오류가 발생했습니다: {agent_result['error']}</p>", "citations": []}
            
        ai_analysis = agent_result.get("ai_analysis", "")
        
        # 가끔 LLM이 마크다운 블록(```html ... ```)으로 감싸서 보내는 경우를 대비해 태그 제거
        ai_analysis = re.sub(r'^```(html)?\s*', '', ai_analysis)
        ai_analysis = re.sub(r'\s*```$', '', ai_analysis)
        
        # Azure OpenAI 안전 필터에 의해 생성이 거부된 경우 우아한 폴백(Fallback) 처리
        if "I'm sorry, but I cannot assist" in ai_analysis or "I cannot assist" in ai_analysis:
            ai_analysis = """
            <div style="text-align:center; padding: 20px;">
                <h3 style="color:#ef4444; margin-bottom:10px;">⚠️ AI 분석이 제한되었습니다</h3>
                <p style="color:#94a3b8; font-size:0.95rem; line-height:1.6;">
                    해당 질병과 관련된 최근 뉴스 기사에 <strong>의료적으로 민감한 내용(중증도, 처방 등)</strong>이 포함되어 있어,<br/>
                    Azure OpenAI 안전 정책(Medical Safety Filter)에 의해 자동 요약이 차단되었습니다.<br/>
                    상세한 발생 동향 및 예방 수칙은 질병관리청 홈페이지를 참고해 주시기 바랍니다.
                </p>
            </div>
            """
        
        # AI가 텍스트 본문에 남기는 출처 기호(예: 【3:3†source】【3:4†source】) 제거
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
        
        # 3. 캐시 저장
        update_insights_cache(disease, result_data)
        
        # 방금 저장된 캐시 정보에서 last_updated 시간을 가져와 응답에 포함
        new_cached = get_insights_cache(disease)
        if new_cached:
            result_data["last_updated"] = new_cached.get("last_updated")
            
        return result_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
