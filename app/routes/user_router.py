from typing import Any
from fastapi import APIRouter
from app.core.security import get_current_user
import app.schema.common_schema as common_schema
import app.schema.user_schema as user_schema
import app.service.user_service as user_service
import app.config as config
from app.repository.base_user_repository import BaseUserRepository
from app.repository.db.db_user_repository import UserRepositoryDB

from fastapi import Depends
from app.core.database import get_db
from sqlalchemy.orm import Session

def get_user_repository(db:Session = Depends(get_db)):
    return UserRepositoryDB(db)


router = APIRouter(tags=["사용자"], prefix="/user")

@router.post("", response_model=common_schema.ApiResponse)
async def create_user(request: user_schema.UserCreate, repo:BaseUserRepository = Depends(get_user_repository)) -> Any:

    user_service.create_user(repo, request)
    response = common_schema.ApiResponse(success=True, message="회원가입이 성공적으로 완료되었습니다.") 

    return response