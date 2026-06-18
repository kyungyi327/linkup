from pathlib import Path
import sqlite3  # 💡 SQLite용 기본 라이브러리 (파이썬 기본 내장)
import pandas as pd

def import_csv_to_sqlite():
    # 1. 가공 완료된 CSV 파일 경로 지정
    target_dir = Path("C:/workspace/linkup/linkup/data")
    csv_file_path = target_dir / "labeled_exercises.csv"
    
    sqlite_db_path = target_dir / "fitteum_db.db"
    
    print("가공된 CSV 파일을 불러오는 중...")
    df = pd.read_csv(csv_file_path)
    
    # 데이터베이스 컬럼명 규칙에 맞게 슬래시(/)를 언더바(_)로 치환
    df.columns = [col.replace('/', '_') for col in df.columns]

    # 2. SQLite 데이터베이스 연결 (파일이 없으면 자동으로 새로 만들어집니다!)
    print(f"SQLite 데이터베이스 파일 연결 중: {sqlite_db_path}")
    conn = sqlite3.connect(sqlite_db_path)

    # 3. DB로 데이터 밀어 넣기 (Table Name: bodyweight_exercises)
    table_name = "bodyweight_exercises"
    print(f"SQLite의 '{table_name}' 테이블로 이관을 시작합니다...")
    
    try:
        df.to_sql(
            name=table_name, 
            con=conn, 
            if_exists='replace', 
            index=False          
        )
        print(f"✨ [성공] 총 {len(df)}개의 맨몸 운동 데이터가 SQLite DB에 정상적으로 적재되었습니다.")
        
    except Exception as e:
        print(f"DB 이관 중 에러 발생: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    import_csv_to_sqlite()