from abc import ABC, abstractmethod
from app.model.models import User

class BaseUserRepository(ABC):
    @abstractmethod
    def insert_user(self, user: User):
        pass
