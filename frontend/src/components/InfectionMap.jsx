'use client';

import React, { useState, useEffect } from 'react';
import { ComposableMap, Geographies, Geography, Line, Marker, ZoomableGroup } from 'react-simple-maps';
import { scaleLinear } from 'd3-scale';
import { AlertTriangle } from 'lucide-react';
import './mapStyles.css';

const KOREA_TOPO_JSON = '/korea-topo.json';
const CONGO_TOPO_JSON = '/congo-topo.json';

const colorScale = scaleLinear()
  .domain([0, 10, 50, 100])
  .range(["#1e293b", "#3b82f6", "#f59e0b", "#ef4444"]);

// 대한민국 17개 시도 대략적 중심 좌표 [경도, 위도]
const REGION_COORDS = {
  "서울": [126.9780, 37.5665],
  "부산": [129.0756, 35.1796],
  "대구": [128.6014, 35.8714],
  "인천": [126.7052, 37.4563],
  "광주": [126.8526, 35.1595],
  "대전": [127.3845, 36.3504],
  "울산": [129.3114, 35.5384],
  "세종": [127.2890, 36.4800],
  "경기": [127.1678, 37.2752],
  "강원": [128.1555, 37.8228],
  "충북": [127.4917, 36.6358],
  "충남": [126.6583, 36.5188],
  "전북": [127.1088, 35.7175],
  "전남": [126.9910, 34.8161],
  "경북": [128.8889, 36.4919],
  "경남": [128.2132, 35.2383],
  "제주": [126.5312, 33.4996]
};

