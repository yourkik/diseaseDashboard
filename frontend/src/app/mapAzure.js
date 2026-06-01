'use client';

import React, { useEffect, useRef } from 'react';

export default function MapAzure() {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initializeAzureMap = () => {
      // 1. Azure Maps SDK(atlas)가 정상적으로 로드되었는지 확인
      if (window.atlas) {
        if (!mapContainer.current) return;

        // 2. 지도 인스턴스 생성
        const map = new window.atlas.Map(mapContainer.current, {
          center: [127.6358, 36.2683], // [경도, 위도] 순서 (카카오와 반대이므로 주의)
          zoom: 6, // Azure Maps 고유 축적 레벨 (전국이 보이는 레벨)
          view: 'Auto',
          authOptions: {
            authType: 'subscriptionKey',
            subscriptionKey: '44n60knzXdRYTfDitjX4a7my8ijv28PhSd40eVhceOXvcvAqm8dqJQQJ99CFACYeBjFUZlQXAAAgAZMPQ9Cw' 
          }
        });

        mapInstance.current = map;

        // 3. 지도 로드가 완료되면 레이아웃 보정 및 콘솔 확인
        map.events.add('ready', () => {
          console.log("Azure Maps 대시보드 렌더링에 성공했습니다.");
          // 브라우저 크기 계산 타이밍 미스 방어용 리사이즈 강제 호출
          setTimeout(() => {
            map.resize();
          }, 200);
        });
      }
    };

    // 4. SDK 스타일시트 및 스크립트 동적 동기화 주입
    if (window.atlas) {
      initializeAzureMap();
    } else {
      // CSS 스타일시트 주입
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://atlas.microsoft.com/sdk/javascript/mapcontrol/3/atlas.min.css';
      link.type = 'text/css';
      document.head.appendChild(link);

      // JS 스크립트 주입
      const script = document.createElement('script');
      script.src = 'https://atlas.microsoft.com/sdk/javascript/mapcontrol/3/atlas.min.js';
      script.async = true;
      script.onload = initializeAzureMap;
      document.head.appendChild(script);
    }
  }, []);

  return (
    <div style={{ width: '100%' }}>
      <div 
        ref={mapContainer} 
        style={{ 
          width: '100%', 
          height: '450px', 
          borderRadius: '12px',
          backgroundColor: '#f8fafc'
        }}
      />
    </div>
  );
}