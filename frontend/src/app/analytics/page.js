"use client";

import React, { useState } from "react";
import RegionalRankingChart from "@/components/analytics/RegionalRankingChart";
import ScatterRiskChart from "@/components/analytics/ScatterRiskChart";
import MultiDiseaseTrendChart from "@/components/analytics/MultiDiseaseTrendChart";

export default function AnalyticsPage() {
  const [selectedDisease, setSelectedDisease] = useState("코로나19");
  const diseases = ["코로나19", "수두", "백일해", "유행성이하선염", "에볼라"];

  return (
    <main className="container animate-fade-in" style={{ paddingBottom: '60px' }}>
      <header style={{ marginBottom: '40px', textAlign: 'center' }}>
        <h1 className="title-gradient" style={{ fontSize: '2.5rem', marginBottom: '16px' }}>심층 통계 분석 (Test)</h1>
        <p className="subtitle">다양한 차트를 통해 전염병의 확산 양상을 입체적으로 분석합니다.</p>
      </header>

      {/* 질병 선택기 */}
      <div className="glass-card" style={{ marginBottom: '32px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px' }}>
        <h3 style={{ margin: 0, color: '#94a3b8' }}>분석 대상 질병:</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {diseases.map(disease => (
            <button
              key={disease}
              onClick={() => setSelectedDisease(disease)}
              style={{
                padding: '8px 16px',
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

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* 시도별 랭킹 차트 */}
        <RegionalRankingChart diseaseName={selectedDisease} />
        
        {/* 산점도 차트 */}
        <ScatterRiskChart diseaseName={selectedDisease} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
        {/* 다중 질병 비교 시계열 차트 */}
        <MultiDiseaseTrendChart targetDiseases={diseases} />
      </div>
    </main>
  );
}
