'use strict';

import React, { useState, useEffect } from 'react';

export default function PredictionPanel({ diseaseName }) {
  const [availableWeeks, setAvailableWeeks] = useState([]);
  const [selectedTimeKey, setSelectedTimeKey] = useState('');
  
  // 기본 검색 지역
  const [searchRegion, setSearchRegion] = useState('서울 강남구');
  const [singlePrediction, setSinglePrediction] = useState(null);
  
  const [topDanger, setTopDanger] = useState([]);
  const [nationalCases, setNationalCases] = useState(0);
  const [prevNationalCases, setPrevNationalCases] = useState(0); // 변동 폭 연산용
  
  const [loadingTop, setLoadingTop] = useState(false);
  const [loadingSearch, setLoadingSearch] = useState(false);

  const BACKEND_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api';
  const AI_BACKEND_URL = 'http://localhost:8001/api';
  const isPredictable = ['수두', '백일해', '유행성이하선염', '코로나19', 'covid'].includes(diseaseName);

  useEffect(() => {
    const generateFutureWeeks = () => {
      const currentWeeksList = [];
      const today = new Date();
      const currentDay = today.getDay();
      const distanceToMonday = currentDay === 0 ? -6 : 1 - currentDay;
      const thisMonday = new Date(today);
      thisMonday.setDate(today.getDate() + distanceToMonday);

      for (let i = 1; i <= 8; i++) {
        const nextMonday = new Date(thisMonday);
        nextMonday.setDate(thisMonday.getDate() + (i * 7));
        const nextSunday = new Date(nextMonday);
        nextSunday.setDate(nextMonday.getDate() + 6);

        const targetYear = nextMonday.getFullYear();
        const startOfYear = new Date(targetYear, 0, 1);
        const days = Math.floor((nextMonday - startOfYear) / (24 * 60 * 60 * 1000));
        const weekNum = Math.ceil((days + startOfYear.getDay() + 1) / 7);

        const label = `${nextMonday.getMonth() + 1}월 ${nextMonday.getDate()}일 ~ ${nextSunday.getMonth() + 1}월 ${nextSunday.getDate()}일 (${weekNum}주차)`;
        
        currentWeeksList.push({
          year: targetYear,
          week: weekNum,
          label: label,
          key: `${targetYear}-${weekNum}`
        });
      }
      
      setAvailableWeeks(currentWeeksList);
      if (currentWeeksList.length > 0) {
        setSelectedTimeKey(currentWeeksList[0].key);
      }
    };

    generateFutureWeeks();
  }, []);

  const getSelectedTime = () => {
    if (!selectedTimeKey) return { year: 2026, week: 25 };
    const [year, week] = selectedTimeKey.split('-');
    return { year: Number(year), week: Number(week) };
  };

  const fetchTopDanger = async () => {
    if (!diseaseName || !isPredictable || !selectedTimeKey) {
      setTopDanger([]);
      return;
    }
    
    const { year, week } = getSelectedTime();
    setLoadingTop(true);
    try {
      const res = await fetch(`${AI_BACKEND_URL}/predict/top-danger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disease: diseaseName, year, week })
      });
      if (res.ok) {
        const data = await res.json();
        setTopDanger(data.top_regions || []);
        
        // 시계열 변동 흐름 트래킹 시각화 데이터 매핑
        setPrevNationalCases(nationalCases); 
        setNationalCases(data.national_cases || 0);
      }
    } catch (err) {
      console.error("예측 데이터 바인딩 실패:", err);
    } finally {
      setLoadingTop(false);
    }
  };

  const handleRegionSearch = async (e) => {
    e.preventDefault();
    if (!diseaseName || !isPredictable || !selectedTimeKey) return;
    
    const { year, week } = getSelectedTime();
    setLoadingSearch(true);
    try {
      const res = await fetch(`${AI_BACKEND_URL}/predict/region`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disease: diseaseName, year, week, region: searchRegion })
      });
      if (res.ok) {
        const data = await res.json();
        setSinglePrediction(data.predicted_cases);
      }
    } catch (err) {
      console.error("지역별 예측 데이터 연동 실패:", err);
    } finally {
      setLoadingSearch(false);
    }
  };

  useEffect(() => {
    setSinglePrediction(null);
    fetchTopDanger();
  }, [diseaseName, selectedTimeKey]);

  if (!isPredictable) {
    return (
      <div style={{
        backgroundColor: 'rgba(30, 41, 59, 0.7)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '30px',
        textAlign: 'center',
        color: '#94a3b8'
      }}>
        <div style={{ fontSize: '1.2rem', marginBottom: '8px', color: '#f43f5e' }}>🔮 예측 모델 미지원 질병</div>
        [{diseaseName}]은 현재 시계열 예측 가중치 모델 생성 대상이 아닙니다.
      </div>
    );
  }

  const selectedWeekLabel = availableWeeks.find(w => w.key === selectedTimeKey)?.label || '';
  
  // 변동 지표 연산 데이터셋 생성
  const diff = nationalCases - prevNationalCases;

  return (
    <div style={{
      backgroundColor: 'rgba(30, 41, 59, 0.7)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
      color: '#f8fafc'
    }}>
      
      {/* 컨트롤러 패널 */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '25px', paddingBottom: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: '1.35rem', color: '#38bdf8', fontWeight: 'bold' }}>
          🔮 머신러닝 기반 감염병 확산 예측 엔진
        </h2>
        
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '15px', alignItems: 'center' }}>
          <label style={{ fontSize: '0.9rem', color: '#94a3b8' }}>예측 대상 기간 선택</label>
          <select 
            value={selectedTimeKey} 
            onChange={(e) => setSelectedTimeKey(e.target.value)} 
            style={{ padding: '8px 16px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.1)', color: '#f8fafc', fontSize: '0.9rem' }}
          >
            {availableWeeks.map(w => (
              <option key={w.key} value={w.key}>{w.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* TOP 3 순수 위험 구역 렌더링 영역 */}
      <div style={{ marginBottom: '30px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '16px', color: '#f43f5e', display: 'flex', alignItems: 'center', gap: '8px' }}>
          🚨 {selectedWeekLabel.split(' (')[0]} [{diseaseName}] 감염 위험 다발 지역 TOP 3 (시군구 기준)
        </h3>
        
        {loadingTop ? (
          <div style={{ color: '#94a3b8', padding: '10px 0' }}>XGBoost 매트릭스 연산 수행 중...</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
            {topDanger.map((item, index) => (
              <div key={index} style={{ 
                padding: '20px', 
                background: 'rgba(15, 23, 42, 0.6)', 
                borderRadius: '12px', 
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderLeft: index === 0 ? '5px solid #ef4444' : index === 1 ? '5px solid #f97316' : '5px solid #eab308'
              }}>
                <div style={{ fontWeight: 'bold', fontSize: '1.05rem', marginBottom: '6px' }}>
                  {index + 1}위 : {item.region}
                </div>
                <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
                  예상 발생 건수: <span style={{ fontWeight: 'bold', color: '#38bdf8', fontSize: '1.1rem' }}>{item.predicted_cases}</span> 건
                </div>
              </div>
            ))}
            {!loadingTop && topDanger.length === 0 && (
              <div style={{ color: '#94a3b8', gridColumn: 'span 3' }}>예측 연산 결과가 존재하지 않습니다.</div>
            )}
          </div>
        )}
      </div>

      {/* 전국 총합 수치 및 삼각 마크 디스플레이 카드 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'between', 
        alignItems: 'center',
        padding: '18px 24px', 
        background: 'rgba(30, 41, 59, 0.4)', 
        borderRadius: '12px', 
        border: '1px solid rgba(255, 255, 255, 0.08)',
        marginBottom: '30px'
      }}>
        <div>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '4px' }}>전국 총합 수치 통계 매트릭스</div>
          <div style={{ fontSize: '1.05rem', fontWeight: 'bold' }}>대한민국 전체 예상 발생 확진자 수</div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ fontSize: '1.75rem', fontWeight: 'bold', color: '#fff' }}>{nationalCases} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>건</span></div>
          
          {/* 전주 대비 상승/하락 조건부 렌더링 팩터 */}
          {!prevNationalCases || prevNationalCases === 0 ? (
            // 지난주 데이터가 없거나 0일 때는 깔끔하게 회색 대시(-) 처리
            <div style={{ color: '#94a3b8', fontSize: '1rem', fontWeight: 'bold' }}>-</div>
          ) : diff > 0 ? (
            <div style={{ color: '#ef4444', fontSize: '1rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '2px' }}>
              ▲ {diff}건 상승
            </div>
          ) : diff < 0 ? (
            <div style={{ color: '#3b82f6', fontSize: '1rem', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '2px' }}>
              ▼ {Math.abs(diff)}건 감소
            </div>
          ) : (
            <div style={{ color: '#94a3b8', fontSize: '1rem', fontWeight: 'bold' }}>- 변동 없음</div>
          )}
        </div>
      </div>

      {/* 개별 조회 구역 */}
      <div style={{ padding: '24px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '16px', color: '#38bdf8' }}>
          🔍 우리 동네 감염병 발생 예측치 개별 조회
        </h3>
        
        <form onSubmit={handleRegionSearch} style={{ display: 'flex', gap: '15px', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ flex: 1 }}>
            <input 
              type="text" 
              value={searchRegion} 
              onChange={(e) => setSearchRegion(e.target.value)} 
              placeholder="예: 서울 강남구, 충남 계룡시"
              style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc' }}
            />
          </div>
          <button type="submit" disabled={loadingSearch}
            style={{ padding: '10px 24px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            {loadingSearch ? '조회 중...' : 'AI 예측치 조회'}
          </button>
        </form>

        {singlePrediction !== null && (
          <div style={{ padding: '16px 20px', background: 'rgba(56, 189, 248, 0.1)', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)', color: '#e2e8f0', lineHeight: '1.6' }}>
            💡 <strong>{selectedWeekLabel.split(' (')[0]}</strong>에 <strong>{searchRegion}</strong>의 
            <strong> [{diseaseName}]</strong> 예상 감염자 수는 총 <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#38bdf8' }}>{singlePrediction}명</span>으로 계량 예측됩니다.
          </div>
        )}
      </div>

    </div>
  );
}