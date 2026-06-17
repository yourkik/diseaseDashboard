import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS_AGE = ['#ef4444', '#f97316', '#f59e0b', '#84cc16', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6'];

export default function BIDemographicChart({ demographicsAge, demographicsGender, selectedDisease }) {
  const ageData = useMemo(() => {
    if (!demographicsAge || !selectedDisease) return [];
    const diseaseData = demographicsAge[selectedDisease];
    if (!diseaseData) return [];
    
    const grouped = {
      '10대 미만': 0,
      '10대': 0,
      '20대': 0,
      '30대': 0,
      '40대': 0,
      '50대': 0,
      '60대 이상': 0,
    };
    
    diseaseData.forEach(d => {
      const age = d.age_group;
      if (age === '계' || age === '전체' || !age) return; // 계 제외
      
      let ageNum = -1;
      const match = age.match(/\d+/);
      if (match) {
        ageNum = parseInt(match[0], 10);
      }
      
      if (ageNum >= 0 && ageNum < 10) {
        grouped['10대 미만'] += d.count;
      } else if (ageNum >= 10 && ageNum < 20) {
        grouped['10대'] += d.count;
      } else if (ageNum >= 20 && ageNum < 30) {
        grouped['20대'] += d.count;
      } else if (ageNum >= 30 && ageNum < 40) {
        grouped['30대'] += d.count;
      } else if (ageNum >= 40 && ageNum < 50) {
        grouped['40대'] += d.count;
      } else if (ageNum >= 50 && ageNum < 60) {
        grouped['50대'] += d.count;
      } else if (ageNum >= 60) {
        grouped['60대 이상'] += d.count;
      } else {
        grouped[age] = (grouped[age] || 0) + d.count;
      }
    });

    return Object.entries(grouped)
      .map(([name, value]) => ({ name, value }))
      .filter(item => item.value > 0)
      .sort((a, b) => b.value - a.value); // 높은 순 정렬
  }, [demographicsAge, selectedDisease]);

  const genderData = useMemo(() => {
    if (!demographicsGender || !selectedDisease) return [];
    const diseaseData = demographicsGender[selectedDisease];
    if (!diseaseData) return [];
    
    return diseaseData
      .filter(d => d.gender !== '계' && d.gender !== '전체') // 계 제외
      .map(d => ({
        name: (d.gender === 'M' || d.gender === '남성' || d.gender === '남') ? '남성' 
            : (d.gender === 'F' || d.gender === '여성' || d.gender === '여') ? '여성' 
            : d.gender,
        value: d.count,
      }));
  }, [demographicsGender, selectedDisease]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const { name, value } = payload[0].payload;
      return (
        <div style={{ backgroundColor: 'rgba(15,23,42,0.9)', padding: '12px', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#f8fafc' }}>
          <p style={{ margin: '0 0 4px 0', color: '#94a3b8' }}>{name}</p>
          <p style={{ margin: 0, color: '#38bdf8', fontWeight: 'bold' }}>확진자 수: {value.toLocaleString()}명</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card" style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        👥 인구통계학적 발생 현황 (실제 데이터)
      </h3>
      {(ageData.length === 0 && genderData.length === 0) ? (
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#64748b' }}>
          {selectedDisease}에 대한 인구통계 데이터가 없습니다.
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', gap: '16px' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <h4 style={{ textAlign: 'center', color: '#94a3b8', fontSize: '0.9rem', marginBottom: '8px' }}>연령별</h4>
            <ResponsiveContainer width="100%" height="80%">
              <PieChart>
                <Pie
                  data={ageData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                  animationDuration={1500}
                >
                  {ageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS_AGE[index % COLORS_AGE.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div style={{ flex: 1, position: 'relative' }}>
            <h4 style={{ textAlign: 'center', color: '#94a3b8', fontSize: '0.9rem', marginBottom: '8px' }}>성별</h4>
            <ResponsiveContainer width="100%" height="80%">
              <PieChart>
                <Pie
                  data={genderData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                  animationDuration={1500}
                >
                  {genderData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.name === '남성' ? '#3b82f6' : '#ef4444'} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '0.8rem', color: '#cbd5e1' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
