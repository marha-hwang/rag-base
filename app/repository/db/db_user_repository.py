from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
import logging
import app.model.models as models
from app.repository.base_user_repository import BaseUserRepository
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class UserRepositoryDB(BaseUserRepository):
    def __init__(self, db:Session):
        super().__init__()
        self.db=db

    def insert_user(self, user: models.User) :
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user) # DB에서 생성된 값(default 등)을 인스턴스에 반영