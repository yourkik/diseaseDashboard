"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import AIInsightsPanel from "@/components/AIInsightsPanel";
import PredictionPanel from '@/components/PredictionPanel';
import OverallMap from "@/components/OverallMap";
import TotalStatsPanel from "@/components/TotalStatsPanel";


import EWSSidebar from "@/components/EWSSidebar";

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
  const [selectedDisease, setSelectedDisease] = useState("전체");
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const diseases = ["전체", "코로나19", "수두", "백일해", "유행성이하선염", "에볼라"];

  React.useEffect(() => {
    window.handleRegionSelect = (region) => {
      setSelectedRegion(region);
    };
    return () => {
      delete window.handleRegionSelect;
    };
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;
    
    // 질병 검색 매칭
    const diseaseMatch = diseases.find(d => d.includes(searchTerm) || searchTerm.includes(d));
    if (diseaseMatch) {
      setSelectedDisease(diseaseMatch);
    }
    
    // 지역 검색 매칭 (시도 명칭 간소화 버전)
    const regionKeywords = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"];
    const regionMatch = regionKeywords.find(r => searchTerm.includes(r) || r.includes(searchTerm));
    if (regionMatch) {
      setSelectedRegion(regionMatch);
    }
    
    setSearchTerm("");
  };

  return (
    <main className="container animate-fade-in" style={{ paddingBottom: '60px' }}>
      <header style={{ marginBottom: '40px', textAlign: 'center' }}>
        <h1 className="title-gradient" style={{ fontSize: '3rem', marginBottom: '16px' }}>우리 동네 감염병 브리핑</h1>
        <p className="subtitle">AI 기반 실시간 뉴스 분석 및 지역 조기 경보(EWS)</p>
      </header>

      {/* 상단 요약 카드 섹션 (기존 루트에 있던 내용) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px', marginBottom: '40px' }}>

        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ margin: 0 }}>선택된 질병</h3>
            <span className="badge success">관찰중</span>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '20px' }}>
            {diseases.map(disease => (
              <button
                key={disease}
                onClick={() => setSelectedDisease(disease)}
                style={{
                  padding: '10px 16px',
                  borderRadius: '8px',
                  border: selectedDisease === disease ? (disease === '전체' ? '2px solid #9333ea' : '2px solid #2563eb') : '1px solid #cbd5e1',
                  backgroundColor: selectedDisease === disease ? (disease === '전체' ? '#f3e8ff' : '#eff6ff') : '#ffffff',
                  color: selectedDisease === disease ? (disease === '전체' ? '#7e22ce' : '#1d4ed8') : '#475569',
                  cursor: 'pointer',
                  fontWeight: selectedDisease === disease ? 'bold' : '600',
                  transition: 'all 0.2s ease'
                }}
              >
                {disease}
              </button>
            ))}
          </div>

          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
            <input 
              type="text" 
              placeholder="지역명(예: 서울) 또는 질병명(예: 수두) 검색..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                flex: 1,
                padding: '10px 16px',
                borderRadius: '8px',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                color: '#fff',
                outline: 'none'
              }}
            />
            <button type="submit" style={{
              padding: '10px 20px',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: '#3b82f6',
              color: '#fff',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}>검색</button>
          </form>
        </div>

        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0 }}>전국 위험도 요약</h3>
            <span className="badge warning">AI 분석 적용</span>
          </div>
          <p className="subtitle" style={{ lineHeight: '1.6', margin: 0 }}>
            지도에 표시된 위험도는 질병관리청 확진자 수와 AI 뉴스 기반 평가가 결합된 결과입니다.<br/>
            지도를 클릭하면 해당 지역의 <strong>실시간 조기 경보(EWS) 뉴스 타임라인</strong>을 볼 수 있습니다.
          </p>
        </div>
      </div>

      {/* 메인 레이아웃 (전체 모드일 때는 1단 레이아웃, 아닐 때는 2단 레이아웃) */}
      <div style={{ position: 'relative' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: selectedDisease === "전체" ? '1fr' : 'minmax(0, 1.8fr) minmax(0, 1.2fr)',
          gap: '24px',
          alignItems: 'start'
        }}>
          {/* 좌측(또는 전체): 지도 영역 */}
          <div className="glass-card" style={{ height: '750px', padding: 0, overflow: 'hidden', position: 'relative' }}>
            {selectedDisease === "전체" ? (
              <OverallMap />
            ) : (
              <RealMap diseaseName={selectedDisease} />
            )}
            
            {/* 지역 클릭 시 지도 위에 오버레이로 뜨는 조기경보 패널 */}
            {selectedRegion && (
              <div style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                width: '380px',
                bottom: '20px',
                zIndex: 100,
                animation: 'slideInRight 0.3s ease-out forwards'
              }}>
                <EWSSidebar 
                  regionName={selectedRegion} 
                  diseaseName={selectedDisease} 
                  onClose={() => setSelectedRegion(null)} 
                />
              </div>
            )}
          </div>

          {/* 우측: 질병 종합 AI 리포트 패널 (전체 모드일 때는 숨김) */}
          {selectedDisease !== "전체" && (
            <div style={{ display: 'flex', flexDirection: 'column', height: '750px' }}>
              <div style={{ flex: 1, minHeight: 0 }}>
                <AIInsightsPanel diseaseName={selectedDisease} />
              </div>
            </div>
          )}
        </div>
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes slideInRight {
            from { transform: translateX(50px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
          }
        `}} />
      </div>
      
      {/* 3. 예측 패널 */}
      <div style={{ width: '100%', marginTop: '24px' }}>
        <PredictionPanel diseaseName={selectedDisease} />
      </div>
    </main>
  );
}
