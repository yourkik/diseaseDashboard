import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#ef4444', '#f97316', '#f59e0b', '#84cc16', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6'];

export default function BIDemographicChart({ demographics, selectedDisease }) {
  const data = useMemo(() => {
    if (!demographics || !selectedDisease) return [];
    
    const diseaseData = demographics[selectedDisease];
    if (!diseaseData) return [];
    
    // Convert weights to percentages and format
    return diseaseData.map(d => ({
      name: `${d.age_group} (${d.gender === 'M' ? '남' : '여'})`,
      value: Math.round(d.weight * 100),
      raw: d
    }));
  }, [demographics, selectedDisease]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const { name, value } = payload[0].payload;
      return (
        <div style={{ backgroundColor: 'rgba(15,23,42,0.9)', padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f8fafc' }}>
          <p style={{ margin: '0 0 4px 0', color: '#94a3b8' }}>{name}</p>
          <p style={{ margin: 0, color: '#38bdf8', fontWeight: 'bold' }}>발생 가중치: {value}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card" style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        👥 인구통계학적 취약성 (연령/성별)
      </h3>
      {data.length === 0 ? (
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#64748b' }}>
          {selectedDisease}에 대한 인구통계 데이터가 없습니다.
        </div>
      ) : (
        <div style={{ flex: 1, position: 'relative' }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
                animationDuration={1500}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '0.8rem', color: '#cbd5e1' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
