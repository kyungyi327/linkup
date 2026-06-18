from pathlib import Path
import pandas as pd

def process_fitteum_csv(input_csv_path, output_csv_path):
    """
    비어있는 secondaryMuscles 컬럼이 있어도 데이터가 밀리지 않도록
    안전장치를 대폭 강화한 최종 정제 함수
    """
    print(f"📖 1. 데이터 불러오는 중: {input_csv_path}")
    try:
        df = pd.read_csv(input_csv_path)
    except FileNotFoundError:
        print(f"❌ 에러: 파일을 찾을 수 없습니다. 경로와 파일명을 다시 확인해 주세요.")
        return None

    # 🛑 1. 기구 필터링 (equipment가 'body weight'인 것만 추출)
    if 'equipment' in df.columns:
        bodyweight_df = df[df['equipment'].astype(str).str.lower().str.strip() == 'body weight'].copy()
    else:
        print("❌ 에러: 데이터에 'equipment' 컬럼이 존재하지 않습니다.")
        return None

    print(f"🔍 맨몸 운동(body weight) 필터링 후 개수: {len(bodyweight_df)}개")

    # 🏷️ 2. 운동 강도(intensity) 자동 분류 함수
    def assign_intensity(row):
        name_str = str(row.get('name', '')).lower()
        instruction_cols = [col for col in row.index if 'instruction' in col]
        instruction_str = " ".join([str(row[col]) for col in instruction_cols if pd.notna(row[col])]).lower()
        
        search_text = name_str + " " + instruction_str
        
        if any(word in search_text for word in ['jump', 'chin-up', 'pull-up', 'single-leg', 'single leg', 'inverted', 'handstand', 'plyometrics', 'advanced', 'explosive']):
            return '고급'
        elif any(word in search_text for word in ['stretch', 'stretching', 'lie', 'lying', 'hold', 'passive', 'flexibility', 'warm-up', 'easy']):
            return '초급'
        else:
            return '중급'

    # 강도 레이블링 적용
    bodyweight_df['intensity'] = bodyweight_df.apply(assign_intensity, axis=1)

    # 🎯 [핵심 수정: 빈칸 방어 절차]
    # 요청하신 컬럼 리스트 정의
    requested_columns = [
        'bodyPart', 
        'name', 
        'gifUrl', 
        'target', 
        'secondaryMuscles/0', 
        'secondaryMuscles/1', 
        'intensity'
    ]
    
    # 엑셀 원본에 해당 컬럼이 없거나 비어있으면 강제로 공백 문자열("")을 주입하여 자리 밀림 방지
    for col in requested_columns:
        if col not in bodyweight_df.columns:
            bodyweight_df[col] = ""
        else:
            # 존재한다면 결측치(NaN)를 전부 빈 문자열("")로 치환합니다.
            bodyweight_df[col] = bodyweight_df[col].fillna("")

    # 💾 지정한 순서대로 컬럼을 딱 고정해서 CSV로 내보내기
    bodyweight_df[requested_columns].to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"✨ 데이터 정렬 및 자동 레이블링 완료!")
    print(f"💾 최종 완성 파일 경로: {output_csv_path}")
    
    return bodyweight_df[requested_columns]


# ==========================================
# 실행 구역
# ==========================================
if __name__ == "__main__":
    target_dir = Path("C:/workspace/Fitteum")
    
    input_file = target_dir / "exercises.csv"
    output_file = target_dir / "labeled_exercises.csv"
    
    process_fitteum_csv(input_file, output_file)