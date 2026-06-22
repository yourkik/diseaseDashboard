import React, { useState, useEffect } from 'react';
import { AlertTriangle, Activity, MapPin } from 'lucide-react';

export default function EWSSidebar({ regionName, diseaseName, onClose }) {
  const [status, setStatus] = useState(null);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      if (!regionName) return;
      setLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        // 1. 해당 지역의 종합 EWS 현황(Risk Level, AI Summary) 호출
        const encodedRegion = encodeURIComponent(regionName);
        const statusRes = await fetch(`${baseUrl}/api/ews/status`);
        const allStatus = await statusRes.json();
        
        // sido_code 매핑 대신 프론트에서 이름으로 대략적 매칭 (실제는 sido_code로 정확히 매칭해야함)
        const myStatus = Array.isArray(allStatus) 
          ? allStatus.find(s => s.name && s.name.includes(regionName))
          : null;
        setStatus(myStatus || { risk_level: "Low", ai_summary: "현재 특별한 징후가 감지되지 않았습니다.", realtime_score: 0 });

        // 2. 해당 지역의 실시간 뉴스 호출
        const newsRes = await fetch(`${baseUrl}/api/ews/news?region=${encodedRegion}&disease=${encodeURIComponent(diseaseName)}`);
        const newsData = await newsRes.json();
        setNews(newsData.items || []);
        
      } catch (err) {
        console.error("EWS Data fetch error:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [regionName, diseaseName]);

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return '#ef4444'; // Red
      case 'high': return '#f97316'; // Orange
      case 'medium': return '#fbbf24'; // Yellow
      case 'low': return '#22c55e'; // Green
      default: return '#94a3b8';
    }
  };

  if (!regionName) return null;

  return (
    <div style={{
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(16px)',
      border: '1px solid #cbd5e1',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
      color: '#0f172a',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative'
    }}>
      {onClose && (
        <button onClick={onClose} style={{
          position: 'absolute', top: '16px', right: '16px', 
          background: 'none', border: 'none', color: '#64748b', 
          cursor: 'pointer', fontSize: '1.4rem'
        }}>✕</button>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
        <MapPin color="#2563eb" size={32} />
        <div>
          <h2 style={{ margin: 0, fontSize: '1.6rem', color: '#0f172a' }}>{regionName} <span style={{fontSize: '1.1rem', color: '#64748b', fontWeight: 'normal'}}>지역 경보</span></h2>
          <div style={{ fontSize: '1rem', color: '#2563eb', marginTop: '4px', fontWeight: '600' }}>AI 실시간 모니터링 시스템</div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#38bdf8' }}>EWS 데이터 연동 중...</div>
      ) : (
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '8px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* 1. Risk Level 패널 */}
          <div style={{ 
            backgroundColor: '#f8fafc', 
            borderRadius: '12px', 
            padding: '20px',
            border: '1px solid #e2e8f0',
            borderLeft: `5px solid ${getRiskColor(status?.risk_level)}`
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle color={getRiskColor(status?.risk_level)} size={22} />
                <span style={{ fontWeight: 'bold', color: '#334155', fontSize: '1.1rem' }}>종합 위험도</span>
              </div>
              <div style={{ 
                backgroundColor: `${getRiskColor(status?.risk_level)}20`, 
                color: getRiskColor(status?.risk_level),
                padding: '6px 16px', 
                borderRadius: '20px', 
                fontWeight: 'bold',
                fontSize: '1.1rem'
              }}>
                {status?.risk_level || 'Low'}
              </div>
            </div>
            
            <div style={{ marginTop: '12px', color: '#475569' }}>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '1rem', color: '#334155' }}>📌 AI 핵심 요약</h4>
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '1rem', lineHeight: '1.7' }}>
                {(status?.ai_summary || '현재 특별한 징후가 감지되지 않았습니다.')
                  .split(/[.!?]+/)
                  .map(s => s.trim())
                  .filter(s => s.length > 0)
                  .map((sentence, idx) => (
                    <li key={idx} style={{ marginBottom: '8px' }}>
                      <span dangerouslySetInnerHTML={{ __html: sentence.replace(/(\[[^\]]+\])/g, '<strong style="color: #d97706;">$1</strong>') }} />.
                    </li>
                  ))}
              </ul>
            </div>
          </div>

          {/* 2. News 타임라인 패널 */}
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity color="#a855f7" size={20} /> 실시간 징후 뉴스
            </h3>
            
            {news.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px', backgroundColor: '#f1f5f9', borderRadius: '8px', color: '#64748b', fontSize: '1rem' }}>
                최근 발견된 관련 징후가 없습니다.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {news.map((n, idx) => (
                  <a key={idx} href={n.link || '#'} target="_blank" rel="noreferrer" style={{
                    textDecoration: 'none',
                    display: 'block',
                    backgroundColor: '#ffffff',
                    padding: '16px',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    borderLeft: '4px solid #8b5cf6',
                    boxShadow: '0 2px 5px rgba(0,0,0,0.02)',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => { 
                    e.currentTarget.style.backgroundColor = '#f8fafc'; 
                    e.currentTarget.style.boxShadow = '0 4px 10px rgba(0,0,0,0.05)';
                  }}
                  onMouseLeave={(e) => { 
                    e.currentTarget.style.backgroundColor = '#ffffff'; 
                    e.currentTarget.style.boxShadow = '0 2px 5px rgba(0,0,0,0.02)';
                  }}
                  >
                    <div style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '8px', fontWeight: '500' }}>
                      {n.published_at ? n.published_at.substring(0, 10) : ''} • <span style={{ color: '#8b5cf6' }}>{n.disease || diseaseName}</span>
                    </div>
                    <div style={{ color: '#1e293b', fontSize: '1.05rem', lineHeight: '1.5', fontWeight: '600' }}>
                      {n.title}
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}
