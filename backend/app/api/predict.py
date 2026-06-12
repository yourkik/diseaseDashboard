import os
import pandas as pd
import xgboost as xgb
import joblib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# 1. 파일 절대 경로 기준 고정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # .../backend/app/api
BASE_DIR = os.path.dirname(CURRENT_DIR)                  # .../backend/app
MODEL_DIR = os.path.join(BASE_DIR, "models")             # .../backend/app/models

MODEL_PATH = os.path.join(MODEL_DIR, "integrated_disease_xgboost.json")
LE_DISEASE_PATH = os.path.join(MODEL_DIR, "le_disease.joblib")
LE_REGION_PATH = os.path.join(MODEL_DIR, "le_region.joblib")

# 2. 모델 및 라벨 인코더 전역 로드 (메모리 무결성 확보)
model = xgb.XGBRegressor()
le_disease = None
le_region = None

if os.path.exists(MODEL_PATH):
    model.load_model(MODEL_PATH)
else:
    print(f"❌ [경고] 예측 가중치 파일이 누락되었습니다: {MODEL_PATH}")

if os.path.exists(LE_DISEASE_PATH) and os.path.exists(LE_REGION_PATH):
    le_disease = joblib.load(LE_DISEASE_PATH)
    le_region = joblib.load(LE_REGION_PATH)
    print("✅ 라벨 인코더 파일(Disease, Region) 로드 성공")
else:
    print("❌ [경고] 라벨 인코더 joblib 파일 세트가 누락되었습니다.")

# 3. 요청 데이터 구조 정의
class SearchRequest(BaseModel):
    disease: str
    year: int
    week: int
    region: str = None


@router.post("/predict/top-danger")
def get_top_danger_regions(req: SearchRequest):
    if le_disease is None or le_region is None:
        raise HTTPException(status_code=500, detail="서버 인코더 미준비 상태")

    # 입력받은 질병이 인코더 클래스에 없는 경우 예외 처리
    if req.disease not in le_disease.classes_:
        return {"disease": req.disease, "top_regions": []}
        
    disease_enc = le_disease.transform([req.disease])[0]
    records = []
    
    # 인코더에 들어있는 실제 전국 시군구 클래스 리스트를 순회하며 매트릭스 구성
    for region_name in le_region.classes_:
        # 데이터 정제를 위해 '전체' 텍스트나 빈 데이터 필터링 (필요시 조건 조절)
        if "전체" in region_name:
            continue
            
        region_enc = le_region.transform([region_name])[0]
        records.append({
            '연도': int(req.year),
            '주차': int(req.week),
            '지역_encoded': region_enc,
            '질병명_encoded': disease_enc,
            'region_name': region_name
        })
        
    if not records:
        return {"disease": req.disease, "top_regions": []}
        
    test_df = pd.DataFrame(records)
    X = test_df[['연도', '주차', '지역_encoded', '질병명_encoded']]
    
    # 모델 추론 및 결과 바인딩
    preds = model.predict(X)
    test_df['predicted_cases'] = [max(0, int(round(p))) for p in preds]
    
    # 1. 전국 데이터 분리 추출 (국가 거시 지표용)
    national_row = test_df[test_df['region_name'].str.contains("전국", na=False)]
    national_cases = int(national_row['predicted_cases'].values[0]) if not national_row.empty else 0
    
    # 2. TOP 3 산출 시 '전체' 및 '전국' 키워드 원천 배제 필터링
    filtered_df = test_df[
        (~test_df['region_name'].str.contains("전국", na=False)) & 
        (~test_df['region_name'].str.contains("전체", na=False)) &
        (test_df['region_name'].str.strip() != "") &
        (~test_df['region_name'].isna())
    ]
    
    top_3 = filtered_df.sort_values(by='predicted_cases', ascending=False).head(3)
    
    result = []
    for _, row in top_3.iterrows():
        clean_region_name = str(row['region_name']).replace("nan ", "").replace("NaN ", "").strip()
        result.append({
            "region": clean_region_name,
            "predicted_cases": int(row['predicted_cases'])
        })
        
    return {
        "disease": req.disease, 
        "top_regions": result,
        "national_cases": national_cases  # 전국 수치 별도 바인딩
    }


@router.post("/predict/region")
def get_single_region_prediction(req: SearchRequest):
    if le_disease is None or le_region is None:
        raise HTTPException(status_code=500, detail="서버 인코더 미준비 상태")
        
    if req.disease not in le_disease.classes_ or req.region not in le_region.classes_:
        return {"predicted_cases": 0}
        
    disease_enc = le_disease.transform([req.disease])[0]
    region_enc = le_region.transform([req.region])[0]
    
    test_df = pd.DataFrame([{
        '연도': int(req.year),
        '주차': int(req.week),
        '지역_encoded': region_enc,
        '질병명_encoded': disease_enc
    }])
    
    try:
        pred = model.predict(test_df)
        val = max(0, int(round(pred[0])))
        return {"predicted_cases": val}
    except Exception as e:
        print(f"❌ 개별 조회 연산 에러: {e}")
        return {"predicted_cases": 0}