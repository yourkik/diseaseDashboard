'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ShieldAlert, AlertTriangle, FileText } from 'lucide-react';
import './mapStyles.css';

// 대한민국 17개 시도 대략적 중심 좌표
const REGION_COORDS = {
  "서울": [126.9780, 37.5665],
  "부산": [129.0756, 35.1796],
  "대구": [128.6014, 35.8714],
  "인천": [126.7052, 37.4563],
  "광주": [126.8526, 35.1595],
  "대전": [127.3845, 36.3504],
  "울산": [129.3114, 35.5384],
  "세종": [127.2890, 36.4800],
  "경기": [127.1678, 37.2752], // 경기는 중심 좌표 유지
  "강원": [128.1555, 37.8228],
  "충북": [127.4917, 36.6358],
  "충남": [126.6583, 36.5188],
  "전북": [127.1088, 35.7175],
  "전남": [126.9910, 34.8161],
  "경북": [128.8889, 36.4919],
  "경남": [128.2132, 35.2383],
  "제주": [126.5312, 33.4996]
};

// 경기도의 뉴스 뱃지가 서울과 겹치지 않게 하기 위한 보정 오프셋 (픽셀 기준)
const NEWS_OFFSET = {
  "경기": [20, -20],
  "서울": [-10, 0]
};

