import React, { useState, useEffect } from 'react';

export default function AIInsightsPanel({ diseaseName }) {
  const [data, setData] = useState({ analysis: "", citations: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchInsights = async (forceRefresh = false) => {
    if (!diseaseName) return;
    
    setLoading(true);
    setError(null);
    try {
      const url = `http://localhost:8000/api/insights?disease=${encodeURIComponent(diseaseName)}${forceRefresh ? '&force_refresh=true' : ''}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('리포트를 불러오는데 실패했습니다.');
      }
      const result = await response.json();
      setData(result || { analysis: "", citations: [] });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, [diseaseName]);

  return (
    <div style={{
      backgroundColor: 'rgba(30, 41, 59, 0.7)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
      color: '#f8fafc',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        paddingBottom: '16px',
        margin: '0 0 20px 0',
      }}>
        <h2 style={{ 
          margin: 0, 
          fontSize: '1.25rem', 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          wordBreak: 'keep-all',
          lineHeight: '1.4'
        }}>
          ✨ AI 종합 분석 리포트: <span style={{ color: '#38bdf8', whiteSpace: 'nowrap' }}>{diseaseName}</span>
        </h2>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          flexWrap: 'wrap'
        }}>
          {data.last_updated && (
            <div style={{ 
              fontSize: '0.75rem', 
              color: '#94a3b8', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '4px', 
              backgroundColor: 'rgba(255,255,255,0.05)', 
              padding: '6px 10px', 
              borderRadius: '16px',
              whiteSpace: 'nowrap',
              flexShrink: 0
            }}>
              🕒 업데이트: {new Date(data.last_updated).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </div>
          )}
          
          <button 
            onClick={() => fetchInsights(true)}
            disabled={loading}
            title="캐시를 무시하고 최신 데이터로 다시 분석합니다"
            style={{
              background: 'none',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#f8fafc',
              padding: '6px 12px',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              opacity: loading ? 0.5 : 1,
              transition: 'all 0.2s ease',
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              whiteSpace: 'nowrap',
              flexShrink: 0
            }}
            onMouseEnter={(e) => {
              if (!loading) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
            }}
            onMouseLeave={(e) => {
              if (!loading) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
            }}
          >
            🔄 새로고침
          </button>
        </div>
      </div>
      
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '8px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8', lineHeight: '1.8' }}>
            <div style={{ 
              fontSize: '1.5rem', 
              marginBottom: '12px', 
              color: '#38bdf8',
              animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
            }}>
              AI 에이전트 분석 중... 🤖
            </div>
            최신 데이터를 수집하고 종합 리포트를 작성하고 있습니다.<br/>
            (최초 분석 시 최대 20초가 소요될 수 있습니다)
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#ef4444' }}>
            {error}
          </div>
        ) : data.analysis ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {/* AI HTML 리포트 렌더링 */}
            <div 
              className="ai-markdown-content"
              style={{
                lineHeight: '1.7',
                fontSize: '0.95rem',
                color: '#e2e8f0'
              }}
              dangerouslySetInnerHTML={{ __html: data.analysis }} 
            />

            {/* 참고 문헌(Citations) 칩 섹션 */}
            {data.citations && data.citations.length > 0 && (
              <div style={{
                marginTop: '20px',
                paddingTop: '20px',
                borderTop: '1px dashed rgba(255, 255, 255, 0.1)'
              }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', color: '#94a3b8' }}>
                  🔗 참고 문헌 (Citations)
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {data.citations.map((item, index) => (
                    <a 
                      key={index} 
                      href={item.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        textDecoration: 'none',
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        color: '#38bdf8',
                        padding: '6px 12px',
                        borderRadius: '20px',
                        fontSize: '0.8rem',
                        border: '1px solid rgba(56, 189, 248, 0.2)',
                        transition: 'all 0.2s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(56, 189, 248, 0.2)';
                        e.currentTarget.style.transform = 'translateY(-2px)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(56, 189, 248, 0.1)';
                        e.currentTarget.style.transform = 'translateY(0)';
                      }}
                    >
                      {item.title}
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
            리포트 데이터가 없습니다.
          </div>
        )}
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .ai-markdown-content h3 {
          color: #38bdf8;
          margin: 1.5em 0 0.5em 0;
          font-size: 1.1rem;
        }
        .ai-markdown-content p {
          margin: 0 0 1em 0;
        }
        .ai-markdown-content ul {
          margin: 0 0 1em 0;
          padding-left: 1.5em;
        }
        .ai-markdown-content li {
          margin-bottom: 0.5em;
        }
        .ai-markdown-content strong {
          color: #f8fafc;
        }
      `}} />
    </div>
  );
}
