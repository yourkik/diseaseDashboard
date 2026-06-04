'use client';

import React, { useState } from 'react';
import InfectionMap from '@/components/InfectionMap';
import './mapStyles.css';

export default function MapTestPage() {
  const [selectedDisease, setSelectedDisease] = useState('수두');
  const diseases = ['수두', '백일해', '유행성이하선염', '코로나19', '에볼라바이러스병'];

  return (
    <div className="pageContainer">
      <div className="pageInner">
        <h1 className="pageTitle">
          KDCA 전파 지도 시각화 테스트
        </h1>
        
        <div className="diseaseButtons">
          {diseases.map(disease => (
            <button
              key={disease}
              onClick={() => setSelectedDisease(disease)}
              className={`diseaseBtn ${selectedDisease === disease ? 'active' : ''}`}
            >
              {disease}
            </button>
          ))}
        </div>

        <div style={{ marginTop: '2rem' }}>
          <InfectionMap diseaseName={selectedDisease} />
        </div>
      </div>
    </div>
  );
}
