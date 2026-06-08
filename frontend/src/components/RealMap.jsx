'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AlertTriangle } from 'lucide-react';

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
  
  // 에볼라 관련 아프리카 주요 도시 임시 좌표
  "Kinshasa": [15.2663, -4.4419],
  "Equateur": [18.2603, 0.0487],
  "Nord-Kivu": [29.3246, -0.6764]
};

export default function RealMap({ diseaseName }) {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const dataSourceRef = useRef(null);
  const animationDataSourceRef = useRef(null);
  const animationRef = useRef(null);
  const popupRef = useRef(null);

  const [aggregatedData, setAggregatedData] = useState({});
  const [loading, setLoading] = useState(true);
  const [mapReady, setMapReady] = useState(false);

  const isEbola = diseaseName === '에볼라';
  const currentCenter = isEbola ? [23.5, -2.5] : [127.6358, 36.2683];
  const currentZoom = isEbola ? 4 : 6;

  // 1. 데이터 패칭 로직
  useEffect(() => {
    const fetchSpreadData = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/stats/map/status?disease=${diseaseName}`);
        if (!res.ok) throw new Error("Backend server error");
        
        const data = await res.json();
        const totals = {};
        Object.values(data).forEach(item => {
          let region = isEbola ? item.region : item.region.substring(0, 2); 
          totals[region] = item.count;
        });
        
        setAggregatedData(totals);
      } catch (err) {
        console.error("Failed to fetch map data", err);
      } finally {
        setLoading(false);
      }
    };
    
    if (diseaseName) fetchSpreadData();
  }, [diseaseName]);

  // 2. Azure Maps 초기화
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initializeAzureMap = () => {
      if (window.atlas && mapContainer.current && !mapInstance.current) {
        const map = new window.atlas.Map(mapContainer.current, {
          center: currentCenter,
          zoom: currentZoom,
          view: 'Auto',
          authOptions: {
            authType: 'subscriptionKey',
            subscriptionKey: '44n60knzXdRYTfDitjX4a7my8ijv28PhSd40eVhceOXvcvAqm8dqJQQJ99CFACYeBjFUZlQXAAAgAZMPQ9Cw' 
          }
        });

        mapInstance.current = map;

        map.events.add('ready', () => {
          console.log("Azure Maps for RealMap Ready.");
          
          const dataSource = new window.atlas.source.DataSource();
          map.sources.add(dataSource);
          dataSourceRef.current = dataSource;

          popupRef.current = new window.atlas.Popup({
            pixelOffset: [0, -12],
            closeButton: false
          });

          // Line Layer (전파 방향 실선 - 가시성을 위해 보라색 사용)
          map.layers.add(new window.atlas.layer.LineLayer(dataSource, null, {
            strokeColor: '#8b5cf6', // 지도 및 버블 색상과 대비되는 선명한 보라색
            strokeWidth: 4,
            filter: ['==', ['geometry-type'], 'LineString']
          }));

          // 애니메이션 데이터 소스 및 레이어 (실선 위를 움직이는 점)
          const animationSource = new window.atlas.source.DataSource();
          map.sources.add(animationSource);
          animationDataSourceRef.current = animationSource;

          const movingDotLayer = new window.atlas.layer.BubbleLayer(animationSource, null, {
            radius: 5,
            color: '#ffffff',
            strokeColor: '#8b5cf6',
            strokeWidth: 2,
            opacity: 1
          });

          map.layers.add(movingDotLayer);

          // Bubble Layer (확진자 규모에 따른 색상 구분: 초록, 노랑, 빨강)
          const bubbleLayer = new window.atlas.layer.BubbleLayer(dataSource, null, {
            filter: ['==', ['geometry-type'], 'Point'],
            radius: ['get', 'radius'],
            color: [
              'step',
              ['get', 'count'],
              '#22c55e', // 초록색 (count < 100)
              100, '#eab308', // 노란색 (count >= 100)
              500, '#ef4444'  // 빨간색 (count >= 500)
            ],
            strokeColor: 'white',
            strokeWidth: 2,
            opacity: 0.8
          });

          map.layers.add(bubbleLayer);

          // Symbol Layer (지역명 및 감염자 수 상시 표기)
          const symbolLayer = new window.atlas.layer.SymbolLayer(dataSource, null, {
            filter: ['==', ['geometry-type'], 'Point'],
            iconOptions: {
              image: 'none' // 파란색 기본 핀 아이콘 제거
            },
            textOptions: {
              textField: ['get', 'label'],
              color: '#ffffff',
              size: 13,
              haloColor: 'rgba(0,0,0,0.6)',
              haloWidth: 1.5,
              offset: [0, 0]
            }
          });

          map.layers.add(symbolLayer);

          // 마우스 상호작용 (Tooltip)
          map.events.add('mousemove', bubbleLayer, (e) => {
            if (e.shapes && e.shapes.length > 0) {
              map.getCanvasContainer().style.cursor = 'pointer';
              const shape = e.shapes[0];
              const properties = shape.getProperties();
              const coordinate = shape.getCoordinates();
              
              const popupContent = `
                <div style="padding: 10px; font-family: sans-serif; min-width: 120px; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 8px;">
                  <h4 style="margin: 0 0 4px 0; color: #0f172a; font-size: 14px; font-weight: bold;">${properties.region}</h4>
                  <div style="font-size: 13px; color: #dc2626; font-weight: bold;">확진자: ${properties.count.toLocaleString()}명</div>
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

          setMapReady(true); // 맵 로딩이 완벽히 끝남을 알림
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
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []); // 지도 초기화는 한 번만

  // 3. 데이터가 변경되거나 맵이 준비되면 Azure Maps에 데이터 추가
  useEffect(() => {
    if (!mapReady || !dataSourceRef.current || !window.atlas || Object.keys(aggregatedData).length === 0) return;

    // 기존 데이터 초기화
    dataSourceRef.current.clear();
    const features = [];

    // 확진자가 가장 많은 1위 지역 탐색 (화살표용)
    const sortedRegions = Object.entries(aggregatedData)
      .filter(([name, count]) => REGION_COORDS[name] && count > 0)
      .sort((a, b) => b[1] - a[1]);

    const sourceRegion = sortedRegions.length > 0 ? sortedRegions[0][0] : null;
    const targetRegions = sortedRegions.slice(1, 4).map(item => item[0]);

    // 반경 연산 헬퍼 (절대적인 수치 기반으로 구간별 크기 조정)
    const getRadius = (count) => {
      if (count === 0) return 0;
      if (count < 100) {
        // 초록색 (최소 10, 최대 15로 고정)
        return 10 + (count / 100) * 5;
      } else if (count < 500) {
        // 노란색 (최소 15, 최대 25로 고정)
        return 15 + ((count - 100) / 400) * 10;
      } else {
        // 빨간색 (최소 25, 5000명 기준 최대 45로 고정)
        const extra = Math.min(count - 500, 5000) / 5000;
        return 25 + extra * 20; 
      }
    };

    // 버블 생성
    Object.entries(aggregatedData).forEach(([region, count]) => {
      const coord = REGION_COORDS[region];
      if (coord && count > 0) {
        features.push(new window.atlas.data.Feature(
          new window.atlas.data.Point(coord),
          {
            region: region,
            count: count,
            radius: getRadius(count),
            label: `${region}\n${count.toLocaleString()}명`
          }
        ));
      }
    });

    // 확산 방향 선 생성 및 애니메이션 패스 저장
    const paths = [];
    if (sourceRegion) {
      const sourceCoord = REGION_COORDS[sourceRegion];
      targetRegions.forEach(target => {
        const targetCoord = REGION_COORDS[target];
        if (targetCoord) {
          paths.push({ start: sourceCoord, end: targetCoord });
          features.push(new window.atlas.data.Feature(
            new window.atlas.data.LineString([sourceCoord, targetCoord])
          ));
        }
      });
    }

    dataSourceRef.current.add(features);
    
    // 이전 애니메이션 취소
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    // 새 애니메이션 시작 (방향성을 보여주기 위함)
    if (paths.length > 0 && animationDataSourceRef.current) {
      let progress = 0;
      const animate = () => {
        progress += 0.005; // 이동 속도
        if (progress > 1) progress = 0;

        const dotFeatures = paths.map(path => {
          const lon = path.start[0] + (path.end[0] - path.start[0]) * progress;
          const lat = path.start[1] + (path.end[1] - path.start[1]) * progress;
          return new window.atlas.data.Feature(new window.atlas.data.Point([lon, lat]));
        });

        animationDataSourceRef.current.clear();
        animationDataSourceRef.current.add(dotFeatures);
        
        animationRef.current = requestAnimationFrame(animate);
      };
      
      animate();
    } else if (animationDataSourceRef.current) {
      animationDataSourceRef.current.clear();
    }

    // 질병(에볼라 등)이 바뀔 때 지도 센터 이동
    if (mapInstance.current) {
      mapInstance.current.setCamera({
        center: currentCenter,
        zoom: currentZoom
      });
    }

  }, [aggregatedData, mapReady, currentCenter, currentZoom]);

  return (
    <div className="mapContainer" style={{ backgroundColor: '#ffffff', color: '#333' }}>
      <div className="mapHeader" style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem', marginBottom: '1rem' }}>
        <div>
          <h2 className="mapTitle" style={{ background: 'linear-gradient(to right, #ef4444, #f59e0b)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            {diseaseName} 동적 확산 지도 (Azure Maps)
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '10px', fontSize: '0.9rem', color: '#475569', fontWeight: '500' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ display: 'inline-block', width: '14px', height: '14px', borderRadius: '50%', backgroundColor: '#22c55e', marginRight: '6px', border: '1px solid rgba(0,0,0,0.1)' }}></span>
              <span>100명 미만 (안전)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ display: 'inline-block', width: '14px', height: '14px', borderRadius: '50%', backgroundColor: '#eab308', marginRight: '6px', border: '1px solid rgba(0,0,0,0.1)' }}></span>
              <span>100명 이상 (주의)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ display: 'inline-block', width: '14px', height: '14px', borderRadius: '50%', backgroundColor: '#ef4444', marginRight: '6px', border: '1px solid rgba(0,0,0,0.1)' }}></span>
              <span>500명 이상 (심각)</span>
            </div>
          </div>
        </div>
        <div className="periodBadge" style={{ backgroundColor: '#eff6ff', color: '#1e40af', border: '1px solid #bfdbfe' }}>
          <AlertTriangle size={20} />
          <span>Azure Maps 실시간 렌더링</span>
        </div>
      </div>

      <div className="mapViewArea" style={{ padding: 0, overflow: 'hidden', height: '650px', position: 'relative' }}>
        {loading && (
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10, background: 'rgba(255,255,255,0.7)' }}>
            <div style={{ color: '#3b82f6', fontWeight: 'bold' }}>데이터를 불러오는 중입니다...</div>
          </div>
        )}
        <div ref={mapContainer} style={{ width: '100%', height: '100%', borderRadius: '12px' }} />
      </div>
    </div>
  );
}
