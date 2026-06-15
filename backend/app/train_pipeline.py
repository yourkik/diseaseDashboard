import os
import glob
import re
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
import warnings

warnings.filterwarnings('ignore')

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

def load_and_preprocess_data(data_dir):
    all_data = []
    file_paths = glob.glob(os.path.join(data_dir, "*.xlsx"))
    valid_diseases = ['수두', '백일해', '유행성이하선염']

    for path in file_paths:
        file_name = os.path.basename(path)
        if '코로나' in file_name or '에볼라' in file_name: continue
        
        disease_name = None
        year = None
        for d in valid_diseases:
            if d in file_name:
                disease_name = d
                break
        year_match = re.search(r'(202\d)', file_name)
        if year_match: year = int(year_match.group(1))
        if not disease_name or not year: continue
        
        try:
            df = find_actual_header_and_load(path)
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
        
    final_df = pd.concat(all_data, ignore_index=True)
    return final_df

def train_xgboost_model():
    data_dir = "backend/app/data"
    model_dir = "backend/app/models"
    os.makedirs(model_dir, exist_ok=True)
    
    print("=== 1단계: 멀티 래그 슬라이딩 윈도우 및 이동 평균 연산 가동 ===")
    df = load_and_preprocess_data(data_dir)
    
    le_region = LabelEncoder()
    le_disease = LabelEncoder()
    df['지역_encoded'] = le_region.fit_transform(df['지역명'])
    df['질병명_encoded'] = le_disease.fit_transform(df['질병명'])
    
    joblib.dump(le_region, os.path.join(model_dir, "le_region.joblib"))
    joblib.dump(le_disease, os.path.join(model_dir, "le_disease.joblib"))
    
    # 시계열 순서 정렬 무결성 보장
    df = df.sort_values(by=['질병명_encoded', '지역_encoded', '연도', '주차']).reset_index(drop=True)
    
    # 슬라이딩 윈도우 기반 멀티 래그 피처 생성
    df['lag_1'] = df.groupby(['질병명_encoded', '지역_encoded'])['발생건수'].shift(1)
    df['lag_2'] = df.groupby(['질병명_encoded', '지역_encoded'])['발생건수'].shift(2)
    df['lag_3'] = df.groupby(['질병명_encoded', '지역_encoded'])['발생건수'].shift(3)
    
    # 최근 3주간의 이동 평균(Rolling Mean) 피처 생성 (단기 노이즈 평탄화)
    # 자기 자신(금주 발생건수)을 포함하지 않기 위해 shift(1) 기준 윈도우 연산 적용
    df['rolling_mean_3'] = df.groupby(['질병명_encoded', '지역_encoded'])['lag_1'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())
    
    # 과거 데이터 누락 영역 결측치 보정 (중앙값 대체 후 0 처리)
    for col in ['lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']:
        df[col] = df.groupby(['질병명_encoded', '지역_encoded'])[col].transform(lambda x: x.fillna(x.median())).fillna(0)
    
    # 확장된 독립변수 독립 매트릭스 레이아웃 정렬
    X = df[['연도', '주차', '지역_encoded', '질병명_encoded', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']]
    X.columns = ['연도', '주차', '지역_encoded', '질병명_encoded', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']
    y = df['발생건수']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"\n=== 2단계: 최적화 하이퍼파라미터 기반 XGBoost 파인튜닝 ===")
    model = xgb.XGBRegressor(
        n_estimators=800,         # 성능 극대화를 위해 트리 용량 재확장
        learning_rate=0.02,       # 오차 수렴 정밀도 극대화
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
    model_path = os.path.join(model_dir, "integrated_disease_xgboost.json")
    model.save_model(model_path)
    
    print(f"\n=== 3단계: 슬라이딩 윈도우 파이프라인 최종 점수 검증 ===")
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    print("=" * 60)
    print("📈 [XGBoost 초고도화 윈도우 파이프라인 성능 리포트]")
    print("-" * 60)
    print(f"결정계수 (R² Score)        : {r2:.4f}")
    print(f"평균절대오차 (MAE)        : {mae:.4f} 건")
    print(f"평균제곱근오차 (RMSE)      : {rmse:.4f} 건")
    print("=" * 60)

if __name__ == "__main__":
    train_xgboost_model()