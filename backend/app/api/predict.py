import os
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/predict", tags=["prediction"])


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # app/api
BACKEND_ROOT = os.path.dirname(CURRENT_DIR)  # app
MODEL_DIR = os.path.join(BACKEND_ROOT, "models")
DATA_DIR = os.path.join(BACKEND_ROOT, "data")

# Pydantic 요청 스키마
class PredictionRequest(BaseModel):
    disease: str
    year: int
    week: int

class RegionPredictionRequest(BaseModel):
    disease: str
    year: int
    week: int
    region: str

# 에셋 로드 (파일이 없을 경우 None 처리하여 서버 구동 실패 방지)
def safe_load_joblib(filename):
    path = os.path.join(MODEL_DIR, filename)
    return joblib.load(path) if os.path.exists(path) else None

def safe_load_xgb(model_class, filename):
    path = os.path.join(MODEL_DIR, filename)
    if os.path.exists(path):
        model = model_class()
        model.load_model(path)
        return model
    return None

def safe_load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        df = pd.read_csv(path)
        if '지역명' in df.columns:
            df = df[~df['지역명'].str.contains('전체', na=False)]
        return df
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

# 일반 질병용 에셋 로드
le_region = safe_load_joblib("le_region.joblib")
le_disease = safe_load_joblib("le_disease.joblib")
clf_model = safe_load_xgb(xgb.XGBClassifier, "hurdle_classifier.json")
reg_model = safe_load_xgb(xgb.XGBRegressor, "hurdle_regressor.json")

# COVID 전용 에셋 로드
le_region_covid = safe_load_joblib("le_region_covid.joblib")
covid_model = safe_load_xgb(xgb.XGBRegressor, "covid_regressor.json")

# 최신 시계열 래그 피처 추적용 데이터셋 로드
master_df = safe_load_csv("processed_master_data.csv")
covid_df = safe_load_csv("processed_covid_data.csv")

def check_models_loaded():
    if clf_model is None or covid_model is None:
        raise HTTPException(status_code=503, detail="AI 예측 모델(JSON)이 아직 생성되지 않았습니다. 머신러닝 파이프라인을 먼저 실행해 주세요.")



def extract_lag_features(df_source, region_name, disease_name, is_covid=False):
    """원천 데이터 히스토리에서 해당 지역/질병의 최신 3개 주차 데이터를 추출해 시차 피처 생성"""
    r_name = str(region_name).strip()
    d_name = str(disease_name).strip()
    
    if is_covid:
        sub_df = df_source[df_source['지역명'].str.contains(r_name, na=False, regex=False)]
    else:
        sub_df = df_source[
            (df_source['지역명'].str.contains(r_name, na=False, regex=False)) & 
            (df_source['질병명'].str.contains(d_name, na=False, regex=False))
        ]
        
    if sub_df.empty:
        return 0.0, 0.0, 0.0, 0.0
        
    sub_df = sub_df[sub_df['발생건수'].notna()].sort_values(by=['연도', '주차'], ascending=False)
    history = sub_df['발생건수'].values
    
    lag_1 = float(history[0]) if len(history) > 0 else 0.0
    lag_2 = float(history[1]) if len(history) > 1 else 0.0
    lag_3 = float(history[2]) if len(history) > 2 else 0.0
    rolling_mean_3 = float(np.mean(history[:3])) if len(history) > 0 else 0.0
    
    return lag_1, lag_2, lag_3, rolling_mean_3


