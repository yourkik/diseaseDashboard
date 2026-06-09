"use client";

import React, { useState } from 'react';

export default function AdminPage() {
  const [debugMode, setDebugMode] = useState(false);

  return (
    <main className="container animate-fade-in">
      <header style={{ marginBottom: '40px' }}>
        <h1 className="title-gradient" style={{ fontSize: '2.5rem', marginBottom: '8px' }}>보건소 알림 설정 관리</h1>
        <p className="subtitle">AI 기반 대시보드의 실시간 알림 트리거 및 디버그 설정을 동적으로 구성합니다.</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
        <div className="glass-card">
          <h2 style={{ marginBottom: '20px', borderBottom: '1px solid var(--border-glow)', paddingBottom: '12px' }}>새 알림 조건 등록</h2>
          
          <form style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>대상 질병 키워드</label>
              <input type="text" placeholder="예: 독감, 코로나, 빈대" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-glow)', background: 'rgba(0,0,0,0.2)', color: 'white', outline: 'none' }} defaultValue="독감" />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>뉴스 언급량 급증 임계치 (일간)</label>
              <input type="number" placeholder="기사 수" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-glow)', background: 'rgba(0,0,0,0.2)', color: 'white', outline: 'none' }} defaultValue="50" />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>일일 확진자 초과 기준</label>
              <input type="number" placeholder="확진자 수" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-glow)', background: 'rgba(0,0,0,0.2)', color: 'white', outline: 'none' }} defaultValue="10000" />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>수신 대상 이메일 (보건소 담당자)</label>
              <input type="email" placeholder="admin@health.go.kr" style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-glow)', background: 'rgba(0,0,0,0.2)', color: 'white', outline: 'none' }} defaultValue="health_center_01@korea.kr" />
            </div>

            <button type="button" className="btn" style={{ marginTop: '10px' }}>조건 저장 및 알림 활성화</button>
          </form>
        </div>

        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h2 style={{ marginBottom: '20px', borderBottom: '1px solid var(--border-glow)', paddingBottom: '12px' }}>현재 활성화된 트리거</h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flexGrow: 1 }}>
            <div style={{ padding: '16px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-glow)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <strong style={{ fontSize: '1.1rem' }}>독감 유행 경보</strong>
                <span className="badge success">Active</span>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '12px' }}>조건: 뉴스 내 '독감' 키워드 50건 이상 또는 확진자 10,000명 초과</p>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button type="button" style={{ background: 'transparent', color: 'var(--accent)', border: 'none', cursor: 'pointer', fontWeight: '600' }}>수정</button>
                <button type="button" style={{ background: 'transparent', color: 'var(--danger)', border: 'none', cursor: 'pointer', fontWeight: '600' }}>삭제</button>
              </div>
            </div>

            <div style={{ padding: '16px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-glow)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <strong style={{ fontSize: '1.1rem' }}>해외 신종 바이러스 모니터링</strong>
                <span className="badge warning">Paused</span>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '12px' }}>조건: 해외 뉴스 내 'Outbreak' 키워드 20건 이상</p>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button type="button" style={{ background: 'transparent', color: 'var(--accent)', border: 'none', cursor: 'pointer', fontWeight: '600' }}>재개</button>
                <button type="button" style={{ background: 'transparent', color: 'var(--danger)', border: 'none', cursor: 'pointer', fontWeight: '600' }}>삭제</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="glass-card" style={{ marginTop: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.5rem', borderBottom: '1px solid var(--border-glow)', paddingBottom: '12px', flex: 1, margin: 0 }}>디버그 및 수동 제어</h2>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', fontSize: '1rem', fontWeight: '500' }}>
            <input 
              type="checkbox" 
              checked={debugMode} 
              onChange={(e) => setDebugMode(e.target.checked)} 
              style={{ marginRight: '8px', width: '18px', height: '18px' }}
            />
            디버그 모드 켜기
          </label>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '1rem', lineHeight: '1.6' }}>
          {debugMode ? (
            <>
              <p style={{ marginBottom: '16px' }}>캐시(Cache)를 무시하고 AI 에이전트 분석을 강제로 새로 수행합니다.</p>
              <button 
                onClick={() => {
                  alert('강제 업데이트 신호가 서버로 전송되었습니다.');
                }}
                style={{
                  backgroundColor: '#3b82f6', color: 'white', border: 'none', padding: '12px 24px',
                  borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '1rem'
                }}
              >
                🚀 AI 강제 업데이트 신호 전송
              </button>
            </>
          ) : (
            <p>디버그 모드를 켜면 AI 에이전트 강제 갱신(Force Update) 버튼이 활성화됩니다. 일반 모드에서는 빠른 캐시 데이터를 사용합니다.</p>
          )}
        </div>
      </div>
    </main>
  );
}
