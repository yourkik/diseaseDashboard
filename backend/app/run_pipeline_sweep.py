import os
import glob
import re
import datetime
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
import warnings
import wandb

warnings.filterwarnings('ignore')

GLOBAL_REPORT_PATH = None

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
    run = wandb.init()
    config = run.config

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(CURRENT_DIR, "data")
    model_dir = os.path.join(CURRENT_DIR, "models")
    os.makedirs(model_dir, exist_ok=True)
    
    df = load_and_preprocess_data(data_dir)
    
    le_region = LabelEncoder()
    le_disease = LabelEncoder()
    df['지역_encoded'] = le_region.fit_transform(df['지역명'])
    df['질병명_encoded'] = le_disease.fit_transform(df['질병명'])
    
    joblib.dump(le_region, os.path.join(model_dir, "le_region.joblib"))
    joblib.dump(le_disease, os.path.join(model_dir, "le_disease.joblib"))
    
    df = df.sort_values(by=['질병명_encoded', '지역_encoded', '연도', '주차']).reset_index(drop=True)
    
    df['lag_1'] = df.groupby(['질병명_encoded', '지역_encoded'])['발생건수'].shift(1)
    df['lag_2'] = df.groupby(['질병명_encoded', '지역_encoded'])['발생건수'].shift(2)
    df['lag_3'] = df.groupby(['질병명_encoded', '지역_encoded'])['발생건수'].shift(3)
    
    df['rolling_mean_3'] = df.groupby(['질병명_encoded', '지역_encoded'])['lag_1'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())
    
    for col in ['lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']:
        df[col] = df.groupby(['질병명_encoded', '지역_encoded'])[col].transform(lambda x: x.fillna(x.median())).fillna(0)
    
    X = df[['연도', '주차', '지역_encoded', '질병명_encoded', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']]
    y = df['발생건수']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBRegressor(
        n_estimators=config.n_estimators,
        learning_rate=config.learning_rate,
        max_depth=config.max_depth,
        subsample=config.subsample,
        colsample_bytree=config.colsample_bytree,
        min_child_weight=config.min_child_weight,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    metrics = {"R2_Score": r2, "MAE": mae, "RMSE": rmse}
    wandb.log(metrics)
    
    global GLOBAL_REPORT_PATH
    current_record = {
        "Run_ID": run.id,
        "n_estimators": config.n_estimators,
        "learning_rate": config.learning_rate,
        "max_depth": config.max_depth,
        "subsample": config.subsample,
        "colsample_bytree": config.colsample_bytree,
        "min_child_weight": config.min_child_weight,
        "R2_Score": round(r2, 4),
        "MAE_Score": round(mae, 4),
        "RMSE_Score": round(rmse, 4)
    }
    
    new_row_df = pd.DataFrame([current_record])
    
    if not os.path.exists(GLOBAL_REPORT_PATH):
        new_row_df.to_excel(GLOBAL_REPORT_PATH, index=False, engine='openpyxl')
    else:
        with pd.ExcelWriter(GLOBAL_REPORT_PATH, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
            start_row = writer.sheets['Sheet1'].max_row
            new_row_df.to_excel(writer, index=False, header=False, startrow=start_row, engine='openpyxl')
            
    print(f"📊 [Run 완료] ID: {run.id} | R²: {r2:.4f} | MAE: {mae:.4f} | RMSE: {rmse:.4f}")
    run.finish()

if __name__ == "__main__":
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    GLOBAL_REPORT_PATH = os.path.join(CURRENT_DIR, f"sweep_full_grid_report_{timestamp}.xlsx")
    
    # 변경 사항: 전수 조사를 위해 'grid' 방식으로 전환
    sweep_config = {
        "method": "grid",
        "parameters": {
            "n_estimators": {"values": [500, 800, 1000]},
            "learning_rate": {"values": [0.01, 0.03, 0.05, 0.1]},
            "max_depth": {"values": [5, 6, 7, 8]},
            "subsample": {"values": [0.7, 0.8, 0.9]},
            "colsample_bytree": {"values": [0.7, 0.8, 0.9]},
            "min_child_weight": {"values": [1, 3, 5]}
        }
    }
    
    sweep_id = wandb.sweep(sweep=sweep_config, entity="jiminyoun816-none", project="disease-xgboost-tuning")
    
    print(f"\n[🚀 모든 조합 전수조사 Grid Sweep 가동]")
    print(f"🎯 저장 파일명: {os.path.basename(GLOBAL_REPORT_PATH)}")
    print("주의: 파라미터 조합이 많아 시간이 다소 소요될 수 있습니다. 엑셀 파일에 실시간 누적됩니다.\n")
    
    # 변경 사항: count=15 제한을 해제하여 전체 경우의 수를 모두 학습하도록 설정
    wandb.agent(sweep_id, function=train_xgboost_model)
    
    print(f"\n[🏁 모든 그리드 탐색이 종료되었습니다.]")
    print(f"최종 엑셀 리포트 파일: {GLOBAL_REPORT_PATH}")