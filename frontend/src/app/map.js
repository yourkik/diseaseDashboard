'use client';

import React, { useEffect, useRef } from 'react';

export default function KakaoMap() {
  const mapContainer = useRef(null);
  const mapInstance = useRef(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const initializeMap = () => {
      // 1. 카카오 API가 정상적으로 존재하고 로드되었는지 확인
      if (window.kakao && window.kakao.maps) {
        window.kakao.maps.load(() => {
          if (!mapContainer.current) return;

          const options = {
            center: new window.kakao.maps.LatLng(36.2683, 127.6358), // 대한민국 중심
            level: 12
          };

          // 2. 지도 인스턴스 생성 및 할당
          const map = new window.kakao.maps.Map(mapContainer.current, options);
          mapInstance.current = map;

          // 3. 브라우저 화면에 안착한 후 레이아웃 강제 재계산
          setTimeout(() => {
            if (mapInstance.current) {
              mapInstance.current.relayout();
              mapInstance.current.setCenter(new window.kakao.maps.LatLng(36.2683, 127.6358));
              console.log("카카오 지도 보정 완료");
            }
          }, 200);
        });
      }
    };

    // 스크립트가 이미 있으면 실행하고, 없으면 동적으로 주입
    if (window.kakao && window.kakao.maps) {
      initializeMap();
    } else {
      const script = document.createElement('script');
      script.src = '//dapi.kakao.com/v2/maps/sdk.js?appkey=a4d399374511870f64c998d3c98de9c0&libraries=services&autoload=false';
      script.async = true;
      script.onload = initializeMap;
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