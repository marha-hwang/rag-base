from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = HTTPBearer(auto_error=True)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def verify_password(plain_password, hashed_password):
    """평문 비밀번호와 해싱된 비밀번호를 비교"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """비밀번호를 해싱"""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> str:
    """
    보호된 엔드포인트에서 사용될 의존성 (Depends)
    1. 요청 헤더에서 토큰을 추출 (FastAPI가 자동으로 해줌)
    2. 토큰을 디코딩하고 검증
    3. 토큰의 username(sub)을 이용해 DB에서 최신 사용자 정보를 가져옴
    """

    token = credentials.credentials
    print(f"token : {token}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"payload : {payload}")
        return payload['user_id']
    except JWTError:
        raise credentials_exception