'use client';

import { useState, useEffect } from 'react';

export default function KdcaContents() {
  const [contents, setContents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchContents() {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/data/contents');
        if (!response.ok) {
          throw new Error('데이터를 불러오는데 실패했습니다.');
        }
        const result = await response.json();
        setContents(result.data || []);
      } catch (err) {
        setError(err.message);
      } finally setLoading(false);
    }

    fetchContents();
  }, []);

  if (loading) return <div>질병관리청 콘텐츠를 불러오는 중입니다...</div>;
  if (error) return <div>에러 발생: {error}</div>;

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h2 style={{ borderBottom: '2px solid #005A9C', paddingBottom: '10px' }}>
        질병관리청 제공 감염병 정보
      </h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '20px' }}>
        {contents.map((item) => (
          <div key={item.id} style={{ 
            border: '1px solid #ddd', 
            borderRadius: '8px', 
            padding: '15px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>
              [{item.id}] {item.name}
            </h3>
            {/* API에서 전달받은 세부 정보 표시 */}
            {item.details ? (
              <pre style={{ 
                background: '#f4f4f4', 
                padding: '10px', 
                borderRadius: '5px',
                fontSize: '12px',
                overflowX: 'auto'
              }}>
                {JSON.stringify(item.details, null, 2)}
              </pre>
            ) : item.error ? (
              <p style={{ color: 'red', fontSize: '14px' }}>
                데이터 로드 실패: {item.error}
              </p>
            ) : (
              <p style={{ color: '#666', fontSize: '14px' }}>
                아직 콘텐츠 상세 정보가 없습니다. (API URL/키 세팅 필요)
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
