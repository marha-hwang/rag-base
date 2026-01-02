from pydantic import BaseModel


#1. Payload 1: 회원 가입 (모든 정보 포함)
# user_id, password, nickname, img_id
class UserCreate(BaseModel):
    user_id: str
    password: str
    nickname: str
    img_id: str