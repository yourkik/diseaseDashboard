import React, { useMemo } from 'react';
import { ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function BIMobilityChart({ mobility, infections, selectedDisease, selectedRegion }) {
  const data = useMemo(() => {
    if (!mobility || !infections) return [];
    
    // 1. Group Mobility by Month (Approximate mapping: W01-W04 -> Jan)
    // 2. Group Infections by Month
    const monthlyData = {};
    for (let i = 1; i <= 12; i++) {
      const monthStr = `${i}월`;
      monthlyData[monthStr] = { month: monthStr, mobility: 0, infections: 0 };
    }

    // Process Mobility
    mobility.forEach(m => {
      if (selectedRegion !== "전체" && m.region !== selectedRegion) return;
      const weekStr = m.week; // "2023-W01"
      const weekNum = parseInt(weekStr.split('-W')[1], 10);
      let monthNum = Math.ceil(weekNum / 4.33);
      if (monthNum > 12) monthNum = 12;
      monthlyData[`${monthNum}월`].mobility += m.traffic_volume;
    });

    // Process Infections
    infections.forEach(inf => {
      if (selectedRegion !== "전체" && inf.Region !== selectedRegion) return;
      if (selectedDisease !== "전체" && inf.Disease !== selectedDisease) return;
      
      const period = inf.Date; // "2023년 01월"
      const parts = period.split(' ');
      if (parts.length > 1) {
        const mStr = parts[1].replace('0', ''); // "05월" -> "5월"
        if (monthlyData[mStr]) {
          monthlyData[mStr].infections += inf.Count;
        }
      }
    });

    return Object.values(monthlyData);
  }, [mobility, infections, selectedDisease, selectedRegion]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length >= 2) {
      return (
        <div style={{ backgroundColor: 'rgba(15,23,42,0.9)', padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f8fafc' }}>
          <p style={{ margin: '0 0 8px 0', color: '#94a3b8', fontWeight: 'bold' }}>{label}</p>
          <p style={{ margin: '0 0 4px 0', fontSize: '0.85rem', color: '#f59e0b' }}>이동량(교통량): {payload[0].value.toLocaleString()}</p>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#ef4444' }}>확진자 수: {payload[1].value.toLocaleString()}명</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card" style={{ height: '450px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        🚗 유동인구(교통량) vs 감염병 확산 시계열 추이
      </h3>
      <div style={{ flex: 1, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <defs>
              <linearGradient id="colorMobility" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
            
            <YAxis 
              yAxisId="left" 
              orientation="left" 
              stroke="#f59e0b" 
              fontSize={12} 
              tickFormatter={(v) => `${(v/10000).toFixed(0)}만`} 
              tickLine={false} 
              axisLine={false} 
              domain={['dataMin', 'dataMax']} 
            />
            <YAxis 
              yAxisId="right" 
              orientation="right" 
              stroke="#ef4444" 
              fontSize={12} 
              tickFormatter={(v) => v.toLocaleString()} 
              tickLine={false} 
              axisLine={false} 
            />
            
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '0.9rem', color: '#e2e8f0' }} />
            
            <Area yAxisId="left" type="monotone" dataKey="mobility" name="지역 내 유동인구 (교통량)" stroke="#f59e0b" fillOpacity={1} fill="url(#colorMobility)" animationDuration={2000} />
            <Line yAxisId="right" type="monotone" dataKey="infections" name="누적 확진자 수" stroke="#ef4444" strokeWidth={4} dot={{ r: 4 }} activeDot={{ r: 6 }} animationDuration={2000} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
