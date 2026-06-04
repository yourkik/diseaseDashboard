"use client";

import React from "react";
import dynamic from "next/dynamic";

const AzureMap = dynamic(() => import("../mapAzure"), {
  ssr: false,
  loading: () => (
    <div style={{ 
      width: "100%", height: "450px", display: "flex", justifyContent: "center", 
      alignItems: "center", backgroundColor: "#f8fafc", color: "#64748b", borderRadius: "12px"
    }}>
      Azure Maps를 불러오는 중입니다...
    </div>
  ),
});

export default function AzureTestPage() {
  return (
    <main className="container animate-fade-in">
      <header style={{ marginBottom: '40px', textAlign: 'center' }}>
        <h1 className="title-gradient" style={{ fontSize: '3rem', marginBottom: '16px' }}>우리 동네 감염병 브리핑</h1>
        <p className="subtitle">AI 기반 실시간 뉴스 분석 및 지역 통계 현황 (Azure Maps 빌드)</p>
      </header>

      {/* 대시보드 통계 카드 지표 영역 (동일 유지) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3>현재 위험도</h3>
            <span className="badge warning">주의</span>
          </div>
          <h1 style={{ fontSize: '3.5rem', margin: '10px 0', color: 'var(--warning)' }}>Level 2</h1>
          <p className="subtitle">전국적인 독감 유행 조짐. 환자 수 급증 중.</p>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3>일일 확진자 (모의)</h3>
            <span className="badge danger">↑ 15%</span>
          </div>
          <h1 style={{ fontSize: '3.5rem', margin: '10px 0', color: 'var(--text-main)' }}>15,034<span style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}> 명</span></h1>
          <p className="subtitle">어제 대비 2,010명 증가</p>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3>AI 행동 지침</h3>
            <span className="badge success">안내</span>
          </div>
          <ul style={{ listStylePosition: 'inside', lineHeight: '1.8', color: 'var(--text-muted)' }}>
            <li><strong style={{ color: 'var(--text-main)' }}>마스크 착용:</strong> 대중교통 및 다중이용시설</li>
            <li><strong style={{ color: 'var(--text-main)' }}>위생 관리:</strong> 귀가 후 손 씻기 생활화</li>
            <li><strong style={{ color: 'var(--text-main)' }}>병원 방문:</strong> 고열 발생 시 즉시 내원</li>
          </ul>
        </div>
      </div>

      {/* 공간 데이터 시각화 영역 */}
      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ marginBottom: '16px', color: 'var(--text-main)' }}>지역별 감염병 확산 지도</h2>
        <div className="glass-card" style={{ position: 'relative', overflow: 'hidden', padding: '0' }}>
          <div>
            <AzureMap />
          </div>
        </div>
      </div>

      {/* 최신 AI 뉴스 요약 영역 */}
      <h2 style={{ marginBottom: '24px', color: 'var(--text-main)' }}>최신 AI 뉴스 요약 (RAG)</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="glass-card" style={{ borderLeft: '4px solid var(--warning)' }}>
          <h3 style={{ marginBottom: '8px' }}>올 겨울 독감 유행 조짐... 보건당국 긴장</h3>
          <p style={{ color: 'var(--text-muted)' }}>AI 분석: 현재 독감 환자가 전국적으로 급증하고 있어 주의가 필요합니다. 대중교통 및 다중이용시설 방문 시 마스크 착용을 권장합니다.</p>
          <div style={{ marginTop: '12px', fontSize: '0.85rem', color: '#64748b' }}>방금 전 • 빙(Bing) 뉴스 기반</div>
        </div>
        <div className="glass-card" style={{ borderLeft: '4px solid var(--danger)' }}>
          <h3 style={{ marginBottom: '8px' }}>New Infectious Disease Outbreak in Southeast Asia</h3>
          <p style={{ color: 'var(--text-muted)' }}>AI 분석: 동남아시아 지역에서 새로운 감염병이 발생하여 모니터링 중입니다. 해당 지역으로의 여행 시 각별한 주의와 사전 예방 접종 확인이 필요합니다.</p>
          <div style={{ marginTop: '12px', fontSize: '0.85rem', color: '#64748b' }}>2시간 전 • 글로벌 모니터링</div>
        </div>
      </div>
    </main>
  );
}
