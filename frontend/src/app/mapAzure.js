'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function MapAzure({ disease = "코로나19", forceUpdateToggle = 0 }) {
  const router = useRouter();
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const dataSourceRef = useRef(null);
  const popupRef = useRef(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // 백엔드에서 받아온 원본 데이터 상태
  const [fetchedMapData, setFetchedMapData] = useState([]);

  const animationRef = useRef(null);
  const hoveredFeatureRef = useRef(null);

  // 기본 반경 연산 헬퍼 함수
  const getBaseRadius = (count) => {
    if (count <= 0) return 10;
    if (count >= 1000) return 40;
    return 10 + (count / 1000) * 30;
  };

  // 1. Azure Maps 초기화
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initializeAzureMap = () => {
      if (window.atlas && mapContainer.current && !mapInstance.current) {
        const map = new window.atlas.Map(mapContainer.current, {
          center: [127.6358, 36.2683],
          zoom: 6,
          view: 'Auto',
          authOptions: {
            authType: 'subscriptionKey',
            subscriptionKey: '44n60knzXdRYTfDitjX4a7my8ijv28PhSd40eVhceOXvcvAqm8dqJQQJ99CFACYeBjFUZlQXAAAgAZMPQ9Cw' 
          }
        });

        mapInstance.current = map;

        map.events.add('ready', () => {
          console.log("Azure Maps Ready.");
          
          const dataSource = new window.atlas.source.DataSource();
          map.sources.add(dataSource);
          dataSourceRef.current = dataSource;

          popupRef.current = new window.atlas.Popup({
            pixelOffset: [0, -12],
            closeButton: false
          });

          // Line Layer (전파 방향)
          map.layers.add(new window.atlas.layer.LineLayer(dataSource, null, {
            strokeColor: '#3b82f6',
            strokeWidth: 3,
            filter: ['==', ['geometry-type'], 'LineString']
          }));

          // Bubble Layer (지역별 수치/위험도, 애니메이션 연동)
          const bubbleLayer = new window.atlas.layer.BubbleLayer(dataSource, null, {
            filter: ['==', ['geometry-type'], 'Point'],
            radius: ['get', 'currentRadius'],
            color: [
              'match',
              ['get', 'risk_level'],
              'High', '#ef4444',
              'Medium', '#f97316',
              'Low', '#22c55e',
              '#6b7280'
            ],
            strokeColor: 'white',
            strokeWidth: 2,
            opacity: 0.8
          });

          map.layers.add(bubbleLayer);

          // 60fps 인터폴레이션 애니메이션 엔진
          const animate = () => {
            if (!dataSourceRef.current) return;

            dataSource.getShapes().forEach(shape => {
              if (shape.getType() === 'Point') {
                const props = shape.getProperties();
                const base = getBaseRadius(props.count);
                const target = (hoveredFeatureRef.current && hoveredFeatureRef.current.getId() === shape.getId()) ? base + 6 : base;

                if (Math.abs(props.currentRadius - target) > 0.01) {
                  const nextRadius = props.currentRadius + (target - props.currentRadius) * 0.15;
                  shape.setProperties({ ...props, currentRadius: nextRadius });
                }
              }
            });

            animationRef.current = requestAnimationFrame(animate);
          };

          animationRef.current = requestAnimationFrame(animate);

          // 마우스 상호작용
          map.events.add('mousemove', bubbleLayer, (e) => {
            if (e.shapes && e.shapes.length > 0) {
              map.getCanvasContainer().style.cursor = 'pointer';
              const shape = e.shapes[0];
              
              if (!hoveredFeatureRef.current || hoveredFeatureRef.current.getId() !== shape.getId()) {
                hoveredFeatureRef.current = shape;
                
                const properties = shape.getProperties();
                const coordinate = shape.getCoordinates();
                
                const casesText = properties.count > 0 ? `${properties.count.toLocaleString()}명` : '수치 미제공(AI 추정)';

                const popupContent = `
                  <div style="padding: 12px; font-family: sans-serif; min-width: 150px; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 8px;">
                    <h4 style="margin: 0 0 6px 0; color: #0f172a; font-size: 14px; font-weight: bold;">${properties.region} 지역</h4>
                    <div style="font-size: 12px; color: #475569; margin-bottom: 4px;">지정 감염병: <span style="color:#2563eb; font-weight:600;">${disease}</span></div>
                    <div style="font-size: 13px; color: #dc2626; font-weight: bold; margin-bottom: 4px;">확진자 집계: ${casesText}</div>
                    <div style="font-size: 12px; color: #64748b;">위험도: <b>${properties.risk_level}</b></div>
                  </div>
                `;

                popupRef.current.setOptions({ content: popupContent, position: coordinate });
                popupRef.current.open(map);
              }
            }
          });

          const clearHoverState = () => {
            map.getCanvasContainer().style.cursor = '';
            popupRef.current.close();
            hoveredFeatureRef.current = null;
          };

          map.events.add('mouseleave', bubbleLayer, clearHoverState);
          map.events.add('mousemove', (e) => {
            const features = map.layers.getRenderedShapes(e.position, [bubbleLayer]);
            if (features.length === 0) {
              clearHoverState();
            }
          });

          map.events.add('click', bubbleLayer, (e) => {
            if (e.shapes && e.shapes.length > 0) {
              const properties = e.shapes[0].getProperties();
              // 간단한 라우팅 예시 (이전 작업자의 로직 유지)
              if (animationRef.current) cancelAnimationFrame(animationRef.current);
              popupRef.current.close();
              router.push(`/azure/details/${properties.region}`);
            }
          });

          fetchDiseaseData(disease, forceUpdateToggle > 0);
          setTimeout(() => { map.resize(); }, 200);
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
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [router]);

  // 2. 질병 변경 및 강제 갱신 요청 시 데이터 패칭
  useEffect(() => {
    if (mapInstance.current && dataSourceRef.current) {
      fetchDiseaseData(disease, forceUpdateToggle > 0);
    }
  }, [disease, forceUpdateToggle]);

  const fetchDiseaseData = async (keyword, isForceUpdate) => {
    setLoading(true);
    setError(null);
    try {
      const isForceQuery = isForceUpdate ? 'true' : 'false';
      const response = await fetch(`http://localhost:8000/api/map/disease-spread?disease=${encodeURIComponent(keyword)}&force_update=${isForceQuery}`);
      if (!response.ok) throw new Error('API 연동 실패');
      
      const result = await response.json();
      if (result.last_updated) setLastUpdated(result.last_updated);
      
      setFetchedMapData(result.data || []);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. 데이터나 검색어가 바뀔 때마다 필터링 후 맵에 렌더링
  useEffect(() => {
    if (!dataSourceRef.current) return;

    const filteredData = fetchedMapData.filter(data => {
      if (!searchQuery) return true;
      return data.name && data.name.toLowerCase().includes(searchQuery.toLowerCase());
    });

    dataSourceRef.current.clear();
    
    const features = [];
    const coordsMap = {};
    
    // 점(Point) 데이터 세팅
    filteredData.forEach(region => {
      if (region.coordinates && region.coordinates.length === 2) {
        coordsMap[region.name] = region.coordinates;
        
        const count = region.cases || 0;
        features.push(new window.atlas.data.Feature(
          new window.atlas.data.Point(region.coordinates),
          {
            region: region.name,
            count: count,
            risk_level: region.risk_level || 'Medium',
            currentRadius: getBaseRadius(count) // 애니메이션용 속성 초기화
          }
        ));
      }
    });
    
    // 선(LineString) 데이터 세팅
    filteredData.forEach(region => {
      if (region.spread_to && Array.isArray(region.spread_to) && coordsMap[region.name]) {
        region.spread_to.forEach(targetName => {
          if (coordsMap[targetName]) {
            features.push(new window.atlas.data.Feature(
              new window.atlas.data.LineString([
                coordsMap[region.name],
                coordsMap[targetName]
              ])
            ));
          }
        });
      }
    });

    dataSourceRef.current.add(features);
  }, [fetchedMapData, searchQuery]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
          {lastUpdated ? `마지막 데이터 업데이트: ${new Date(lastUpdated).toLocaleString()}` : ''}
        </div>
        <div style={{ width: '300px' }}>
          <input 
            type="text"
            placeholder="조회할 지역명 입력..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}
          />
        </div>
      </div>

      <div style={{ width: '100%', position: 'relative' }}>
        {loading && (
          <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 10, background: 'rgba(255,255,255,0.9)', padding: '8px 12px', borderRadius: '4px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            데이터 분석 중... (AI Agent 증분검색 실행중)
          </div>
        )}
        {error && (
          <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 10, background: '#fee2e2', color: '#ef4444', padding: '8px 12px', borderRadius: '4px' }}>
            오류: {error}
          </div>
        )}
        <div ref={mapContainer} style={{ width: '100%', height: '520px', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)', backgroundColor: '#f8fafc' }} />
      </div>
    </div>
  );
}