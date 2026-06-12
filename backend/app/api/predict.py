import os
import pandas as pd
import xgboost as xgb
import joblib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# 모델 및 인코더 로드 경로 세팅
MODEL_DIR = "backend/app/models"
model = xgb.XGBRegressor()
model.load_model(os.path.join(MODEL_DIR, "integrated_disease_xgboost.json"))

le_region = joblib.load(os.path.join(MODEL_DIR, "le_region.joblib"))
le_disease = joblib.load(os.path.join(MODEL_DIR, "le_disease.joblib"))

class SearchRequest(BaseModel):
    disease: str  # 예: '백일해'
    year: int     # 예: 2026
    week: int     # 예: 25
    region: str = None  # 예: '충남 계룡시' (검색 기능용, 선택 사항)

# 트랙 1: 지역 검색 API
@router.post("/predict/region")
def predict_by_region(req: SearchRequest):
    if req.disease not in le_disease.classes_:
        raise HTTPException(status_code=400, detail="지원하지 않는 질병명입니다.")
    if req.region not in le_region.classes_:
        raise HTTPException(status_code=400, detail="존재하지 않는 지역명입니다.")
        
    # 인코딩 변환
    disease_enc = le_disease.transform([req.disease])[0]
    region_enc = le_region.transform([req.region])[0]
    
    # 모델 입력용 데이터프레임 매트릭스 구성
    input_df = pd.DataFrame([{
        '연도': req.year,
        '주차': req.week,
        '지역_encoded': region_enc,
        '질병명_encoded': disease_enc
    }])
    
    # 예측 수행 후 음수 수치 예외 처리 무결성 확보
    pred = model.predict(input_df)[0]
    pred_val = max(0, int(round(pred)))
    
    return {"region": req.region, "disease": req.disease, "predicted_cases": pred_val}

# 트랙 2: 대시보드 하단 위험 지역 TOP 3 추출 API
@router.post("/predict/top-danger")
def get_top_danger_regions(req: SearchRequest):
    if req.disease not in le_disease.classes_:
        raise HTTPException(status_code=400, detail="지원하지 않는 질병명입니다.")
        
    disease_enc = le_disease.transform([req.disease])[0]
    
    records = []
    # 학습된 모든 지역 리스트를 순회하며 매트릭스 배치 연산 처리
    for region_name in le_region.classes_:
        # '전체'가 포함된 대분류 행은 랭킹 카드에서 제외하고 순수 시군구만 필터링
        if "전체" in region_name:
            continue
            
        region_enc = le_region.transform([region_name])[0]
        records.append({
            '연도': req.year,
            '주차': req.week,
            '지역_encoded': region_enc,
            '질병명_encoded': disease_enc,
            'region_name': region_name
        })
        
    test_df = pd.DataFrame(records)
    X = test_df[['연도', '주차', '지역_encoded', '질병명_encoded']]
    
    # 전체 지역 배치 예측
    preds = model.predict(X)
    test_df['predicted_cases'] = [max(0, int(round(p))) for p in preds]
    
    # 예측 환자 수 기준 내림차순 정렬 후 상위 3개 노출
    top_3 = test_df.sort_values(by='predicted_cases', ascending=False).head(3)
    
    result = []
    for _, row in top_3.iterrows():
        result.append({
            "region": row['region_name'],
            "predicted_cases": row['predicted_cases']
        })
        
    return {"disease": req.disease, "top_regions": result}