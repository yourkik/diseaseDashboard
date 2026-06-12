import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function RegionalRankingChart({ diseaseName }) {
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
        // status API returns [{region: "서울", count: 100, rate: 1.5, period: "..."}, ...]
        const response = await fetch(`${baseUrl}/api/stats/map/status?disease=${encodeURIComponent(diseaseName)}`);
        if (!response.ok) throw new Error('데이터를 불러오는데 실패했습니다.');
        
        const result = await response.json();
        
        // 에볼라 등 일부 응답이 객체(Dict) 형태일 경우 배열로 강제 변환
        const dataArray = Array.isArray(result) ? result : Object.values(result);
        
        // 정렬: 확진자 수 내림차순, 상위 10개만
        const sorted = dataArray.sort((a, b) => b.count - a.count).slice(0, 10);
        setData(sorted);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, [diseaseName]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ backgroundColor: 'rgba(15,23,42,0.9)', padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f8fafc' }}>
          <p style={{ margin: '0 0 4px 0', color: '#94a3b8' }}>{label}</p>
          <p style={{ margin: 0, color: '#38bdf8', fontWeight: 'bold' }}>{payload[0].value.toLocaleString()}명</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card" style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        🏆 지역별 확진자 수 랭킹 (Top 10)
      </h3>
      <div style={{ flex: 1, position: 'relative' }}>
        {loading && <div style={{ position: 'absolute', inset: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#94a3b8' }}>불러오는 중...</div>}
        {error && <div style={{ color: '#ef4444' }}>{error}</div>}
        {!loading && !error && data.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" stroke="#94a3b8" fontSize={12} tickFormatter={(val) => val.toLocaleString()} />
              <YAxis dataKey="region" type="category" stroke="#94a3b8" fontSize={12} width={60} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
              <Bar dataKey="count" radius={[0, 4, 4, 0]} animationDuration={1500}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index === 0 ? '#ef4444' : index < 3 ? '#f59e0b' : '#38bdf8'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
