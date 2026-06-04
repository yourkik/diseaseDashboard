'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { mockMapData } from './mockData';

export default function MapAzure({ disease = "코로나19" }) {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);
  const dataSourceRef = useRef(null);
  const router = useRouter();

  const [searchQuery, setSearchQuery] = useState('');

  const animationRef = useRef(null);
  const hoveredFeatureRef = useRef(null);

  // 기본 반경 연산 헬퍼 함수
  const getBaseRadius = (count) => {
    if (count <= 0) return 10;
    if (count >= 1000) return 40;
    return 10 + (count / 1000) * 30;
  };

  // [기능 무결성 확보 1] 프로프(disease) 및 검색어(searchQuery) 연동 데이터 필터링 파이프라인
  useEffect(() => {
    if (!dataSourceRef.current) return;

    const filteredData = mockMapData.filter(data => {
      // 대시보드 상단 선택 질병(prop)과 데이터의 질병명이 일치하는지 선제 검증
      const matchesDiseaseProp = data.diseaseName === disease;
      
      // 검색창 입력값에 따른 지역명 매칭 여부를 검증
      const matchesSearch = data.region.toLowerCase().includes(searchQuery.toLowerCase());
      
      return matchesDiseaseProp && matchesSearch;
    });

    dataSourceRef.current.clear();
    
    // 필터링된 데이터셋을 맵 버블 레이어에 재투입하며 동적 반경 연산 속성을 동기화
    filteredData.forEach((data) => {
      dataSourceRef.current.add(
        new window.atlas.data.Feature(
          new window.atlas.data.Point([data.lng, data.lat]), 
          {
            id: data.id,
            count: data.count,
            region: data.region,
            diseaseNm: data.diseaseName,
            currentRadius: getBaseRadius(data.count) 
          }
        )
      );
    });
  }, [searchQuery, disease]);

  // [기능 무결성 확보 2] Azure Maps 인프라 초기화 및 고성능 그래픽스 애니메이션 파이프라인
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initializeAzureMap = () => {
      if (window.atlas) {
        if (!mapContainer.current) return;

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
          console.log("Azure Maps 대시보드 렌더링에 성공했습니다.");
          
          const dataSource = new window.atlas.source.DataSource();
          map.sources.add(dataSource);
          dataSourceRef.current = dataSource;

          // 최초 렌더링 시 상단 선택 질병에 부합하는 데이터만 선별하여 적재
          const initialData = mockMapData.filter(data => data.diseaseName === disease);
          initialData.forEach((data) => {
            dataSource.add(
              new window.atlas.data.Feature(
                new window.atlas.data.Point([data.lng, data.lat]), 
                {
                  id: data.id,
                  count: data.count,
                  region: data.region,
                  diseaseNm: data.diseaseName,
                  currentRadius: getBaseRadius(data.count) 
                }
              )
            );
          });

          // 데이터 속성 'currentRadius'를 실시간 수신하는 버블 레이어 구축
          const bubbleLayer = new window.atlas.layer.BubbleLayer(dataSource, null, {
            radius: ['get', 'currentRadius'],
            color: [
              'step',
              ['get', 'count'],
              '#22c55e',  
              100, '#f97316', 
              500, '#ef4444'  
            ],
            strokeColor: 'white',
            strokeWidth: 2,
            opacity: 0.8
          });

          map.layers.add(bubbleLayer);

          const popup = new window.atlas.Popup({
            pixelOffset: [0, -12],
            closeButton: false
          });

          // 60fps 인터폴레이션 애니메이션 프레임 제어 엔진
          const animate = () => {
            if (!dataSourceRef.current) return;

            dataSource.getShapes().forEach(shape => {
              const props = shape.getProperties();
              const base = getBaseRadius(props.count);
              const target = (hoveredFeatureRef.current && hoveredFeatureRef.current.getId() === shape.getId()) ? base + 6 : base;

              if (Math.abs(props.currentRadius - target) > 0.01) {
                const nextRadius = props.currentRadius + (target - props.currentRadius) * 0.15;
                shape.setProperties({ ...props, currentRadius: nextRadius });
              }
            });

            animationRef.current = requestAnimationFrame(animate);
          };

          animationRef.current = requestAnimationFrame(animate);

          // 마우스 상호작용 인터페이스 및 예외 방어 로직
          map.events.add('mousemove', bubbleLayer, (e) => {
            if (e.shapes && e.shapes.length > 0) {
              map.getCanvasContainer().style.cursor = 'pointer';
              const shape = e.shapes[0];
              
              if (!hoveredFeatureRef.current || hoveredFeatureRef.current.getId() !== shape.getId()) {
                hoveredFeatureRef.current = shape;
                
                const properties = shape.getProperties();
                const coordinate = shape.getCoordinates();

                const popupContent = `
                  <div style="padding: 12px; font-family: sans-serif; min-width: 150px; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 8px;">
                    <h4 style="margin: 0 0 6px 0; color: #0f172a; font-size: 14px; font-weight: bold;">${properties.region} 지역</h4>
                    <div style="font-size: 12px; color: #475569; margin-bottom: 4px;">지정 감염병: <span style="color:#2563eb; font-weight:600;">${properties.diseaseNm}</span></div>
                    <div style="font-size: 13px; color: #dc2626; font-weight: bold;">확진자 집계: ${properties.count.toLocaleString()}명</div>
                  </div>
                `;

                popup.setOptions({ content: popupContent, position: coordinate });
                popup.open(map);
              }
            }
          });

          const clearHoverState = () => {
            map.getCanvasContainer().style.cursor = '';
            popup.close();
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
              const regionId = properties.id;

              if (regionId) {
                if (animationRef.current) cancelAnimationFrame(animationRef.current);
                popup.close();
                router.push(`/azure/details/${regionId}`);
              }
            }
          });

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
  }, [router, disease]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%', fontFamily: 'sans-serif' }}>
      <div style={{ alignSelf: 'flex-end', width: '300px' }}>
        <input 
          type="text"
          placeholder="조회할 지역명 입력..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px', outline: 'none', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}
        />
      </div>

      <div style={{ width: '100%', position: 'relative' }}>
        <div ref={mapContainer} style={{ width: '100%', height: '520px', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)', backgroundColor: '#f8fafc' }} />
      </div>
    </div>
  );
}