"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import AIInsightsPanel from "@/components/AIInsightsPanel";
import InfectionMap from "@/components/InfectionMap";
import TotalStatsPanel from "@/components/TotalStatsPanel";

const RealMap = dynamic(() => import("@/components/RealMap"), {
  ssr: false,
  loading: () => (
    <div style={{ 
      height: '650px', 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      backgroundColor: 'rgba(30, 41, 59, 0.7)', 
      color: '#94a3b8', 
      borderRadius: '16px',
      border: '1px solid rgba(255, 255, 255, 0.1)'
    }}>
      지도 불러오는 중...
    </div>
  )
});

export default function Home() {
  const [selectedDisease, setSelectedDisease] = useState("코로나19");
  const [mapMode, setMapMode] = useState("real"); // 'static' or 'real'
  const diseases = ["코로나19", "수두", "백일해", "유행성이하선염", "에볼라"];

  return (
    <main className="container animate-fade-in" style={{ paddingBottom: '60px' }}>
      <header style={{ marginBottom: '40px', textAlign: 'center' }}>
        <h1 className="title-gradient" style={{ fontSize: '3rem', marginBottom: '16px' }}>우리 동네 감염병 브리핑</h1>
        <p className="subtitle">AI 기반 실시간 뉴스 분석 및 지역 통계 현황</p>
      </header>

      {/* 상단 요약 카드 섹션 (기존 루트에 있던 내용) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ margin: 0 }}>선택된 질병</h3>
            <span className="badge success">관찰중</span>
          </div>
          
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
            {diseases.map(disease => (
              <button
                key={disease}
                onClick={() => setSelectedDisease(disease)}
                style={{
                  padding: '10px 16px',
                  borderRadius: '8px',
                  border: selectedDisease === disease ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.1)',
                  backgroundColor: selectedDisease === disease ? 'rgba(56, 189, 248, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  color: selectedDisease === disease ? '#38bdf8' : '#e2e8f0',
                  cursor: 'pointer',
                  fontWeight: selectedDisease === disease ? 'bold' : 'normal',
                  transition: 'all 0.2s ease'
                }}
              >
                {disease}
              </button>
            ))}
          </div>
        </div>

        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0 }}>전국 위험도 요약</h3>
            <span className="badge warning">AI 분석 적용</span>
          </div>
          <p className="subtitle" style={{ lineHeight: '1.6', margin: 0 }}>
            지도에 표시된 위험도(초록, 노랑, 빨강)는 <strong>질병관리청 확진자 수</strong>와 <strong>AI 뉴스 기반 정성적 평가</strong>가 결합된 하이브리드 결과입니다. 좌측의 지도를 통해 확산 방향을, 우측의 AI 리포트 패널을 통해 전수 검색 기반의 상세한 최신 동향을 파악할 수 있습니다.
          </p>
        </div>
      </div>

      {/* 맵 모드 스위치 */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
        <div style={{ display: 'flex', backgroundColor: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '4px', border: '1px solid rgba(255,255,255,0.1)' }}>
          <button 
            onClick={() => setMapMode('static')}
            style={{
              padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.9rem',
              backgroundColor: mapMode === 'static' ? '#3b82f6' : 'transparent',
              color: mapMode === 'static' ? '#fff' : '#94a3b8',
              transition: 'all 0.2s'
            }}>
            정적 다각형 모드
          </button>
          <button 
            onClick={() => setMapMode('real')}
            style={{
              padding: '8px 20px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.9rem',
              backgroundColor: mapMode === 'real' ? '#ef4444' : 'transparent',
              color: mapMode === 'real' ? '#fff' : '#94a3b8',
              transition: 'all 0.2s'
            }}>
            동적 확산 맵 모드
          </button>
        </div>
      </div>

      {/* 메인 2단 레이아웃: 지도 + 리포트 */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'minmax(0, 1.8fr) minmax(0, 1.2fr)', 
        gap: '24px',
        alignItems: 'start'
      }}>
        {/* 좌측: 지도 영역 */}
        <div className="glass-card" style={{ height: '750px', padding: 0, overflow: 'hidden' }}>
          {mapMode === 'static' ? (
            <InfectionMap diseaseName={selectedDisease} />
          ) : (
            <RealMap diseaseName={selectedDisease} />
          )}
        </div>

        {/* 우측: 전국 단위 통계 패널 + AI 리포트 패널 */}
        <div style={{ display: 'flex', flexDirection: 'column', height: '750px' }}>
          {/* 1. 전국 통합 지표 차트 패널 */}
          <TotalStatsPanel diseaseName={selectedDisease} />
          
          {/* 2. AI 리포트 패널 */}
          <div style={{ flex: 1, minHeight: 0 }}>
            <AIInsightsPanel diseaseName={selectedDisease} />
          </div>
        </div>
      </div>
    </main>
  );
}
