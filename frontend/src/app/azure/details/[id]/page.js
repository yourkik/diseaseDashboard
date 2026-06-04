'use client';

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { mockRegionalDetails } from '../../../mockData';

export default function RegionalDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const regionId = params.id;

  const [selectedYear, setSelectedYear] = useState('2026');
  const [selectedDisease, setSelectedDisease] = useState('수두');

  const regionData = mockRegionalDetails[regionId];

  if (!regionData) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', fontFamily: 'sans-serif' }}>
        <p style={{ color: '#64748b', marginBottom: '16px' }}>해당 지역의 통계 데이터가 존재하지 않습니다.</p>
        <button 
          onClick={() => router.push('/azure')}
          style={{ padding: '8px 16px', background: '#0f172a', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
        >
          메인 화면으로 돌아가기
        </button>
      </div>
    );
  }

  const yearStats = regionData.years[selectedYear] || [];
  const currentStat = yearStats.find(stat => stat.diseaseName === selectedDisease);
  const availableDiseases = yearStats.map(stat => stat.diseaseName);

  return (
    <div style={{ padding: '32px', maxWidth: '900px', margin: '0 auto', fontFamily: 'sans-serif', color: '#334155' }}>
      
      {/* 상단 네비게이션 헤더 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '2px solid #f1f5f9', paddingBottom: '16px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: '#0f172a' }}>
          {regionData.regionName} 감염병 정보 대시보드
        </h1>
        <button 
          onClick={() => router.push('/azure')}
          style={{ padding: '8px 14px', background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', borderRadius: '6px', cursor: 'pointer', fontSize: '14px' }}
        >
          ← 지도 보기
        </button>
      </div>

      {/* 연도 제어 탭 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {Object.keys(regionData.years).sort().map((year) => (
          <button
            key={year}
            onClick={() => {
              setSelectedYear(year);
              const nextYearStats = regionData.years[year] || [];
              if (nextYearStats.length > 0) {
                setSelectedDisease(nextYearStats[0].diseaseName);
              }
            }}
            style={{
              padding: '10px 20px',
              borderRadius: '6px',
              fontWeight: '600',
              backgroundColor: selectedYear === year ? '#2563eb' : '#f8fafc',
              color: selectedYear === year ? 'white' : '#64748b',
              border: selectedYear === year ? '1px solid #2563eb' : '1px solid #e2e8f0',
              cursor: 'pointer'
            }}
          >
            {year}년 통계
          </button>
        ))}
      </div>

      {/* 질병 제어 드롭다운 */}
      <div style={{ marginBottom: '32px', background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <label htmlFor="disease-select" style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#475569' }}>
          분석 데이터 선택
        </label>
        <select
          id="disease-select"
          value={selectedDisease}
          onChange={(e) => setSelectedDisease(e.target.value)}
          style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: 'white', fontSize: '16px', color: '#0f172a', outline: 'none' }}
        >
          {availableDiseases.length > 0 ? (
            availableDiseases.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))
          ) : (
            <option>가용한 감염병 데이터가 없습니다</option>
          )}
        </select>
      </div>

      {/* 데이터 시각화 결과 보드 */}
      {currentStat ? (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '32px' }}>
            <div style={{ padding: '20px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ fontSize: '14px', color: '#64748b', fontWeight: '500', marginBottom: '4px' }}>지정 질병 총 발생 건수</div>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#0f172a' }}>
                {currentStat.totalCount.toLocaleString()} <span style={{ fontSize: '18px', fontWeight: 'normal', color: '#64748b' }}>건</span>
              </div>
            </div>
            <div style={{ padding: '20px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <div style={{ fontSize: '14px', color: '#64748b', fontWeight: '500', marginBottom: '4px' }}>인구통계학 성별 분포 비율</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#0f172a', marginTop: '12px', display: 'flex', gap: '16px' }}>
                <span style={{ color: '#3b82f6' }}>남성 {currentStat.demographics.male}%</span>
                <span style={{ color: '#ec4899' }}>여성 {currentStat.demographics.female}%</span>
              </div>
            </div>
          </div>

          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
            <div style={{ padding: '16px 20px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', fontWeight: '600', color: '#334155' }}>
              연령 격차 분포 분석 데이터
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#fff', borderBottom: '2px solid #e2e8f0' }}>
                  <th style={{ padding: '14px 20px', fontSize: '14px', fontWeight: '600', color: '#64748b' }}>연령대</th>
                  <th style={{ padding: '14px 20px', fontSize: '14px', fontWeight: '600', color: '#64748b', textAlign: 'right' }}>확진 집계 건수</th>
                </tr>
              </thead>
              <tbody>
                {currentStat.ageGroups && currentStat.ageGroups.length > 0 ? (
                  currentStat.ageGroups.map((group, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '14px 20px', fontSize: '15px', color: '#334155', fontWeight: '500' }}>{group.age}</td>
                      <td style={{ padding: '14px 20px', fontSize: '15px', color: '#0f172a', fontWeight: 'bold', textAlign: 'right' }}>
                        {group.count.toLocaleString()} 건
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="2" style={{ padding: '20px', textAlign: 'center', color: '#94a3b8', fontSize: '14px' }}>
                      해당 질병의 세부 연령대 통계가 누락되었습니다.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div style={{ padding: '40px', textAlign: 'center', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0', color: '#64748b' }}>
          선택한 연도 및 질병에 부합하는 통계 레코드가 존재하지 않습니다.
        </div>
      )}
    </div>
  );
}