import os
import glob
import re
import pandas as pd
import datetime
import warnings

warnings.filterwarnings('ignore')

def find_actual_header_and_load(path, is_covid=False):
    raw_df = pd.read_excel(path, header=None, dtype=str)
    header_idx = None
    
    for idx, row in raw_df.iterrows():
        row_values = [str(val).strip() for val in row.values if pd.notna(val)]
        
        if is_covid:
            if any('시도명' in val or '시군구' in val for val in row_values):
                header_idx = idx
                break
        else:
            if '구분' in row_values and '계' in row_values:
                header_idx = idx
                break
                
    if header_idx is None:
        return pd.read_excel(path, dtype=str)

    if is_covid:
        row7 = raw_df.iloc[header_idx].ffill()
        row8 = raw_df.iloc[header_idx + 1].ffill()
        
        combined_headers = []
        for r7, r8 in zip(row7, row8):
            r7_str = str(r7).strip() if pd.notna(r7) else ""
            r8_str = str(r8).strip() if pd.notna(r8) else ""
            
            if r7_str == r8_str or r8_str == "nan" or r8_str == "":
                combined_headers.append(r7_str)
            elif r7_str == "nan" or r7_str == "":
                combined_headers.append(r8_str)
            else:
                combined_headers.append(f"{r7_str} {r8_str}".strip())
        
        df = pd.read_excel(path, skiprows=header_idx + 2, header=None, dtype=str)
        df.columns = combined_headers
    else:
        df = pd.read_excel(path, skiprows=header_idx, dtype=str)
        
    return df

def preprocess_covid_data(path, year):
    df = find_actual_header_and_load(path, is_covid=True)
    df.columns = [str(col).strip() for col in df.columns]
    
    rename_dict = {}
    for col in df.columns:
        if '시도명' in col: rename_dict[col] = '시도'
        elif '시군구' in col: rename_dict[col] = '시군구'
    df = df.rename(columns=rename_dict)
    
    if '시도' not in df.columns or '시군구' not in df.columns:
        df = df.rename(columns={df.columns[0]: '시도', df.columns[1]: '시군구'})
        
    df = df.dropna(subset=['시도', '시군구'] if '시도' in df.columns else ['시도', '시군구']).copy()
    if '시度' in df.columns: df = df.rename(columns={'시도': '시도'})
    
    df['시도'] = df['시도'].astype(str).str.strip()
    df['시군구'] = df['시군구'].astype(str).str.strip()
    
    df_filtered = df[~df['시도'].isin(['전국', '계', '합계', 'nan'])].copy()
    df_filtered = df_filtered[~df_filtered['시군구'].isin(['전국', '계', '합계', 'nan'])].copy()
    
    df_filtered['지역명'] = df_filtered.apply(
        lambda row: f"{row['시도']} 전체" if row['시도'] == row['시군구'] or row['시군구'] in ['전체', '소계']
        else f"{row['시도']} {row['시군구']}", 
        axis=1
    )
    
    time_cols = [c for c in df_filtered.columns if '년' in c and '월' in c]
    
    df_long = pd.melt(
        df_filtered, 
        id_vars=['지역명'], 
        value_vars=time_cols, 
        var_name='기간', 
        value_name='발생건수'
    )
    
    df_long['주차'] = df_long['기간'].str.extract(r'(\d+)\s*월').fillna(0).astype(int)
    df_long = df_long[df_long['주차'] > 0].copy()
    
    df_long['연도'] = year
    df_long['질병명'] = '코로나'
    
    df_long['발생건수'] = df_long['발생건수'].astype(str).str.replace(',', '').str.strip()
    df_long['발생건수'] = pd.to_numeric(df_long['발생건수'], errors='coerce').fillna(0).astype(int)
    
    return df_long[['지역명', '연도', '주차', '질병명', '발생건수']]

