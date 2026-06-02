"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";

const AzureMap = dynamic(() => import("./mapAzure"), {
  ssr: false,
  loading: () => (
    <div style={{ 
      width: "100%", 
      height: "600px", 
      display: "flex", 
      justifyContent: "center", 
      alignItems: "center", 
      backgroundColor: "#f8fafc",
      color: "#64748b",
      borderRadius: "12px"
    }}>
      지도를 불러오는 중입니다...
    </div>
  ),
});

export default function Home() {
  const [selectedDisease, setSelectedDisease] = useState("코로나19");

  const diseases = ["코로나19", "독감", "뎅기열", "말라리아", "신증후군출혈열"];

  return (
    <main className="container animate-fade-in">
      <header style={{ marginBottom: '40px', textAlign: 'center' }}>
        <h1 className="title-gradient" style={{ fontSize: '3rem', marginBottom: '16px' }}>우리 동네 감염병 브리핑</h1>
        <p className="subtitle">AI 기반 실시간 뉴스 분석 및 지역 통계 현황</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3>선택된 질병</h3>
            <span className="badge success">관찰중</span>
          </div>
          <h1 style={{ fontSize: '2.5rem', margin: '10px 0', color: 'var(--text-main)' }}>{selectedDisease}</h1>
          <select 
            value={selectedDisease} 
            onChange={(e) => setSelectedDisease(e.target.value)}
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', fontSize: '1rem', marginTop: '10px', width: '100%' }}
          >
            {diseases.map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3>전국 위험도 요약</h3>
            <span className="badge warning">AI 분석</span>
          </div>
          <p className="subtitle" style={{ lineHeight: '1.6' }}>
            지도에 표시된 위험도(Red, Orange, Green)는 <strong>질병관리청 확진자 수</strong>와 <strong>AI 뉴스 기반 정성적 평가</strong>가 결합된 하이브리드 결과입니다. 선(Line)은 확산의 주요 방향을 나타냅니다.
          </p>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3>AI 행동 지침</h3>
            <span className="badge success">안내</span>
          </div>
          <ul style={{ listStylePosition: 'inside', lineHeight: '1.8', color: 'var(--text-muted)' }}>
            <li><strong style={{ color: 'var(--text-main)' }}>마스크 착용:</strong> 대중교통 및 다중이용시설</li>
            <li><strong style={{ color: 'var(--text-main)' }}>위생 관리:</strong> 귀가 후 손 씻기 생활화</li>
            <li><strong style={{ color: 'var(--text-main)' }}>관찰 요망:</strong> 확산 경로에 인접한 지역</li>
          </ul>
        </div>
      </div>

      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ marginBottom: '16px', color: 'var(--text-main)' }}>지역별 감염병 확산 지도 ({selectedDisease})</h2>

        <div className="glass-card" style={{ position: 'relative', overflow: 'hidden', padding: '0' }}>
          <div>
            <AzureMap disease={selectedDisease} />
          </div>
        </div>
      </div>
    </main>
  );
}
