import os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
import wandb

def train_hurdle_model():
    run = wandb.init(project="disease-xgboost-tuning", entity="jiminyoun816-none")
    config = run.config

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    master_data_path = os.path.join(CURRENT_DIR, "data", "processed_master_data.csv")
    model_dir = os.path.join(CURRENT_DIR, "models")
    os.makedirs(model_dir, exist_ok=True)
    
    print("=== 1단계: 마스터 데이터셋 로드 및 멀티 래그 피처 연산 ===")
    if not os.path.exists(master_data_path):
        raise FileNotFoundError("processed_master_data.csv 파일이 없습니다. 전처리 스크립트를 먼저 실행하세요.")
        
    df = pd.read_csv(master_data_path)
    
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
    
    
    # 데이터 분할
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"\n=== 2단계: Hurdle 이진 분류 모델(Classifier) 학습 ===")
    # 타겟을 "발생함(1) / 발생안함(0)"으로 이진화
    y_train_clf = (y_train > 0).astype(int)
    y_test_clf = (y_test > 0).astype(int)
    
    # 0이 압도적으로 많으므로 scale_pos_weight로 불균형 조정
    pos_weight = (y_train_clf == 0).sum() / (y_train_clf == 1).sum()
    
    clf_model = xgb.XGBClassifier(
        n_estimators=config.get('n_estimators', 1000),
        learning_rate=config.get('learning_rate', 0.03),
        max_depth=config.get('max_depth', 7),
        subsample=config.get('subsample', 0.8),
        colsample_bytree=config.get('colsample_bytree', 0.8),
        scale_pos_weight=pos_weight,
        random_state=42,
        n_jobs=-1
    )
    clf_model.fit(X_train, y_train_clf, eval_set=[(X_test, y_test_clf)], verbose=False)
    
    print(f"\n=== 3단계: Hurdle 수량 회귀 모델(Regressor) 학습 ===")
    # 실제 환자가 발생한(Positive) 데이터만 필터링하여 회귀기 학습 진행
    pos_mask_train = (y_train > 0)
    X_train_reg = X_train[pos_mask_train]
    y_train_reg = y_train[pos_mask_train]
    
    # 극단적 아웃라이어 완화를 위해 회귀 타겟 변수에 log1p 적용
    y_train_reg_log = np.log1p(y_train_reg)
    
    reg_model = xgb.XGBRegressor(
        n_estimators=config.get('n_estimators', 1000),
        learning_rate=config.get('learning_rate', 0.03),
        max_depth=config.get('max_depth', 7),
        subsample=config.get('subsample', 0.8),
        colsample_bytree=config.get('colsample_bytree', 0.8),
        min_child_weight=config.get('min_child_weight', 1),
        random_state=42,
        n_jobs=-1
    )
    reg_model.fit(X_train_reg, y_train_reg_log, verbose=False)
    
    # 두 개의 독립 모델 파일로 각각 저장
    clf_model.save_model(os.path.join(model_dir, "hurdle_classifier.json"))
    reg_model.save_model(os.path.join(model_dir, "hurdle_regressor.json"))
    
    print(f"\n=== 4단계: 투스텝 파이프라인 결합 및 오프라인 지표 검증 ===")
    # 1. 분류기로 발생 여부 예측 (0 또는 1)
    pred_clf = clf_model.predict(X_test)
    
    # 2. 회귀기로 건수 예측 및 원래 스케일 복원(expm1)
    pred_reg_log = reg_model.predict(X_test)
    pred_reg = np.expm1(pred_reg_log)
    pred_reg = np.clip(pred_reg, 0, None) # 음수 방지 방어코드
    
    # 3. 투스텝 결합 체인 가동: 분류가 0이면 무조건 0건, 1이면 회귀 결과 적용
    final_pred = np.where(pred_clf == 1, pred_reg, 0)
    
    # 지표 산출
    r2 = r2_score(y_test, final_pred)
    mae = mean_absolute_error(y_test, final_pred)
    rmse = np.sqrt(mean_squared_error(y_test, final_pred))
    
    y_mean = y_test.mean()
    ratio = (rmse / y_mean) * 100 if y_mean > 0 else 0
    
    print("=" * 60)
    print("📈 [Hurdle Two-Stage 파이프라인 최종 점수 리포트]")
    print("-" * 60)
    print(f"타겟 데이터 평균 건수      : {y_mean:.4f} 건")
    print(f"결정계수 (R² Score)        : {r2:.4f}")
    print(f"평균절대오차 (MAE)        : {mae:.4f} 건")
    print(f"평균제곱근오차 (RMSE)      : {rmse:.4f} 건")
    print(f"평균값 대비 RMSE 오차 비율 : {ratio:.2f} %")
    print("=" * 60)
    
    metrics = {"R2_Score": r2, "MAE": mae, "RMSE": rmse, "Error_Ratio": ratio}
    wandb.log(metrics)
    
    # 결과 아카이빙 (CSV 누적 저장)
    result_file = os.path.join(CURRENT_DIR, "hurdle_performance_report.csv")
    current_result = {
        "run_id": run.id,
        "n_estimators": config.get('n_estimators'),
        "learning_rate": config.get('learning_rate'),
        "max_depth": config.get('max_depth'),
        "subsample": config.get('subsample'),
        "colsample_bytree": config.get('colsample_bytree'),
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
        
    run.finish()

if __name__ == "__main__":
    if wandb.run is None:
        
        class DummyConfig:
            def get(self, key, default=None): 
                return default
        
        class DummyRun:
            config = DummyConfig()
            id = "hurdle_local_test"
            def finish(self): pass
            def log(self, metrics):
                print(f"[Local Only] wandb 로그 전송 생략됨: {metrics}")
        
        dummy = DummyRun()
        wandb.init = lambda **kwargs: dummy
        wandb.log = lambda metrics: dummy.log(metrics)
        
    train_hurdle_model()