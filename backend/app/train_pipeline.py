import os
import glob
import re
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import warnings

# 불필요한 경고창 숨김 처리
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', category=FutureWarning)

def find_actual_header_and_load(path):
    """
    엑셀 파일 상단의 불필요한 메타데이터 행들을 건너뛰고,
    '구분'과 '계'가 시작되는 진짜 헤더 행을 찾아 데이터프레임을 로드합니다.
    """
    # 먼저 전체 데이터를 문자열로 로드하여 탐색
    raw_df = pd.read_excel(path, header=None, dtype=str)
    
    header_idx = 0
    for idx, row in raw_df.iterrows():
        row_values = [str(val).strip() for val in row.values if pd.notna(val)]
        # 행 내용물 중 '구분'과 '계'가 모두 들어있는 진짜 데이터 시작행 포착
        if '구분' in row_values and '계' in row_values:
            header_idx = idx
            break
            
    # 찾은 헤더 위치를 반영하여 재로드
    df = pd.read_excel(path, skiprows=header_idx, dtype=str)
    return df

def load_and_preprocess_data(data_dir):
    all_data = []
    file_paths = glob.glob(os.path.join(data_dir, "*.xlsx"))

    if not file_paths:
        raise FileNotFoundError(f"'{data_dir}' 폴더 안에 .xlsx 파일이 존재하지 않습니다. 파일을 확인해 주세요.")

    valid_diseases = ['수두', '백일해', '유행성이하선염']

    for path in file_paths:
        file_name = os.path.basename(path)
        
        if '코로나' in file_name or '에볼라' in file_name:
            print(f"분석 대상이 아니므로 제외됨: {file_name}")
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
            print(f"파일명에서 질병명 또는 연도를 추출할 수 없어 제외됨: {file_name}")
            continue
            
        print(f"   -> [읽기 시작] 질병: {disease_name} | 연도: {year}년 | 파일명: {file_name}")
        
        try:
            # 수정된 동적 헤더 탐색 로드 함수 사용
            df = find_actual_header_and_load(path)
            
            # 병합 해제 등으로 발생할 수 있는 컬럼 중복 방지를 위해 앞의 2개 컬럼을 강제 정의
            # 감염병포털 특성상 구분, 구분 두 개가 나란히 들어오는 현상 대응
            new_cols = ['시도', '시군구']
            
            # 세 번째 컬럼부터 매핑 처리 진행
            remaining_cols = list(df.columns[2:])
            
            # '계' 컬럼 이름 고정 및 나머지 주차 컬럼 매핑 구조화
            if remaining_cols and '계' in str(remaining_cols[0]):
                new_cols.append('계')
                new_cols.extend(remaining_cols[1:])
            else:
                new_cols.extend(remaining_cols)
                
            # 컬럼 수 맞춤형 재조정
            df.columns = new_cols[:len(df.columns)]
            
            # '전국' 행 제외 및 시도/시군구 복합 엔티티 유지
            df_filtered = df[df['시도'] != '전국'].copy()
            
            # 시도 전체와 하위 시군구 결합 고유 지역명 스트링 빌드
            df_filtered['지역명'] = df_filtered.apply(
                lambda row: f"{str(row['시도']).strip()} 전체" if str(row['시도']).strip() == str(row['시군구']).strip() 
                else f"{str(row['시도']).strip()} {str(row['시군구']).strip()}", 
                axis=1
            )
            
            # 가용 컬럼만 안전하게 필터링하여 드롭
            drop_targets = [c for c in ['시도', '시군구', '계'] if c in df_filtered.columns]
            df_filtered = df_filtered.drop(columns=drop_targets)
            
            # 와이드 포맷 -> 롱 포맷 멜트 가동
            df_long = pd.melt(
                df_filtered, 
                id_vars=['지역명'], 
                var_name='주차', 
                value_name='발생건수'
            )
            
            # 주차 텍스트 정제 및 순수 숫자 필터링
            df_long['주차'] = df_long['주차'].astype(str).str.strip()
            df_long = df_long[df_long['주차'].str.isdigit()].copy()
            
            # 타입 캐스팅 파이프라인 정렬
            df_long['주차'] = df_long['주차'].astype(int)
            df_long['연도'] = year
            df_long['질병명'] = disease_name
            
            # 발생자 수 0명 및 쉼표 예외 처리 무결성 확보
            df_long['발생건수'] = df_long['발생건수'].astype(str).str.replace(',', '').str.strip()
            df_long['발생건수'] = pd.to_numeric(df_long['발생건수'], errors='coerce').fillna(0).astype(int)
            
            all_data.append(df_long)
            
        except Exception as e:
            print(f"파일 읽기 중 내부 데이터 구조 오류 발생 ({file_name}): {e}")
            continue
        
    if not all_data:
        raise ValueError("정상적으로 로드된 엑셀 데이터가 없습니다.")
        
    final_df = pd.concat(all_data, ignore_index=True)
    return final_df

def train_xgboost_model():
    data_dir = "backend/app/data"
    model_dir = "backend/app/models"
    os.makedirs(model_dir, exist_ok=True)
    
    print("=== 1단계: 엑셀 데이터 로드 및 시도/시군구 복합 전처리 시작 ===")
    try:
        df = load_and_preprocess_data(data_dir)
    except Exception as e:
        print(f"{e}")
        return
    
    print(f"▶ 데이터 수집 성공! 총 수집된 데이터 행 수: {len(df)}개")
    
    # 문자열 카테고리 데이터 수치형 변환
    le_region = LabelEncoder()
    le_disease = LabelEncoder()
    
    df['지역_encoded'] = le_region.fit_transform(df['지역명'])
    df['질병명_encoded'] = le_disease.fit_transform(df['질병명'])
    
    # FastAPI 백엔드 서빙용 인코더 객체 저장
    joblib.dump(le_region, os.path.join(model_dir, "le_region.joblib"))
    joblib.dump(le_disease, os.path.join(model_dir, "le_disease.joblib"))
    
    # 데이터 매트릭스 변수 세팅
    X = df[['연도', '주차', '지역_encoded', '질병명_encoded']]
    y = df['발생건수']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"\n=== 2단계: XGBoost Regressor 통합 모델 학습 진행 ===")
    model = xgb.XGBRegressor(
        n_estimators=200,
        learning_rate=0.07,
        max_depth=6,
        random_state=42
    )
    
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    
    # 학습 완료된 가중치 엔진 파일 저장
    model_path = os.path.join(model_dir, "integrated_disease_xgboost.json")
    model.save_model(model_path)
    
    print(f"\n=== 3단계: 파이프라인 무결성 검증 및 모델 다운로드 완료 ===")
    print(f"▶ 저장된 통합 모델 경로: {os.path.abspath(model_path)}")
    print(f"▶ 복합 인코딩 완료된 지역 총 개수: {len(le_region.classes_)}개")
    print(f"▶ 포함된 질병 목록: {list(le_disease.classes_)}")

if __name__ == "__main__":
    train_xgboost_model()