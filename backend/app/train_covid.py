import os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib

def train_covid_model():
    final_config = {
        "n_estimators": 1200,
        "learning_rate": 0.05,
        "max_depth": 9,
        "min_child_weight": 15,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "reg_alpha": 1,
        "reg_lambda": 5
    }

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    covid_data_path = os.path.join(CURRENT_DIR, "data", "processed_covid_data.csv")
    model_dir = os.path.join(CURRENT_DIR, "models")
    os.makedirs(model_dir, exist_ok=True)
    
    print("=== 1단계: COVID 데이터셋 로드 및 멀티 래그 피처 연산 ===")
    if not os.path.exists(covid_data_path):
        raise FileNotFoundError("processed_covid_data.csv 파일이 없습니다. 전처리 스크립트를 먼저 실행하세요.")
        
    df = pd.read_csv(covid_data_path)
    
    # 지역 인코더 생성 및 저장
    le_region = LabelEncoder()
    df['지역_encoded'] = le_region.fit_transform(df['지역명'])
    joblib.dump(le_region, os.path.join(model_dir, "le_region_covid.joblib"))
    
    # 시계열 정렬
    df = df.sort_values(by=['지역_encoded', '연도', '주차']).reset_index(drop=True)
    
    # COVID 연속성 학습을 위한 핵심 시차(Lag) 피처 생성
    df['lag_1'] = df.groupby(['지역_encoded'])['발생건수'].shift(1)
    df['lag_2'] = df.groupby(['지역_encoded'])['발생건수'].shift(2)
    df['lag_3'] = df.groupby(['지역_encoded'])['발생건수'].shift(3)
    df['rolling_mean_3'] = df.groupby(['지역_encoded'])['lag_1'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())
    
    # 결측치 방어 처리
    for col in ['lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']:
        df[col] = df.groupby(['지역_encoded'])[col].transform(lambda x: x.fillna(x.median())).fillna(0)
    
    X = df[['연도', '주차', '지역_encoded', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']]
    y = df['발생건수']
    
    # 데이터 분할
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"\n=== 2단계: COVID 단일 회귀 모델(Regressor) 학습 ===")
    y_train_log = np.log1p(y_train)
    
    reg_model = xgb.XGBRegressor(
        n_estimators=final_config["n_estimators"],
        learning_rate=final_config["learning_rate"],
        max_depth=final_config["max_depth"],
        min_child_weight=final_config["min_child_weight"],
        subsample=final_config["subsample"],
        colsample_bytree=final_config["colsample_bytree"],
        reg_alpha=final_config["reg_alpha"],
        reg_lambda=final_config["reg_lambda"],
        random_state=42,
        n_jobs=-1
    )
    reg_model.fit(X_train, y_train_log, eval_set=[(X_test, np.log1p(y_test))], verbose=False)
    
    # covid 전용 모델 저장
    reg_model.save_model(os.path.join(model_dir, "covid_regressor.json"))
    
    print(f"\n=== 3단계: 예측 및 오프라인 지표 검증 ===")
    pred_log = reg_model.predict(X_test)
    final_pred = np.expm1(pred_log)
    final_pred = np.clip(final_pred, 0, None)
    
    # 지표 산출
    r2 = r2_score(y_test, final_pred)
    mae = mean_absolute_error(y_test, final_pred)
    rmse = np.sqrt(mean_squared_error(y_test, final_pred))
    
    y_mean = y_test.mean()
    ratio = (rmse / y_mean) * 100 if y_mean > 0 else 0
    
    print("=" * 60)
    print("📈 [COVID 단일 시계열 파이프라인 최종 점수 리포트]")
    print("-" * 60)
    print(f"COVID 평균 확진 건수     : {y_mean:.4f} 건")
    print(f"결정계수 (R² Score)        : {r2:.4f}")
    print(f"평균절대오차 (MAE)        : {mae:.4f} 건")
    print(f"평균제곱근오차 (RMSE)      : {rmse:.4f} 건")
    print(f"평균값 대비 RMSE 오차 비율 : {ratio:.2f} %")
    print("=" * 60)
    
    
    result_file = os.path.join(CURRENT_DIR, "covid_performance_report.csv")
    current_result = {
        "run_id": "local_final_run",
        "n_estimators": final_config["n_estimators"],
        "learning_rate": final_config["learning_rate"],
        "max_depth": final_config["max_depth"],
        "subsample": final_config["subsample"],
        "colsample_bytree": final_config["colsample_bytree"],
        "R2_Score": round(r2, 4),
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "Error_Ratio_Percent": round(ratio, 2)
    }
    
    df_res = pd.DataFrame([current_result])
    if not os.path.exists(result_file):
        df_res.to_csv(result_file, index=False, encoding='utf-8-sig')
    else:
        df_res.to_csv(result_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        

if __name__ == "__main__":
    train_covid_model()