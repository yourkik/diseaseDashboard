import os
import glob
import re
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")

MODEL_PATH = os.path.join(MODEL_DIR, "integrated_disease_xgboost.json")
LE_DISEASE_PATH = os.path.join(MODEL_DIR, "le_disease.joblib")
LE_REGION_PATH = os.path.join(MODEL_DIR, "le_region.joblib")

model = xgb.XGBRegressor()
le_disease = None
le_region = None
GLOBAL_HISTORY_DF = None

if os.path.exists(MODEL_PATH):
    model.load_model(MODEL_PATH)
else:
    print(f"Warning: Model file missing at {MODEL_PATH}")

if os.path.exists(LE_DISEASE_PATH) and os.path.exists(LE_REGION_PATH):
    le_disease = joblib.load(LE_DISEASE_PATH)
    le_region = joblib.load(LE_REGION_PATH)
else:
    print("Warning: LabelEncoder files missing")

def find_actual_header_and_load(path):
    raw_df = pd.read_excel(path, header=None, dtype=str)
    header_idx = 0
    for idx, row in raw_df.iterrows():
        row_values = [str(val).strip() for val in row.values if pd.notna(val)]
        if '구분' in row_values and '계' in row_values:
            header_idx = idx
            break
    df = pd.read_excel(path, skiprows=header_idx, dtype=str)
    return df

def get_realtime_history_df():
    all_data = []
    file_paths = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))
    valid_diseases = ['수두', '백일해', '유행성이하선염']

    for path in file_paths:
        file_name = os.path.basename(path)
        if '코로나' in file_name or '에볼라' in file_name: 
            continue
        
        disease_name = None
        year = None
        for d in valid_diseases:
            if d in file_name:
                disease_name = d
                break
        year_match = re.search(r'(202\d)', file_name)
        if year_match: 
            year = int(year_match.group(1))
        if not disease_name or not year: 
            continue
        
        try:
            df = find_actual_header_and_load(path)
            stop_idx = None
            for idx, row in df.iterrows():
                row_str = "".join([str(val) for val in row.values if pd.notna(val)])
                if '통계 집계 기준' in row_str:
                    stop_idx = idx
                    break
            if stop_idx is not None:
                df = df.iloc[:stop_idx]
            new_cols = ['시도', '시군구']
            remaining_cols = list(df.columns[2:])
            if remaining_cols and '계' in str(remaining_cols[0]):
                new_cols.append('계')
                new_cols.extend(remaining_cols[1:])
            else:
                new_cols.extend(remaining_cols)
                
            df.columns = new_cols[:len(df.columns)]
            df_filtered = df[df['시도'] != '전국'].copy()
            
            df_filtered['지역명'] = df_filtered.apply(
                lambda row: f"{str(row['시도']).strip()} 전체" if str(row['시도']).strip() == str(row['시군구']).strip() 
                else f"{str(row['시도']).strip()} {str(row['시군구']).strip()}", 
                axis=1
            )
            
            drop_targets = [c for c in ['시도', '시군구', '계'] if c in df_filtered.columns]
            df_filtered = df_filtered.drop(columns=drop_targets)
            
            df_long = pd.melt(df_filtered, id_vars=['지역명'], var_name='주차', value_name='발생건수')
            df_long['주차'] = df_long['주차'].astype(str).str.strip()
            df_long = df_long[df_long['주차'].str.isdigit()].copy()
            df_long['주차'] = df_long['주차'].astype(int)
            df_long['연도'] = year
            df_long['질병명'] = disease_name
            
            df_long['발생건수'] = df_long['발생건수'].astype(str).str.replace(',', '').str.strip()
            df_long['발생건수'] = pd.to_numeric(df_long['발생건수'], errors='coerce').fillna(0).astype(int)
            
            all_data.append(df_long)
        except Exception:
            continue
        
    if not all_data:
        return pd.DataFrame(columns=['연도', '주차', '지역명', '질병명', '발생건수'])
    return pd.concat(all_data, ignore_index=True)

# 서버 시작 시 엑셀 데이터를 RAM에 적재하여 런타임 지연 원천 차단
try:
    print("Initial processing: Loading Excel data into memory...")
    GLOBAL_HISTORY_DF = get_realtime_history_df()
    print(f"Caching complete: Loaded {len(GLOBAL_HISTORY_DF)} rows.")
except Exception as e:
    print(f"Error initializing memory cache: {e}")

