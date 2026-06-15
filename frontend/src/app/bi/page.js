"use client";

import React, { useState, useEffect, useMemo } from "react";
import BIDemographicChart from "@/components/bi/BIDemographicChart";
import BIInfrastructureChart from "@/components/bi/BIInfrastructureChart";
import BIMobilityChart from "@/components/bi/BIMobilityChart";

export default function BIDashboardPage() {
  const [dataset, setDataset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Cross-filtering states
  const [selectedDisease, setSelectedDisease] = useState("전체");
  const [selectedRegion, setSelectedRegion] = useState("전체");

  useEffect(() => {
    const fetchDataset = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/api/powerbi/dataset`);
        if (!response.ok) throw new Error("BI 데이터셋을 불러오는데 실패했습니다.");
        const data = await response.json();
        setDataset(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchDataset();
  }, []);

  const diseaseOptions = ["전체", "코로나19", "수두", "백일해", "유행성이하선염"];
  
  // Extract unique regions from Dim_Region
  const regionOptions = useMemo(() => {
    if (!dataset?.Dim_Region) return ["전체"];
    const regions = dataset.Dim_Region.map(r => r.region);
    return ["전체", ...regions];
  }, [dataset]);

  if (loading) {
    return (
      <main className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <h2 style={{ color: '#38bdf8' }}>BI 데이터 통합 로딩 중...</h2>
      </main>
    );
  }

  if (error) {
    return (
      <main className="container">
        <div style={{ color: '#ef4444', textAlign: 'center', marginTop: '50px' }}>{error}</div>
      </main>
    );
  }

  return (
    <main className="container animate-fade-in" style={{ paddingBottom: '60px' }}>
      <header style={{ marginBottom: '32px', textAlign: 'center' }}>
        <h1 className="title-gradient" style={{ fontSize: '2.5rem', marginBottom: '8px' }}>종합 BI 분석 대시보드</h1>
        <p className="subtitle">인구, 의료 인프라, 유동인구 데이터를 감염병 확산 지표와 교차 분석합니다.</p>
      </header>

      {/* Slicers (Filters) */}
      <div className="glass-card" style={{ marginBottom: '24px', display: 'flex', gap: '32px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ color: '#94a3b8', fontWeight: 'bold' }}>💉 분석 질병:</label>
          <select 
            value={selectedDisease} 
            onChange={(e) => setSelectedDisease(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: '6px', backgroundColor: 'rgba(15,23,42,0.8)', color: '#f8fafc', border: '1px solid rgba(255,255,255,0.1)' }}
          >
            {diseaseOptions.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ color: '#94a3b8', fontWeight: 'bold' }}>📍 분석 지역:</label>
          <select 
            value={selectedRegion} 
            onChange={(e) => setSelectedRegion(e.target.value)}
            style={{ padding: '8px 12px', borderRadius: '6px', backgroundColor: 'rgba(15,23,42,0.8)', color: '#f8fafc', border: '1px solid rgba(255,255,255,0.1)' }}
          >
            {regionOptions.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* 인구통계 파이 차트 */}
        <BIDemographicChart 
          demographics={dataset.Fact_Demographics} 
          selectedDisease={selectedDisease === "전체" ? "코로나19" : selectedDisease} 
        />
        
        {/* 의료 인프라 바/산점도 차트 */}
        <BIInfrastructureChart 
          regions={dataset.Dim_Region} 
          infections={dataset.Fact_Infections}
          selectedDisease={selectedDisease}
          selectedRegion={selectedRegion}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
        {/* 유동인구 vs 확진자 콤보 차트 */}
        <BIMobilityChart 
          mobility={dataset.Fact_Mobility}
          infections={dataset.Fact_Infections}
          selectedDisease={selectedDisease}
          selectedRegion={selectedRegion}
        />
      </div>
    </main>
  );
}