@router.post("/top-danger")
async def get_top_danger(req: PredictionRequest):
    check_models_loaded()
    disease = "코로나19" if req.disease in ["코로나19", "covid", "COVID"] else req.disease
    is_covid = (disease == "코로나19")
    
    target_df = covid_df if is_covid else master_df
    encoder = le_region_covid if is_covid else le_region
    
    if target_df.empty:
        return {"top_regions": [], "national_cases": 0}
        
    eval_year = int(target_df['연도'].max())
    eval_week = int(target_df[target_df['연도'] == eval_year]['주차'].max())
    
    all_regions = target_df['지역명'].unique()
    results = []
    
    for r_name in all_regions:
        try:
            r_enc = encoder.transform([r_name])[0]
        except ValueError:
            continue
            
        lag_1, lag_2, lag_3, rolling_mean = extract_lag_features(
            target_df, r_name, disease, is_covid=is_covid
        )
        
        if is_covid:
            features = pd.DataFrame([{
                '연도': req.year, '주차': req.week, '지역_encoded': r_enc,
                'lag_1': lag_1, 'lag_2': lag_2, 'lag_3': lag_3, 'rolling_mean_3': rolling_mean
            }])
            pred_raw = covid_model.predict(features)[0]
            pred_cases = int(np.clip(pred_raw, 0, None))
        else:
            try:
                d_enc = le_disease.transform([disease])[0]
            except ValueError:
                continue
                
            # 1. features 변수를 먼저 안전하게 생성합니다.
            features = pd.DataFrame([{
                '연도': req.year, '주차': req.week, '지역_encoded': r_enc, '질병명_encoded': d_enc,
                'lag_1': lag_1, 'lag_2': lag_2, 'lag_3': lag_3, 'rolling_mean_3': rolling_mean
            }])
            
            prob_positive = clf_model.predict_proba(features)[0][1]
            
            # 강남구 디버깅 로그
            if r_name == "서울 강남구":
                print(f"\n===== [디버그] {r_name} / {disease} 데이터 매칭 검증 =====")
                print(f"-> 추출된 피처: lag_1={lag_1}, lag_2={lag_2}, lag_3={lag_3}, rolling_mean_3={rolling_mean}")
                print(f"-> 🎯 XGBoost 분류기가 계산한 강남구 발생 확률: {prob_positive:.4f} (기준선: 0.15)")
            
            if prob_positive >= 0.01:
                pred_log = reg_model.predict(features)[0]
                pred_cases = int(np.clip(np.expm1(pred_log), 0, None))
            else:
                pred_cases = 0
                
        results.append({"region": r_name, "predicted_cases": pred_cases})
        
    results = sorted(results, key=lambda x: x['predicted_cases'], reverse=True)
    top_regions = results[:3]
    national_cases = sum(r['predicted_cases'] for r in results)
    
    return {
        "top_regions": top_regions,
        "national_cases": national_cases
    }


@router.post("/region")
async def get_region_prediction(req: RegionPredictionRequest):
    check_models_loaded()
    disease = "코로나19" if req.disease in ["코로나19", "covid", "COVID"] else req.disease
    is_covid = (disease == "코로나19")
    
    target_df = covid_df if is_covid else master_df
    encoder = le_region_covid if is_covid else le_region
    
    eval_year = int(target_df['연도'].max())
    eval_week = int(target_df[target_df['연도'] == eval_year]['주차'].max())
    
    try:
        r_enc = encoder.transform([req.region])[0]
    except ValueError:
        raise HTTPException(status_code=400, detail="학습 모델 매트릭스에 존재하지 않는 지역명입니다.")
        
    lag_1, lag_2, lag_3, rolling_mean = extract_lag_features(
        target_df, req.region, disease, is_covid=is_covid
    )
    
    if is_covid:
        features = pd.DataFrame([{
            '연도': req.year, '주차': req.week, '지역_encoded': r_enc,
            'lag_1': lag_1, 'lag_2': lag_2, 'lag_3': lag_3, 'rolling_mean_3': rolling_mean
        }])
        pred_raw = covid_model.predict(features)[0]
        pred_cases = int(np.clip(pred_raw, 0, None))
        
    else:
        d_enc = le_disease.transform([disease])[0]
        features = pd.DataFrame([{
            '연도': req.year, '주차': req.week, '지역_encoded': r_enc, '질병명_encoded': d_enc,
            'lag_1': lag_1, 'lag_2': lag_2, 'lag_3': lag_3, 'rolling_mean_3': rolling_mean
        }])
        
        prob_positive = clf_model.predict_proba(features)[0][1]
        if prob_positive >= 0.01:
            pred_log = reg_model.predict(features)[0]
            pred_cases = int(np.clip(np.expm1(pred_log), 0, None))
        else:
            pred_cases = 0
            
    return {"predicted_cases": pred_cases}