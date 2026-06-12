import React, { useState, useEffect } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis } from 'recharts';

export default function ScatterRiskChart({ diseaseName }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      if (!diseaseName) return;
      setLoading(true);
      setError(null);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/api/stats/map/status?disease=${encodeURIComponent(diseaseName)}`);
        if (!response.ok) throw new Error('데이터를 불러오는데 실패했습니다.');
        
        const result = await response.json();
        
        // 유효한 데이터만 필터링 (에볼라 등 객체 응답 대비 배열로 강제 변환)
        const dataArray = Array.isArray(result) ? result : Object.values(result);
        setData(dataArray);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, [diseaseName]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ backgroundColor: 'rgba(15,23,42,0.9)', padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f8fafc' }}>
          <p style={{ margin: '0 0 8px 0', color: '#38bdf8', fontWeight: 'bold' }}>{data.region}</p>
          <p style={{ margin: '0 0 4px 0', fontSize: '0.85rem' }}>확진자 수: {data.count.toLocaleString()}명</p>
          <p style={{ margin: 0, fontSize: '0.85rem' }}>10만명당 발생률: {data.rate}명</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card" style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        🎯 위험도 분포 (발생률 vs 확진자 수)
      </h3>
      <div style={{ flex: 1, position: 'relative' }}>
        {loading && <div style={{ position: 'absolute', inset: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#94a3b8' }}>불러오는 중...</div>}
        {error && <div style={{ color: '#ef4444' }}>{error}</div>}
        {!loading && !error && data.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis 
                type="number" 
                dataKey="count" 
                name="확진자 수" 
                stroke="#94a3b8" 
                fontSize={12} 
                tickFormatter={(val) => val.toLocaleString()}
                label={{ value: "확진자 수 (명)", position: "bottom", fill: "#64748b", fontSize: 12 }}
              />
              <YAxis 
                type="number" 
                dataKey="rate" 
                name="발생률" 
                stroke="#94a3b8" 
                fontSize={12}
                label={{ value: "10만명당 발생률", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 12 }}
              />
              <ZAxis type="category" dataKey="region" name="지역" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} content={<CustomTooltip />} />
              <Scatter data={data} fill="#a855f7" opacity={0.8} />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