def generate_master_dataset():
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(CURRENT_DIR, "data")
    file_paths = glob.glob(os.path.join(data_dir, "*.xlsx"))
    
    general_data = []
    covid_data = []
    valid_diseases = ['수두', '백일해', '유행성이하선염']

    for path in file_paths:
        file_name = os.path.basename(path)
        if '에볼라' in file_name: continue
        
        year_match = re.search(r'(20\d{2})', file_name)
        if not year_match: continue
        year = int(year_match.group(1))
        
        # [분기 1] 코로나 파일 처리 -> covid_data 리스트에 격리
        if '코로나' in file_name:
            try:
                df_covid = preprocess_covid_data(path, year)
                if not df_covid.empty:
                    covid_data.append(df_covid)
                    print(f"성공 (코로나 분리): [코로나] {file_name}")
            except Exception as e:
                print(f"실패: [코로나] {file_name} -> {e}")
                
        # [분기 2] 일반 질병 파일 처리 -> general_data 리스트에 격리
        else:
            disease_name = None
            for d in valid_diseases:
                if d in file_name:
                    disease_name = d
                    break
            if not disease_name: continue
            
            try:
                df = find_actual_header_and_load(path, is_covid=False)
                df.columns = [str(c).strip() for c in df.columns]
                
                rename_dict = {}
                if '구분' in df.columns: rename_dict['구분'] = '시도'
                if '구분.1' in df.columns: rename_dict['구분.1'] = '시군구'
                df = df.rename(columns=rename_dict)
                
                if '시도' not in df.columns or '시군구' not in df.columns:
                    df = df.rename(columns={df.columns[0]: '시도', df.columns[1]: '시군구'})
                
                df = df.dropna(subset=['시도', '시군구']).copy()
                df['시도'] = df['시도'].astype(str).str.strip()
                df['시군구'] = df['시군구'].astype(str).str.strip()
                
                df_filtered = df[~df['시도'].isin(['전국', '계', '합계', 'nan'])].copy()
                df_filtered = df_filtered[~df_filtered['시군구'].isin(['전국', '계', '합계', 'nan'])].copy()
                
                df_filtered['지역명'] = df_filtered.apply(
                    lambda row: f"{row['시도']} 전체" if row['시도'] == row['시군구'] or row['시군구'] in ['전체', '소계']
                    else f"{row['시도']} {row['시군구']}", 
                    axis=1
                )
                
                week_cols = [c for c in df_filtered.columns if re.search(r'\d+', str(c))]
                if not week_cols: continue
                
                df_long = pd.melt(df_filtered, id_vars=['지역명'], value_vars=week_cols, var_name='주차', value_name='발생건수')
                df_long['주차'] = df_long['주차'].astype(str).str.extract(r'(\d+)').astype(int)
                df_long['연度'] = year
                df_long = df_long.rename(columns={'연度': '연도'})
                df_long['질병명'] = disease_name
                
                df_long['발생건수'] = df_long['발생건수'].astype(str).str.replace(',', '').str.strip()
                df_long['발생건수'] = pd.to_numeric(df_long['발생건수'], errors='coerce').fillna(0).astype(int)
                
                if not df_long.empty:
                    general_data.append(df_long[['지역명', '연도', '주차', '질병명', '발생건수']])
                    print(f"성공 (마스터 통합): [{disease_name}] {file_name}")
            except Exception as e:
                print(f"실패: [{disease_name}] {file_name} -> {e}")
        
    # 1. 일반 질병 마스터 파일 저장 (Hurdle 모델 대상)
    if general_data:
        final_general_df = pd.concat(general_data, ignore_index=True)
        final_general_df = final_general_df.dropna(subset=['지역명'])
        final_general_df = final_general_df[~final_general_df['지역명'].str.contains('nan|전국', na=False)]
        
        output_path = os.path.join(data_dir, "processed_master_data.csv")
        final_general_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n[저장 완료] 일반 질병 마스터 데이터셋 구축 완료: {output_path}")
    else:
        print("\n[경고] 처리된 일반 질병 데이터가 전혀 없습니다.")

    # 2. 코로나 전용 파일 단독 저장
    if covid_data:
        final_covid_df = pd.concat(covid_data, ignore_index=True)
        final_covid_df = final_covid_df.dropna(subset=['지역명'])
        final_covid_df = final_covid_df[~final_covid_df['지역명'].str.contains('nan|전국', na=False)]
        
        covid_output_path = os.path.join(data_dir, "processed_covid_data.csv")
        final_covid_df.to_csv(covid_output_path, index=False, encoding='utf-8-sig')
        print(f"[저장 완료] 코로나 단독 데이터셋 구축 완료: {covid_output_path}")
    else:
        print("[참고] 처리된 코로나 데이터가 없습니다.")

if __name__ == "__main__":
    generate_master_dataset()