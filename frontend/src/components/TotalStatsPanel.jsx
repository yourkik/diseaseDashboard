import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function TotalStatsPanel({ diseaseName }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTotalStats = async () => {
    if (!diseaseName) return;
    
    setLoading(true);
    setError(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const year = new Date().getFullYear();
      const url = `${baseUrl}/api/stats/map/total?disease=${encodeURIComponent(diseaseName)}&year=${year}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('통계 데이터를 불러오는데 실패했습니다.');
      }
      
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTotalStats();
  }, [diseaseName]);

  // Format the month for the X-axis (e.g., "2024년 05월" -> "5월")
  const formatXAxis = (tickItem) => {
    if (!tickItem) return '';
    const parts = tickItem.split(' ');
    if (parts.length > 1) {
      return parts[1].replace('0', ''); // "05월" -> "5월"
    }
    return tickItem;
  };

  // Custom Tooltip for the chart
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          border: '1px solid #cbd5e1',
          borderRadius: '8px',
          padding: '16px',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
          color: '#1e293b'
        }}>
          <p style={{ margin: '0 0 8px 0', fontSize: '0.95rem', fontWeight: '600', color: '#64748b' }}>{label}</p>
          <p style={{ margin: 0, fontWeight: 'bold', color: '#2563eb', fontSize: '1.3rem' }}>
            {payload[0].value.toLocaleString()}명
          </p>
        </div>
      );
    }
    return null;
  };

  if (!diseaseName) return null;

  return (
    <div style={{
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      backdropFilter: 'blur(12px)',
      border: '1px solid #e2e8f0',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.05)',
      color: '#0f172a',
      marginBottom: '20px',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <h3 style={{ margin: '0 0 20px 0', fontSize: '1.3rem', fontWeight: 'bold', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px' }}>
        📊 전국 단위 발생 지표
      </h3>
      
      {loading ? (
        <div style={{ padding: '40px 0', textAlign: 'center', color: '#94a3b8' }}>
          통계 데이터를 불러오는 중...
        </div>
      ) : error ? (
        <div style={{ padding: '20px 0', textAlign: 'center', color: '#ef4444', fontSize: '0.9rem' }}>
          {error}
        </div>
      ) : data ? (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
            {/* 누적 확진자 수 카드 */}
            <div style={{
              backgroundColor: '#f8fafc',
              borderRadius: '12px',
              padding: '20px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 10px rgba(0,0,0,0.02)'
            }}>
              <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#64748b', marginBottom: '8px' }}>
                당해 누적 확진자 수
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 'bold', color: '#0f172a', display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                {data.total_count.toLocaleString()} <span style={{ fontSize: '1rem', color: '#94a3b8', fontWeight: 'normal' }}>명</span>
              </div>
            </div>

            {/* 10만 명당 발생률 카드 */}
            <div style={{
              backgroundColor: '#f8fafc',
              borderRadius: '12px',
              padding: '20px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 10px rgba(0,0,0,0.02)'
            }}>
              <div style={{ fontSize: '0.95rem', fontWeight: '600', color: '#64748b', marginBottom: '8px' }}>
                10만 명당 발생률
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 'bold', color: '#0f172a', display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                {data.incidence_rate.toFixed(1)} <span style={{ fontSize: '1rem', color: '#94a3b8', fontWeight: 'normal' }}>명</span>
              </div>
            </div>
          </div>

          {/* 시계열 꺾은선 차트 영역 */}
          {data.monthly_trend && data.monthly_trend.length > 0 ? (
            <div style={{ height: '240px', width: '100%', marginTop: '15px' }}>
              <div style={{ fontSize: '1rem', fontWeight: '600', color: '#475569', marginBottom: '16px' }}>월별 발생 추이 ({data.year}년)</div>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.monthly_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis 
                    dataKey="period" 
                    tickFormatter={formatXAxis} 
                    stroke="#cbd5e1" 
                    tick={{ fill: '#64748b', fontSize: 13, fontWeight: '500' }} 
                    axisLine={false} 
                    tickLine={false}
                  />
                  <YAxis 
                    stroke="#cbd5e1" 
                    tick={{ fill: '#64748b', fontSize: 13, fontWeight: '500' }} 
                    axisLine={false} 
                    tickLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#3b82f6" 
                    strokeWidth={3}
                    fillOpacity={1} 
                    fill="url(#colorCount)" 
                    animationDuration={1500}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#64748b', padding: '20px', fontSize: '0.9rem' }}>
              시계열 데이터가 없습니다.
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
