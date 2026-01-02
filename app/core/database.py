from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MariaDB 연결 URL
user = "user"
password = "user" # 특수문자 포함 시
host = "localhost" # Docker라면 'host.docker.internal' 또는 서비스명
db_name = "backend"
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:3306/{db_name}"

# 연결 옵션 추가
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 체크
    pool_recycle=3600,   # 1시간마다 연결 재생성
    echo=True            # SQL 쿼리 로깅 (개발 시에만 True)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()