def extract_sliding_windows(history_df, target_year, target_week, disease_str, region_str=None):
    history_df['absolute_week'] = history_df['연도'] * 53 + history_df['주차']
    target_abs_week = target_year * 53 + target_week
    needed_abs_weeks = [target_abs_week - 1, target_abs_week - 2, target_abs_week - 3]
    
    disease_df = history_df[history_df['질병명'] == disease_str]
    if region_str:
        disease_df = disease_df[disease_df['지역명'] == region_str]
        
    window_map = {}
    for (r_name), group in disease_df.groupby(['지역명']):
        sub_g = group[group['absolute_week'].isin(needed_abs_weeks)]
        
        lag_1 = sub_g[sub_g['absolute_week'] == (target_abs_week - 1)]['발생건수'].values
        lag_2 = sub_g[sub_g['absolute_week'] == (target_abs_week - 2)]['발생건수'].values
        lag_3 = sub_g[sub_g['absolute_week'] == (target_abs_week - 3)]['발생건수'].values
        
        l1 = int(lag_1[0]) if len(lag_1) > 0 else 0
        l2 = int(lag_2[0]) if len(lag_2) > 0 else 0
        l3 = int(lag_3[0]) if len(lag_3) > 0 else 0
        
        valid_lags = [l1, l2, l3]
        r_mean = float(np.mean(valid_lags)) if valid_lags else 0.0
        
        window_map[r_name] = {
            'lag_1': l1,
            'lag_2': l2,
            'lag_3': l3,
            'rolling_mean_3': r_mean
        }
    return window_map

class SearchRequest(BaseModel):
    disease: str
    year: int
    week: int
    region: str = None

@router.post("/predict/top-danger")
def get_top_danger_regions(req: SearchRequest):
    if le_disease is None or le_region is None:
        raise HTTPException(status_code=500, detail="Encoder not ready")

    if req.disease not in le_disease.classes_:
        return {"disease": req.disease, "top_regions": []}
        
    disease_enc = le_disease.transform([req.disease])[0]
    
    if GLOBAL_HISTORY_DF is None or GLOBAL_HISTORY_DF.empty:
        raise HTTPException(status_code=500, detail="Global history cache is empty")
        
    window_map = extract_sliding_windows(GLOBAL_HISTORY_DF, req.year, req.week, req.disease)
    
    records = []
    for region_name in le_region.classes_:
        if "전체" in region_name:
            continue
            
        region_enc = le_region.transform([region_name])[0]
        win_data = window_map.get(region_name, {'lag_1': 0, 'lag_2': 0, 'lag_3': 0, 'rolling_mean_3': 0.0})
        
        records.append({
            '연도': int(req.year),
            '주차': int(req.week),
            '지역_encoded': region_enc,
            '질병명_encoded': disease_enc,
            'lag_1': win_data['lag_1'],
            'lag_2': win_data['lag_2'],
            'lag_3': win_data['lag_3'],
            'rolling_mean_3': win_data['rolling_mean_3'],
            'region_name': region_name
        })
        
    if not records:
        return {"disease": req.disease, "top_regions": []}
        
    test_df = pd.DataFrame(records)
    X = test_df[['연도', '주차', '지역_encoded', '질병명_encoded', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']]
    
    preds = model.predict(X)
    test_df['predicted_cases'] = [max(0, int(round(p))) for p in preds]
    
    national_row = test_df[test_df['region_name'].str.contains("전국", na=False)]
    national_cases = int(national_row['predicted_cases'].values[0]) if not national_row.empty else 0
    
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
        "national_cases": national_cases
    }

@router.post("/predict/region")
def get_single_region_prediction(req: SearchRequest):
    if le_disease is None or le_region is None:
        raise HTTPException(status_code=500, detail="Encoder not ready")
        
    if req.disease not in le_disease.classes_ or req.region not in le_region.classes_:
        return {"predicted_cases": 0}
        
    disease_enc = le_disease.transform([req.disease])[0]
    region_enc = le_region.transform([req.region])[0]
    
    if GLOBAL_HISTORY_DF is None or GLOBAL_HISTORY_DF.empty:
        raise HTTPException(status_code=500, detail="Global history cache is empty")
        
    window_map = extract_sliding_windows(GLOBAL_HISTORY_DF, req.year, req.week, req.disease, req.region)
    win_data = window_map.get(req.region, {'lag_1': 0, 'lag_2': 0, 'lag_3': 0, 'rolling_mean_3': 0.0})
    
    test_df = pd.DataFrame([{
        '연도': int(req.year),
        '주차': int(req.week),
        '지역_encoded': region_enc,
        '질병명_encoded': disease_enc,
        'lag_1': win_data['lag_1'],
        'lag_2': win_data['lag_2'],
        'lag_3': win_data['lag_3'],
        'rolling_mean_3': win_data['rolling_mean_3']
    }])
    
    try:
        X = test_df[['연도', '주차', '지역_encoded', '질병명_encoded', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']]
        pred = model.predict(X)
        val = max(0, int(round(pred[0])))
        return {"predicted_cases": val}
    except Exception as e:
        print(f"Error in single prediction calculation: {e}")
        return {"predicted_cases": 0}