import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

// 고정된 질병별 색상 팔레트
const COLORS = {
  "코로나19": "#ef4444",
  "수두": "#38bdf8",
  "백일해": "#f59e0b",
  "유행성이하선염": "#a855f7",
  "에볼라": "#10b981",
  "기타": "#64748b"
};

export default function MultiDiseaseTrendChart({ targetDiseases = [] }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAllTrends = async () => {
      if (targetDiseases.length === 0) return;
      setLoading(true);
      setError(null);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const year = new Date().getFullYear();
        
        // 모든 질병에 대해 API 호출
        const promises = targetDiseases.map(disease => 
          fetch(`${baseUrl}/api/stats/map/total?disease=${encodeURIComponent(disease)}&year=${year}`)
            .then(res => {
              if (!res.ok) throw new Error(`${disease} 데이터 로딩 실패`);
              return res.json();
            })
        );
        
        const results = await Promise.all(promises);
        
        // 데이터 병합 (Merge periods)
        // results = [ { disease: '수두', monthly_trend: [{period: '2024년 1월', count: 100}] }, ... ]
        const mergedMap = {};
        
        results.forEach(res => {
          const disease = res.disease;
          res.monthly_trend.forEach(item => {
            if (!mergedMap[item.period]) {
              mergedMap[item.period] = { period: item.period };
            }
            mergedMap[item.period][disease] = item.count;
          });
        });
        
        // Map을 배열로 변환하고 기간순으로 정렬
        const mergedArray = Object.values(mergedMap).sort((a, b) => a.period.localeCompare(b.period));
        setData(mergedArray);

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAllTrends();
  }, [targetDiseases]);

  const formatXAxis = (tickItem) => {
    if (!tickItem) return '';
    const parts = tickItem.split(' ');
    if (parts.length > 1) {
      return parts[1].replace('0', ''); // "05월" -> "5월"
    }
    return tickItem;
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ backgroundColor: 'rgba(15,23,42,0.9)', padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f8fafc' }}>
          <p style={{ margin: '0 0 8px 0', color: '#94a3b8' }}>{label}</p>
          {payload.map((entry, index) => (
            <div key={index} style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', marginBottom: '4px' }}>
              <span style={{ color: entry.color, fontWeight: 'bold' }}>{entry.name}</span>
              <span>{entry.value.toLocaleString()}명</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card" style={{ height: '450px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        📈 다중 질병 확산 추이 비교 (올해 기준)
      </h3>
      <div style={{ flex: 1, position: 'relative' }}>
        {loading && <div style={{ position: 'absolute', inset: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#94a3b8' }}>데이터 수집 및 병합 중...</div>}
        {error && <div style={{ color: '#ef4444' }}>{error}</div>}
        {!loading && !error && data.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis dataKey="period" tickFormatter={formatXAxis} stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(val) => val.toLocaleString()} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '0.9rem', color: '#e2e8f0' }} />
              {targetDiseases.map(disease => (
                <Line 
                  key={disease} 
                  type="monotone" 
                  dataKey={disease} 
                  stroke={COLORS[disease] || COLORS["기타"]} 
                  strokeWidth={3} 
                  dot={{ r: 4, strokeWidth: 2 }}
                  activeDot={{ r: 6 }}
                  animationDuration={2000}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
