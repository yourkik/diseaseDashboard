'use client';

import React, { useState, useEffect, useRef } from 'react';
import { AlertTriangle } from 'lucide-react';
import './mapStyles.css';

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
  "제주": [126.5312, 33.4996],
  "Kinshasa": [15.2663, -4.4419],
  "Equateur": [18.2603, 0.0487],
  "Nord-Kivu": [29.3246, -0.6764]
};

export default function InfectionMap({ diseaseName }) {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const dataSourceRef = useRef(null);
  const popupRef = useRef(null);

  const [aggregatedData, setAggregatedData] = useState({});
  const [rawData, setRawData] = useState({});
  const [loading, setLoading] = useState(true);
  const [mapReady, setMapReady] = useState(false);
  const [availableYears, setAvailableYears] = useState(['전체']);
  const [selectedYear, setSelectedYear] = useState('전체');

  const isEbola = diseaseName === '에볼라';
  const currentCenter = isEbola ? [23.5, -2.5] : [127.6358, 36.2683];
  const currentZoom = isEbola ? 4 : 6;

  useEffect(() => {
    const fetchYears = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${baseUrl}/api/stats/map/years?disease=${diseaseName}`);
        if (res.ok) {
          const years = await res.json();
          setAvailableYears([...years, '전체']);
          if (years.length > 0) {
            setSelectedYear(years[0]);
          }
        }
      } catch (err) {
        console.error("Failed to fetch years", err);
      }
    };
    if (diseaseName) fetchYears();
  }, [diseaseName]);

  useEffect(() => {
    const fetchSpreadData = async () => {
      setLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const yearParam = selectedYear === '전체' ? '' : selectedYear;
        const res = await fetch(`${baseUrl}/api/stats/map/status?disease=${encodeURIComponent(diseaseName)}&year=${yearParam}`);
        if (!res.ok) throw new Error("Backend server error");
        
        const data = await res.json();
        
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
  }, [diseaseName, selectedYear]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initializeAzureMap = () => {
      if (window.atlas && mapContainer.current && !mapInstance.current) {
        const map = new window.atlas.Map(mapContainer.current, {
          center: currentCenter,
          zoom: currentZoom,
          style: 'light', // 라이트 테마에 맞춘 밝은 스타일
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

          popupRef.current = new window.atlas.Popup({
            pixelOffset: [0, -12],
            closeButton: false
          });

          // Line Layer (확산 방향 대시선)
          map.layers.add(new window.atlas.layer.LineLayer(dataSource, null, {
            strokeColor: '#f43f5e',
            strokeWidth: 3,
            strokeDashArray: [2, 2],
            filter: ['==', ['geometry-type'], 'LineString']
          }));

          // Bubble Layer (확진자 규모)
          const bubbleLayer = new window.atlas.layer.BubbleLayer(dataSource, null, {
            filter: ['==', ['geometry-type'], 'Point'],
            radius: ['get', 'radius'],
            color: [
              'step',
              ['get', 'count'],
              '#3b82f6', // 기본 파랑
              50, '#f59e0b', // 50이상 노랑
              200, '#ef4444' // 200이상 빨강
            ],
            strokeColor: '#ffffff',
            strokeWidth: 2,
            opacity: 0.8
          });

          map.layers.add(bubbleLayer);

          // Symbol Layer (지역명)
          const symbolLayer = new window.atlas.layer.SymbolLayer(dataSource, null, {
            filter: ['==', ['geometry-type'], 'Point'],
            iconOptions: { image: 'none' },
            textOptions: {
              textField: ['get', 'label'],
              color: '#1e293b', // 라이트 모드 가독성을 위해 어두운 텍스트
              size: 13,
              haloColor: 'rgba(255,255,255,0.8)',
              haloWidth: 2,
              offset: [0, 0]
            }
          });

          map.layers.add(symbolLayer);

          // Tooltip 이벤트
          map.events.add('mousemove', bubbleLayer, (e) => {
            if (e.shapes && e.shapes.length > 0) {
              map.getCanvasContainer().style.cursor = 'pointer';
              const shape = e.shapes[0];
              const properties = shape.getProperties();
              const coordinate = shape.getCoordinates();
              
              const popupContent = `
                <div style="padding: 12px; font-family: sans-serif; min-width: 140px; background: white; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15); border: 1px solid #e2e8f0; border-radius: 8px;">
                  <h4 style="margin: 0 0 6px 0; color: #0f172a; font-size: 15px; font-weight: bold; border-bottom: 1px solid #f1f5f9; padding-bottom: 6px;">${properties.region}</h4>
                  <div style="font-size: 14px; color: #475569;">누적 확진자: <span style="color: #2563eb; font-weight: bold;">${properties.count.toLocaleString()}명</span></div>
                  ${properties.deaths > 0 ? `<div style="font-size: 14px; color: #475569; margin-top: 4px;">의심/사망: <span style="color: #ef4444; font-weight: bold;">${properties.deaths.toLocaleString()}명</span></div>` : ''}
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
    if (!mapReady || !dataSourceRef.current || !window.atlas || Object.keys(aggregatedData).length === 0) return;

    dataSourceRef.current.clear();
    const features = [];

    const sortedRegions = Object.entries(aggregatedData)
      .filter(([name, count]) => REGION_COORDS[name] && count > 0)
      .sort((a, b) => b[1] - a[1]);

    const sourceRegion = sortedRegions.length > 0 ? sortedRegions[0][0] : null;
    const targetRegions = sortedRegions.slice(1, 4).map(item => item[0]);

    const getRadius = (count) => {
      if (count === 0) return 0;
      if (count < 50) return 10 + (count / 50) * 5;
      if (count < 200) return 15 + ((count - 50) / 150) * 10;
      return 25 + Math.min(count - 200, 1000) / 1000 * 15; 
    };

    Object.entries(aggregatedData).forEach(([region, count]) => {
      const coord = REGION_COORDS[region];
      const detail = rawData[region] || {};
      if (coord && count > 0) {
        features.push(new window.atlas.data.Feature(
          new window.atlas.data.Point(coord),
          {
            region: region,
            count: count,
            deaths: detail.deaths || 0,
            radius: getRadius(count),
            label: `${region}\n${count.toLocaleString()}명`
          }
        ));
      }
    });

    if (sourceRegion) {
      const sourceCoord = REGION_COORDS[sourceRegion];
      targetRegions.forEach(target => {
        const targetCoord = REGION_COORDS[target];
        if (targetCoord) {
          features.push(new window.atlas.data.Feature(
            new window.atlas.data.LineString([sourceCoord, targetCoord])
          ));
        }
      });
    }

    dataSourceRef.current.add(features);

    if (mapInstance.current) {
      mapInstance.current.setCamera({
        center: currentCenter,
        zoom: currentZoom
      });
    }

  }, [aggregatedData, mapReady, currentCenter, currentZoom]);

  let periodDisplay = "데이터 로드 중...";
  if (isEbola) {
    periodDisplay = `HDX 글로벌 데이터 (${new Date().getFullYear()}년)`;
  } else if (Object.keys(rawData).length > 0) {
    const firstItem = Object.values(rawData)[0];
    periodDisplay = firstItem.period || "최신 누적 데이터";
  }

  return (
    <div className="mapContainer">
      <div className="mapHeader">
        <div>
          <h2 className="mapTitle" style={{ fontSize: '1.6rem', color: '#0f172a' }}>
            {diseaseName} 정적 확산 지도 (Azure Maps)
          </h2>
          <p className="mapSubtitle" style={{ color: '#475569', fontSize: '1rem', marginTop: '6px' }}>연간 누적 감염 현황 및 주요 확산 경로 추정</p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
          <div className="periodBadge">
            <AlertTriangle color="#d97706" size={20} />
            <span>{periodDisplay}</span>
          </div>
        </div>
      </div>

      <div className="mapViewArea" style={{ padding: 0, overflow: 'hidden', height: '650px', position: 'relative' }}>
        {loading && (
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10, background: 'rgba(255,255,255,0.7)' }}>
            <div style={{ color: '#2563eb', fontWeight: 'bold', fontSize: '1.1rem' }}>데이터를 불러오는 중입니다...</div>
          </div>
        )}
        {Object.keys(aggregatedData).length > 0 && Object.values(aggregatedData).every(v => v === 0) && (
          <div style={{
            position: 'absolute', top: '20px', left: '50%', transform: 'translateX(-50%)',
            backgroundColor: '#fef2f2', color: '#dc2626', padding: '12px 24px',
            borderRadius: '8px', fontWeight: 'bold', zIndex: 10, boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            border: '1px solid #fecaca'
          }}>
            🚫 현재 데이터 기준 감염자 없음 (0명)
          </div>
        )}
        <div ref={mapContainer} style={{ width: '100%', height: '100%', borderRadius: '12px' }} />
      </div>
    </div>
  );
}
