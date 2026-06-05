import React, { useState, useEffect } from 'react';

export default function NewsPanel({ diseaseName }) {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchNews() {
      if (!diseaseName) return;
      
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`http://localhost:8000/api/news?disease=${encodeURIComponent(diseaseName)}`);
        if (!response.ok) {
          throw new Error('뉴스를 불러오는데 실패했습니다.');
        }
        const data = await response.json();
        setNews(data || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchNews();
  }, [diseaseName]);

  return (
    <div style={{
      backgroundColor: 'rgba(30, 41, 59, 0.7)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '16px',
      padding: '20px',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
      color: '#f8fafc',
      height: '100%',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <h2 style={{ 
        margin: '0 0 16px 0', 
        fontSize: '1.25rem', 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        paddingBottom: '12px'
      }}>
        📰 {diseaseName} 관련 최신 뉴스
      </h2>
      
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '20px', color: '#94a3b8' }}>
            뉴스를 분석 중입니다...
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '20px', color: '#ef4444' }}>
            {error}
          </div>
        ) : news.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px', color: '#94a3b8' }}>
            관련 뉴스가 없습니다.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {news.map((item, index) => (
              <a 
                key={index} 
                href={item.url} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{
                  display: 'block',
                  textDecoration: 'none',
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  padding: '16px',
                  borderRadius: '12px',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  transition: 'all 0.2s ease',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(56, 189, 248, 0.1)';
                  e.currentTarget.style.border = '1px solid rgba(56, 189, 248, 0.3)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(15, 23, 42, 0.6)';
                  e.currentTarget.style.border = '1px solid rgba(255, 255, 255, 0.05)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <h3 style={{ 
                  margin: '0 0 8px 0', 
                  fontSize: '1rem', 
                  color: '#38bdf8',
                  lineHeight: '1.4'
                }} dangerouslySetInnerHTML={{ __html: item.title }} />
                
                <p style={{ 
                  margin: '0 0 10px 0', 
                  fontSize: '0.85rem', 
                  color: '#cbd5e1',
                  lineHeight: '1.5',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden'
                }} dangerouslySetInnerHTML={{ __html: item.description }} />
                
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  fontSize: '0.75rem', 
                  color: '#64748b' 
                }}>
                  <span>{item.source}</span>
                  {item.date && <span>{new Date(item.date).toLocaleDateString()}</span>}
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
