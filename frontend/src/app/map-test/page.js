'use client';

import dynamic from 'next/dynamic';
import React, { useState } from 'react';
import InfectionMap from '@/components/InfectionMap';
import AIInsightsPanel from '@/components/AIInsightsPanel';
import './mapStyles.css';

const RealMap = dynamic(() => import('@/components/RealMap'), {
  ssr: false,
  loading: () => <div style={{ height: '650px', display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: '#f8fafc', color: '#94a3b8', borderRadius: '12px' }}>지도 불러오는 중...</div>
});

export default function MapTestPage() {
  const [selectedDisease, setSelectedDisease] = useState('수두');
  const [mapMode, setMapMode] = useState('real'); // 'static' or 'real'
  const diseases = ['수두', '백일해', '유행성이하선염', '코로나19', '에볼라', '한타바이러스'];

  return (
    <div className="pageContainer">
      <div className="pageInner">
        <h1 className="pageTitle">
          KDCA 전파 지도 시각화 테스트
        </h1>
        
        <div className="diseaseButtons">
          {diseases.map(disease => (
            <button
              key={disease}
              onClick={() => setSelectedDisease(disease)}
              className={`diseaseBtn ${selectedDisease === disease ? 'active' : ''}`}
            >
              {disease}
            </button>
          ))}
        </div>

        {/* 맵 모드 스위치 추가 */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', backgroundColor: '#1e293b', borderRadius: '8px', padding: '4px' }}>
            <button 
              onClick={() => setMapMode('static')}
              style={{
                padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold',
                backgroundColor: mapMode === 'static' ? '#3b82f6' : 'transparent',
                color: mapMode === 'static' ? '#fff' : '#94a3b8',
                transition: 'all 0.2s'
              }}>
              기존 버전 (정적 다각형)
            </button>
            <button 
              onClick={() => setMapMode('real')}
              style={{
                padding: '8px 16px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold',
                backgroundColor: mapMode === 'real' ? '#ef4444' : 'transparent',
                color: mapMode === 'real' ? '#fff' : '#94a3b8',
                transition: 'all 0.2s'
              }}>
              최신 버전 (실제 지도 + 버블 맵)
            </button>
          </div>
        </div>

        <div style={{ 
          marginTop: '2rem', 
          display: 'grid', 
          gridTemplateColumns: '2fr 1fr', 
          gap: '24px',
          alignItems: 'start'
        }}>
          <div style={{ height: '700px' }}>
            {mapMode === 'static' ? (
              <InfectionMap diseaseName={selectedDisease} />
            ) : (
              <RealMap diseaseName={selectedDisease} />
            )}
          </div>
          <div style={{ height: '700px' }}>
            <AIInsightsPanel diseaseName={selectedDisease} />
          </div>
        </div>
      </div>
    </div>
  );
}
