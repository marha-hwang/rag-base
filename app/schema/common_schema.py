from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success:bool = Field(default=None, description="응답상태")
    code:str = Field(default=None, description="응답 코드")
    message:str = Field(default=None, description="응답 메시지")
    data: T | None = Field(default=None, description="응답 데이터 페이로드")
