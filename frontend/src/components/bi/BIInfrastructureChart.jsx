import React, { useMemo } from 'react';
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

export default function BIInfrastructureChart({ regions, infections, selectedDisease, selectedRegion }) {
  const data = useMemo(() => {
    if (!regions || !infections) return [];
    
    // Calculate total infections per region
    const regionInfections = {};
    infections.forEach(inf => {
      if (selectedDisease !== "전체" && inf.Disease !== selectedDisease) return;
      if (!regionInfections[inf.Region]) regionInfections[inf.Region] = 0;
      regionInfections[inf.Region] += inf.Count;
    });

    return regions.map(r => {
      // 10만명당 병상 수 계산
      const bedsPer100k = Math.round((r.total_beds / r.population) * 100000);
      const totalInf = regionInfections[r.region] || 0;
      
      return {
        region: r.region,
        bedsPer100k: bedsPer100k,
        infections: totalInf,
        elderlyRatio: r.elderly_ratio
      };
    }).sort((a, b) => b.infections - a.infections); // 확진자 순 정렬

  }, [regions, infections, selectedDisease]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length >= 2) {
      return (
        <div style={{ backgroundColor: 'rgba(15,23,42,0.9)', padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f8fafc' }}>
          <p style={{ margin: '0 0 8px 0', color: '#38bdf8', fontWeight: 'bold' }}>{label}</p>
          <p style={{ margin: '0 0 4px 0', fontSize: '0.85rem' }}>10만명당 병상 수: {payload[0].value.toLocaleString()}개</p>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#ef4444' }}>총 확진자 수: {payload[1].value.toLocaleString()}명</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card" style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        🏥 지역 의료 인프라 대비 확진자
      </h3>
      <div style={{ flex: 1, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="region" stroke="#94a3b8" fontSize={12} tickLine={false} />
            
            <YAxis yAxisId="left" orientation="left" stroke="#38bdf8" fontSize={12} tickFormatter={(v) => `${v}개`} />
            <YAxis yAxisId="right" orientation="right" stroke="#ef4444" fontSize={12} tickFormatter={(v) => v.toLocaleString()} />
            
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '0.8rem' }} />
            
            <Bar yAxisId="left" dataKey="bedsPer100k" name="10만명당 병상 수" radius={[4, 4, 0, 0]} animationDuration={1500}>
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={(selectedRegion !== "전체" && entry.region !== selectedRegion) ? 'rgba(56,189,248,0.2)' : '#38bdf8'} 
                />
              ))}
            </Bar>
            <Line yAxisId="right" type="monotone" dataKey="infections" name="누적 확진자 수" stroke="#ef4444" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} animationDuration={1500} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
