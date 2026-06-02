'use client';

import React, { useEffect, useRef, useState } from 'react';

export default function MapAzure({ disease = "코로나19" }) {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const dataSourceRef = useRef(null);
  const popupRef = useRef(null);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 지도 인스턴스 초기화
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initializeAzureMap = () => {
      if (window.atlas && mapContainer.current && !mapInstance.current) {
        const map = new window.atlas.Map(mapContainer.current, {
          center: [127.6358, 36.2683], // 한국 중심점
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
          
          // 데이터 소스 추가
          const dataSource = new window.atlas.source.DataSource();
          map.sources.add(dataSource);
          dataSourceRef.current = dataSource;

          // 팝업 추가
          popupRef.current = new window.atlas.Popup({
            pixelOffset: [0, -18],
            closeButton: false
          });

          // Line Layer (전파 방향)
          map.layers.add(new window.atlas.layer.LineLayer(dataSource, null, {
            strokeColor: '#3b82f6',
            strokeWidth: 3,
            filter: ['==', ['geometry-type'], 'LineString']
          }));

          // Bubble Layer (지역별 수치/위험도)
          const bubbleLayer = new window.atlas.layer.BubbleLayer(dataSource, null, {
            filter: ['==', ['geometry-type'], 'Point'],
            color: [
              'match',
              ['get', 'risk_level'],
              'High', '#ef4444',     // Red
              'Medium', '#f97316',   // Orange
              'Low', '#22c55e',      // Green
              '#6b7280'              // Gray (default)
            ],
            radius: [
              'step',
              ['get', 'cases'],
              10,    // cases가 없거나 0일때 기본 반경
              100, 15, // 100 이상이면 15
              1000, 20, // 1000 이상이면 20
              10000, 30 // 10000 이상이면 30
            ],
            strokeColor: 'white',
            strokeWidth: 2
          });
          map.layers.add(bubbleLayer);

          // 마우스 오버 팝업 이벤트
          map.events.add('mouseover', bubbleLayer, (e) => {
            if (e.shapes && e.shapes.length > 0) {
              const properties = e.shapes[0].getProperties();
              const coordinate = e.shapes[0].getCoordinates();
              
              const casesText = properties.cases ? `${properties.cases.toLocaleString()}명` : '수치 미제공(AI 추정)';
              
              popupRef.current.setOptions({
                position: coordinate,
                content: `<div style="padding:10px; font-family:sans-serif;">
                            <strong>${properties.name}</strong><br/>
                            확진자 수: ${casesText}<br/>
                            위험도: <b>${properties.risk_level}</b>
                          </div>`
              });
              popupRef.current.open(map);
            }
          });

          map.events.add('mouseleave', bubbleLayer, () => {
            popupRef.current.close();
          });

          // 초기 로드가 완료되면 데이터 패칭
          fetchDiseaseData(disease);
          
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
  }, []);

  // 질병 키워드가 바뀔 때마다 데이터 다시 불러오기
  useEffect(() => {
    if (mapInstance.current && dataSourceRef.current) {
      fetchDiseaseData(disease);
    }
  }, [disease]);

  const fetchDiseaseData = async (keyword) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/api/map/disease-spread?disease=${encodeURIComponent(keyword)}`);
      if (!response.ok) throw new Error('API 연동 실패');
      
      const result = await response.json();
      const mapData = result.data || [];
      
      if (dataSourceRef.current) {
        dataSourceRef.current.clear();
        
        // 데이터 파싱 및 Shape 추가
        const features = [];
        
        // 좌표 매핑용 딕셔너리 (Line 그릴 때 사용)
        const coordsMap = {};
        
        mapData.forEach(region => {
          if (region.coordinates && region.coordinates.length === 2) {
            coordsMap[region.name] = region.coordinates;
            
            // 점(Point) 데이터 추가
            features.push(new window.atlas.data.Feature(
              new window.atlas.data.Point(region.coordinates),
              {
                name: region.name,
                cases: region.cases || 0,
                risk_level: region.risk_level || 'Medium'
              }
            ));
          }
        });
        
        // 선(LineString) 데이터 추가 (spread_to 필드가 있는 경우)
        mapData.forEach(region => {
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
      }
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      {loading && (
        <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 10, background: 'white', padding: '5px 10px', borderRadius: '4px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          데이터 분석 중... (AI Agent 실행중)
        </div>
      )}
      {error && (
        <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 10, background: '#fee2e2', color: '#ef4444', padding: '5px 10px', borderRadius: '4px' }}>
          오류: {error}
        </div>
      )}
      <div 
        ref={mapContainer} 
        style={{ 
          width: '100%', 
          height: '600px', 
          borderRadius: '12px',
          backgroundColor: '#f8fafc'
        }}
      />
    </div>
  );
}