export default function InfectionMap({ diseaseName }) {
  const [aggregatedData, setAggregatedData] = useState({});
  const [rawData, setRawData] = useState({});
  const [loading, setLoading] = useState(true);
  const [tooltipData, setTooltipData] = useState(null);

  const isEbola = diseaseName === '에볼라';
  const currentGeoUrl = isEbola ? CONGO_TOPO_JSON : KOREA_TOPO_JSON;
  const currentCenter = isEbola ? [23.5, -2.5] : [127.5, 36];
  const currentScale = isEbola ? 2000 : 5500;

  // 데이터 Fetching 및 연간 총합 집계
  useEffect(() => {
    const fetchSpreadData = async () => {
      setLoading(true);
      try {
        // 정적 지도이므로 월별 가짜 데이터(/spread) 대신 실제 연간 지역 데이터(/status) 호출
        // 백엔드에서 기본값으로 최신 연도(올해) 데이터를 불러옵니다.
        const res = await fetch(`http://localhost:8000/api/stats/map/status?disease=${diseaseName}`);
        if (!res.ok) throw new Error("Backend server error");
        
        const data = await res.json();
        
        // /status 응답 포맷: { "서울": { "region": "서울", "count": 1477, "rate": 15.6 }, ... }
        const totals = {};
        const rawMap = {};
        Object.values(data).forEach(item => {
          let region = isEbola ? item.region : item.region.substring(0, 2); 
          totals[region] = item.count;
          rawMap[region] = item;
        });
        
        setAggregatedData(totals);
        setRawData(rawMap);
      } catch (err) {
        console.error("Failed to fetch map data", err);
      } finally {
        setLoading(false);
      }
    };
    
    if (diseaseName) fetchSpreadData();
  }, [diseaseName]);

  // 확산 방향(화살표) 계산 로직: 확진자가 가장 많은 1위 지역에서 2~4위 지역으로 전파된다고 가정 (시각화 연출용)
  const sortedRegions = Object.entries(aggregatedData)
    .filter(([name, count]) => REGION_COORDS[name] && count > 0)
    .sort((a, b) => b[1] - a[1]);

  const sourceRegion = sortedRegions.length > 0 ? sortedRegions[0][0] : null;
  const targetRegions = sortedRegions.slice(1, 4).map(item => item[0]); // 상위 3곳 타겟

  // 지역 이름 정규화 (topojson 프로퍼티 매핑용)
  const normalizeRegion = (name) => {
    if (!name) return "";
    if (name.includes("경상남도")) return "경남";
    if (name.includes("경상북도")) return "경북";
    if (name.includes("전라남도")) return "전남";
    if (name.includes("전라북도") || name.includes("전북특별자치도")) return "전북";
    if (name.includes("충청남도")) return "충남";
    if (name.includes("충청북도")) return "충북";
    if (name.includes("제주")) return "제주";
    if (name.includes("세종")) return "세종";
    if (name.includes("강원")) return "강원";
    return name.substring(0, 2);
  };

  let periodDisplay = isEbola ? "HDX 글로벌 데이터 (2026년)" : "데이터 로드 중...";
  if (!isEbola && Object.keys(rawData).length > 0) {
    const firstItem = Object.values(rawData)[0];
    if (firstItem.period) {
      periodDisplay = firstItem.period.includes("누적 데이터") 
        ? firstItem.period 
        : `${firstItem.period} 기준 데이터`;
    } else {
      periodDisplay = "최신 누적 데이터";
    }
  }

  return (
    <div className="mapContainer">
      <div className="mapHeader">
        <div>
          <h2 className="mapTitle">
            {diseaseName} 정적 확산 지도 (Static)
          </h2>
          <p className="mapSubtitle">연간 누적 감염 현황 및 주요 확산 경로 추정</p>
        </div>
        <div className="periodBadge">
          <AlertTriangle color="#fbbf24" size={20} />
          <span>{periodDisplay}</span>
        </div>
      </div>

      <div className="mapViewArea">
        {loading ? (
          <div style={{ color: '#2dd4bf', fontWeight: 'bold' }}>데이터를 불러오는 중입니다...</div>
        ) : (
          <>
            {Object.keys(aggregatedData).length > 0 && Object.values(aggregatedData).every(v => v === 0) && (
              <div style={{
                position: 'absolute', top: '20px', left: '50%', transform: 'translateX(-50%)',
                backgroundColor: 'rgba(239, 68, 68, 0.9)', color: 'white', padding: '10px 20px',
                borderRadius: '8px', fontWeight: 'bold', zIndex: 10, boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
                border: '1px solid #fca5a5'
              }}>
                🚫 현재 데이터 기준 국내 감염자 없음 (0명)
              </div>
            )}
            <ComposableMap
            projection="geoMercator"
            projectionConfig={{ scale: currentScale, center: currentCenter }}
            style={{ width: "100%", height: "100%" }}
          >
            <ZoomableGroup zoom={1}>
            <Geographies geography={currentGeoUrl}>
              {({ geographies }) =>
                geographies.map(geo => {
                  const rawName = isEbola 
                    ? geo.properties.shapeName 
                    : (geo.properties.name || geo.properties.CTP_KOR_NM || geo.properties.CTPRVN_NM);
                  const regionName = isEbola ? rawName : normalizeRegion(rawName);
                  const count = aggregatedData[regionName] || 0;
                  const detail = rawData[regionName] || {};
                  
                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      fill={count === 0 ? "#0f172a" : colorScale(count)}
                      stroke="#334155"
                      strokeWidth={1}
                      style={{
                        default: { outline: "none", transition: "all 250ms" },
                        hover: { fill: "#38bdf8", outline: "none", cursor: "pointer" },
                        pressed: { outline: "none" }
                      }}
                      onMouseEnter={(e) => {
                        setTooltipData({
                          region: rawName,
                          count: count,
                          deaths: detail.deaths || 0,
                          isEbola: isEbola,
                          x: e.clientX,
                          y: e.clientY
                        });
                      }}
                      onMouseMove={(e) => {
                        setTooltipData(prev => prev ? { ...prev, x: e.clientX, y: e.clientY } : null);
                      }}
                      onMouseLeave={() => {
                        setTooltipData(null);
                      }}
                    />
                  );
                })
              }
            </Geographies>

            {/* 마커 및 확산 라인(화살표) 렌더링 */}
            {sourceRegion && targetRegions.map(target => {
              const sourceCoord = REGION_COORDS[sourceRegion];
              const targetCoord = REGION_COORDS[target];
              return (
                <Line
                  key={`line-${target}`}
                  from={sourceCoord}
                  to={targetCoord}
                  stroke="#f43f5e"
                  strokeWidth={3}
                  strokeLinecap="round"
                  style={{
                    strokeDasharray: "6, 6",
                    animation: "dash 1s linear infinite"
                  }}
                />
              );
            })}

            {/* 각 확산 거점 마커 표시 */}
            {sourceRegion && (
              <Marker coordinates={REGION_COORDS[sourceRegion]}>
                <circle 
                  r={12} 
                  fill="rgba(244, 63, 94, 0.4)" 
                  style={{ animation: "pulse 2s infinite" }} 
                />
                <circle r={8} fill="#f43f5e" stroke="#fff" strokeWidth={2} />
                <text textAnchor="middle" y={20} style={{ fill: "#fff", fontSize: "12px", fontWeight: "bold" }}>
                  {sourceRegion} (진원지)
                </text>
              </Marker>
            )}
            
            {targetRegions.map(target => (
              <Marker key={`marker-${target}`} coordinates={REGION_COORDS[target]}>
                <circle r={5} fill="#fbbf24" stroke="#fff" strokeWidth={1.5} />
                <text textAnchor="middle" y={15} style={{ fill: "#cbd5e1", fontSize: "10px" }}>
                  {target}
                </text>
              </Marker>
            ))}

            </ZoomableGroup>
          </ComposableMap>
          </>
        )}
      </div>

      {/* Tooltip Render */}
      {tooltipData && (
        <div 
          className="mapTooltip"
          style={{ left: tooltipData.x, top: tooltipData.y }}
        >
          <div className="tooltipRegion">{tooltipData.region}</div>
          <div className="tooltipCount">
            {tooltipData.count === 0 ? (
              <span style={{ color: '#94a3b8' }}>감염자 없음</span>
            ) : (
              <>
                누적 확진자: <span>{tooltipData.count.toLocaleString()}명</span>
                {tooltipData.isEbola && (
                  <><br/>의심/사망: <span style={{color: '#ef4444'}}>{tooltipData.deaths.toLocaleString()}명</span></>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
