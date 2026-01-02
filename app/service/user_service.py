import app.schema.user_schema as user_schema
import app.model.models as app_models
import app.core.security as security
from app.repository.base_user_repository import BaseUserRepository
import logging
from app.core.exception import CustomException, ErrorCode

logger = logging.getLogger(__name__)

def create_user(repo:BaseUserRepository, data:user_schema.UserCreate) :

    hashedPassword = security.get_password_hash(data.password)
    user = app_models.User(
        user_id=data.user_id,
        password=hashedPassword,
        nickname=data.nickname,
        img_id=data.img_id
    )
    try :
        repo.insert_user(user)
    except Exception as e:
        logger.error("error", exc_info=True)
        raise CustomException(code=ErrorCode.INVALID_INPUT_VALUE, message="회원가입에 실패하였습니다.")