export default function OverallMap() {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const dataSourceRef = useRef(null);
  const newsSourceRef = useRef(null);
  const popupRef = useRef(null);

  const [aggregatedData, setAggregatedData] = useState({});
  const [regionStatusMap, setRegionStatusMap] = useState({});
  const [regionNewsCount, setRegionNewsCount] = useState({});
  const [nationalNews, setNationalNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    const fetchOverallData = async () => {
      setLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        
        const mapRes = await fetch(`${baseUrl}/api/stats/map/status?disease=전체`);
        if (!mapRes.ok) throw new Error("Backend server error");
        const mapData = await mapRes.json();
        
        const totals = {};
        Object.values(mapData).forEach(item => {
          let region = item.region.substring(0, 2); 
          totals[region] = item.count;
        });
        setAggregatedData(totals);

        const statusRes = await fetch(`${baseUrl}/api/ews/status`);
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          const sMap = {};
          if (Array.isArray(statusData)) {
            statusData.forEach(s => {
              if (s.name) sMap[s.name.substring(0,2)] = s.risk_level;
            });
          }
          setRegionStatusMap(sMap);
        }

        const normalizeRegion = (name) => {
          if (!name || name === "불명") return "전국";
          if (name.includes("경상남도")) return "경남";
          if (name.includes("경상북도")) return "경북";
          if (name.includes("전라남도")) return "전남";
          if (name.includes("전라북도") || name.includes("전북특별자치도")) return "전북";
          if (name.includes("충청남도")) return "충남";
          if (name.includes("충청북도")) return "충북";
          if (name.includes("제주")) return "제주";
          if (name.includes("세종")) return "세종";
          if (name.includes("강원")) return "강원";
          if (name.includes("도") && name.length === 1) return "전국"; // 잘못 파싱된 "도"
          return name.substring(0, 2);
        };

        const newsRes = await fetch(`${baseUrl}/api/ews/news?disease=전체&limit=100`);
        if (newsRes.ok) {
          const newsData = await newsRes.json();
          const nCount = {};
          const natNews = [];
          if (newsData.items) {
            newsData.items.forEach(item => {
              const r = normalizeRegion(item.wide_region);
              nCount[r] = (nCount[r] || 0) + 1;
              if (r === "전국") {
                natNews.push(item);
              }
            });
          }
          setRegionNewsCount(nCount);
          setNationalNews(natNews.slice(0, 5));
        }

      } catch (err) {
        console.error("Failed to fetch overall map data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchOverallData();
  }, []);

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return '#ef4444'; 
      case 'high': return '#f97316'; 
      case 'medium': return '#fbbf24'; 
      case 'low': return '#22c55e'; 
      default: return '#94a3b8';
    }
  };

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initializeAzureMap = () => {
      if (window.atlas && mapContainer.current && !mapInstance.current) {
        const map = new window.atlas.Map(mapContainer.current, {
          center: [127.6358, 36.2683],
          zoom: 6,
          style: 'light',
          view: 'Auto',
          authOptions: {
            authType: 'subscriptionKey',
            subscriptionKey: process.env.NEXT_PUBLIC_AZURE_MAPS_KEY 
          }
        });

        mapInstance.current = map;

        map.events.add('ready', () => {
          const dataSource = new window.atlas.source.DataSource();
          map.sources.add(dataSource);
          dataSourceRef.current = dataSource;

          // 뉴스를 위한 별도 데이터 소스
          const newsSource = new window.atlas.source.DataSource();
          map.sources.add(newsSource);
          newsSourceRef.current = newsSource;

          popupRef.current = new window.atlas.Popup({
            pixelOffset: [0, -12],
            closeButton: false
          });

          // Bubble Layer (종합 확진자 수 기준 보라/빨강 톤)
          const bubbleLayer = new window.atlas.layer.BubbleLayer(dataSource, null, {
            filter: ['==', ['geometry-type'], 'Point'],
            radius: ['get', 'radius'],
            color: [
              'step',
              ['get', 'count'],
              '#8b5cf6', // 보라색 (기본)
              500, '#d946ef', // 핑크보라
              2000, '#e11d48' // 빨강
            ],
            strokeColor: '#ffffff',
            strokeWidth: 2,
            opacity: 0.85
          });

          map.layers.add(bubbleLayer);

          // Symbol Layer (지역명)
          const symbolLayer = new window.atlas.layer.SymbolLayer(dataSource, null, {
            filter: ['==', ['geometry-type'], 'Point'],
            iconOptions: { image: 'none' },
            textOptions: {
              textField: ['get', 'label'],
              color: '#0f172a',
              size: 13,
              haloColor: 'rgba(255,255,255,0.8)',
              haloWidth: 2,
              offset: [0, 0]
            }
          });

          map.layers.add(symbolLayer);

          // Tooltip Event
          map.events.add('mousemove', bubbleLayer, (e) => {
            if (e.shapes && e.shapes.length > 0) {
              map.getCanvasContainer().style.cursor = 'pointer';
              const shape = e.shapes[0];
              const properties = shape.getProperties();
              const coordinate = shape.getCoordinates();
              
              const popupContent = `
                <div style="padding: 12px; font-family: sans-serif; min-width: 180px; background: white; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15); border: 1px solid #e2e8f0; border-radius: 8px;">
                  <h4 style="margin: 0 0 8px 0; color: #0f172a; font-size: 15px; font-weight: bold; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px;">${properties.region}</h4>
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: #64748b; font-size: 13px;">누적 확진</span>
                    <span style="color: #a855f7; font-weight: bold;">${properties.count.toLocaleString()}명</span>
                  </div>
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: #64748b; font-size: 13px;">위험도</span>
                    <span style="color: ${getRiskColor(properties.riskLevel)}; font-weight: bold;">${properties.riskLevel}</span>
                  </div>
                  <div style="display: flex; justify-content: space-between;">
                    <span style="color: #64748b; font-size: 13px;">징후/뉴스</span>
                    <span style="color: #0f172a; font-weight: bold;">${properties.newsCount}건</span>
                  </div>
                </div>
              `;

              popupRef.current.setOptions({ content: popupContent, position: coordinate });
              popupRef.current.open(map);
            }
          });

          map.events.add('mouseleave', bubbleLayer, () => {
            map.getCanvasContainer().style.cursor = '';
            popupRef.current.close();
          });

          setMapReady(true);
        });
      }
    };

    if (window.atlas) {
      initializeAzureMap();
    } else {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://atlas.microsoft.com/sdk/javascript/mapcontrol/3/atlas.min.css';
      link.type = 'text/css';
      document.head.appendChild(link);

      const script = document.createElement('script');
      script.src = 'https://atlas.microsoft.com/sdk/javascript/mapcontrol/3/atlas.min.js';
      script.async = true;
      script.onload = initializeAzureMap;
      document.head.appendChild(script);
    }
  }, []);

  useEffect(() => {
    if (!mapReady || !dataSourceRef.current || !newsSourceRef.current) return;

    dataSourceRef.current.clear();
    newsSourceRef.current.clear();
    
    const features = [];

    const getRadius = (count) => {
      if (count === 0) return 0;
      if (count < 100) return 12 + (count / 100) * 5;
      if (count < 1000) return 17 + ((count - 100) / 900) * 10;
      return 27 + Math.min(count - 1000, 5000) / 5000 * 15; 
    };

    // 마커 배열 (뉴스 뱃지)
    const htmlMarkers = [];

    // 모든 지역을 순회하며 데이터나 뉴스가 있는지 확인 (확진자가 0명이어도 뉴스가 있으면 핀 표시)
    Object.keys(REGION_COORDS).forEach(region => {
      const coord = REGION_COORDS[region];
      const count = aggregatedData[region] || 0;
      const newsCount = regionNewsCount[region] || 0;
      const riskLevel = regionStatusMap[region] || "Low";

      if (coord) {
        // 확진자가 있는 경우 버블 데이터 추가
        if (count > 0) {
          features.push(new window.atlas.data.Feature(
            new window.atlas.data.Point(coord),
            {
              region: region,
              count: count,
              riskLevel: riskLevel,
              newsCount: newsCount,
              radius: getRadius(count),
              label: `${region}\n${count.toLocaleString()}명`
            }
          ));
        }

        // 뉴스 개수가 있으면 확진자 여부와 관계없이 핀(Pin) 모양의 HTML 마커를 띄움
        if (newsCount > 0 && mapInstance.current) {
          const offset = NEWS_OFFSET[region] || [15, -15];
          
          // 핀 모양 컨테이너 (문자열 템플릿 방식)
          const markerHtml = `
            <div style="
              display: flex;
              justify-content: center;
              align-items: center;
              width: 32px;
              height: 32px;
              background-color: #9333ea;
              color: white;
              border-radius: 50% 50% 50% 0;
              transform: rotate(-45deg);
              box-shadow: -2px 2px 8px rgba(0,0,0,0.5);
              border: 2px solid white;
              cursor: pointer;
            ">
              <span style="
                transform: rotate(45deg);
                font-weight: 800;
                font-size: 13px;
                text-shadow: 0 1px 2px rgba(0,0,0,0.3);
              ">${newsCount}</span>
            </div>
          `;

          const marker = new window.atlas.HtmlMarker({
            position: coord,
            htmlContent: markerHtml,
            anchor: 'bottom', // 핀의 뾰족한 끝 부분이 좌표를 가리키도록 설정
            pixelOffset: offset
          });
          
          // 핀 클릭 시 해당 지역 선택 이벤트 발생
          mapInstance.current.events.add('click', marker, () => {
            if (window.handleRegionSelect) {
              window.handleRegionSelect(region);
            }
          });
          
          htmlMarkers.push(marker);
        }
      }
    });

    dataSourceRef.current.add(features);

    if (mapInstance.current) {
      mapInstance.current.markers.clear();
      mapInstance.current.markers.add(htmlMarkers);
    }

  }, [aggregatedData, regionNewsCount, regionStatusMap, mapReady]);

  return (
    <div className="mapContainer">
      <div className="mapHeader">
        <div>
          <h2 className="mapTitle" style={{ fontSize: '1.6rem', color: '#0f172a' }}>
            전국 감염병 통합 위험도 지도 (Azure Maps)
          </h2>
          <p className="mapSubtitle" style={{ color: '#475569', fontSize: '1rem', marginTop: '6px' }}>모든 감염병(코로나19, 수두 등)을 합산한 지역별 종합 누적 확진 현황</p>
        </div>
        <div className="periodBadge" style={{ backgroundColor: '#f3e8ff', border: '1px solid #d8b4fe', color: '#7e22ce' }}>
          <ShieldAlert size={20} />
          <span>전체 질병 종합 데이터</span>
        </div>
      </div>

      <div className="mapViewArea" style={{ padding: 0, overflow: 'hidden', height: '700px', position: 'relative' }}>
        {loading && (
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10, background: 'rgba(255,255,255,0.7)' }}>
            <div style={{ color: '#a855f7', fontWeight: 'bold', fontSize: '1.1rem' }}>통합 데이터를 불러오는 중입니다...</div>
          </div>
        )}
        <div ref={mapContainer} style={{ width: '100%', height: '100%', borderRadius: '12px' }} />

        {/* 전국 공통 데이터 플로팅 패널 (Light Mode 디자인) */}
        {!loading && (
          <div style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            width: '360px',
            maxHeight: '660px',
            overflowY: 'auto',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(16px)',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '24px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
            color: '#1e293b',
            zIndex: 10,
            animation: 'fadeInRight 0.5s ease-out forwards'
          }}>
            <h3 style={{ margin: '0 0 20px 0', fontSize: '1.3rem', color: '#7e22ce', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldAlert size={22} /> 전국 공통 현황
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#475569', fontSize: '1rem', fontWeight: '600' }}>전국 합산 확진</span>
                <span style={{ color: '#0f172a', fontWeight: 'bold', fontSize: '1.3rem' }}>
                  {(aggregatedData["전국"] || 0).toLocaleString()}명
                </span>
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#475569', fontSize: '1rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <AlertTriangle size={18} /> 국가 종합 위험도
                </span>
                <span style={{ 
                  color: getRiskColor(regionStatusMap["전국"] || "Low"), 
                  fontWeight: 'bold',
                  backgroundColor: `${getRiskColor(regionStatusMap["전국"] || "Low")}15`,
                  border: `1px solid ${getRiskColor(regionStatusMap["전국"] || "Low")}30`,
                  padding: '6px 14px',
                  borderRadius: '20px',
                  fontSize: '1rem'
                }}>{regionStatusMap["전국"] || "Low"}</span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: '#475569', fontSize: '1rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <FileText size={18} /> 전국 대상 뉴스
                </span>
                <span style={{ color: '#a855f7', fontWeight: 'bold', fontSize: '1.4rem' }}>
                  {regionNewsCount["전국"] || 0}건
                </span>
              </div>
            </div>

            {/* 전국 뉴스 리스트 및 관련 질병 정보 */}
            {nationalNews.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '24px' }}>
                <h4 style={{ margin: '0 0 8px 0', fontSize: '1.05rem', color: '#7e22ce', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <AlertTriangle size={16} color="#f59e0b" /> 전국 주요 위험 감염병 징후
                </h4>
                {nationalNews.map((n, idx) => (
                  <a key={idx} href={n.link || '#'} target="_blank" rel="noreferrer" style={{
                    textDecoration: 'none',
                    display: 'block',
                    backgroundColor: '#ffffff',
                    padding: '16px',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    borderLeft: '4px solid #a855f7',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => { 
                    e.currentTarget.style.backgroundColor = '#f8fafc'; 
                    e.currentTarget.style.boxShadow = '0 4px 10px rgba(0,0,0,0.05)';
                  }}
                  onMouseLeave={(e) => { 
                    e.currentTarget.style.backgroundColor = '#ffffff'; 
                    e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.02)';
                  }}
                  >
                    <div style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '8px', fontWeight: '500' }}>
                      {n.disease && <span style={{ color: '#d97706', fontWeight: 'bold', marginRight: '6px' }}>[{n.disease}]</span>}
                      {n.published_at ? n.published_at.substring(0, 10) : ''}
                    </div>
                    <div style={{ color: '#1e293b', fontSize: '1rem', lineHeight: '1.5', fontWeight: '600' }}>
                      {n.title}
                    </div>
                  </a>
                ))}
              </div>
            )}
            
            <div style={{ marginTop: '24px', padding: '16px', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <p style={{ margin: 0, fontSize: '0.9rem', color: '#475569', lineHeight: '1.6' }}>
                지도 위에 꽂혀 있는 <strong>보라색 핀(Pin) 안의 숫자</strong>는 해당 지역을 구체적으로 지목한 실시간 징후(뉴스 등)의 건수를 의미합니다.<br/><br/>
                특정 지역에 국한되지 않고 <strong>대한민국 전체</strong>를 아우르는 포괄적인 감염병 현황 및 뉴스는 이 패널에 따로 합산되어 표시됩니다.
              </p>
            </div>
          </div>
        )}
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes fadeInRight {
            from { transform: translateX(20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
          }
        `}} />
      </div>
    </div>
  );
}
