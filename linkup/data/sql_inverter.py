from pathlib import Path
from sqlalchemy import create_engine
import pandas as pd

def import_csv_to_mysql():
    # 1. 가공 완료된 CSV 파일 경로 지정
    target_dir = Path("C:/workspace/Fitteum")
    csv_file_path = target_dir / "labeled_exercises.csv"
    
    print("📖 가공된 CSV 파일을 불러오는 중...")
    df = pd.read_csv(csv_file_path)
    
    # 데이터베이스 컬럼명 규칙에 맞게 슬래시(/)를 언더바(_)로 치환 (선택 사항)
    # 컬럼명에 슬래시가 있으면 SQL 쿼리 보낼 때 에러가 날 수 있어서 미리 안전하게 바꿔줍니다.
    df.columns = [col.replace('/', '_') for col in df.columns]

    # 2. MySQL 데이터베이스 연결 설정 (본인의 DB 정보로 수정하세요)
    db_user = "root"          # DB 아이디
    db_password = "yikyung0327"  # DB 비밀번호
    db_host = "localhost"     # DB 주소 (로컬PC인 경우 localhost)
    db_port = "3306"          # MySQL 기본 포트
    db_name = "fitteum_db"    # 미리 만들어둔 데이터베이스 이름
    
    # SQLAlchemy 엔진 생성
    engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4")

    # 3. DB로 데이터 밀어 넣기 (Table Name: bodyweight_exercises)
    table_name = "bodyweight_exercises"
    print(f"🗄️ MySQL 데이터베이스의 '{table_name}' 테이블로 이관을 시작합니다...")
    
    try:
        df.to_sql(
            name=table_name, 
            con=engine, 
            if_exists='replace', # 만약 테이블이 이미 있으면 지우고 새로 만듭니다 ('append'로 바꾸면 기존 데이터에 누적됨)
            index=False          # 판다스의 index 행은 DB에 넣지 않음
        )
        print(f"총 {len(df)}개의 맨몸 운동 데이터가 SQL DB에 정상적으로 적재되었습니다.")
        
    except Exception as e:
        print(f"❌ DB 이관 중 에러 발생: {e}")

if __name__ == "__main__":
    import_csv_to_mysql()