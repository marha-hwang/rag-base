from fastapi import FastAPI, Request, status
from .config import server_config
from fastapi import APIRouter
from app.routes import user_router
import logging
from fastapi.exceptions import RequestValidationError
import app.schema.common_schema as common_schema
from fastapi.responses import JSONResponse
from app.core.exception import CustomException, ErrorCode
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

app = FastAPI(title="Backend + AI Server")

logging.basicConfig(
    level=logging.INFO,  # 로그 레벨을 INFO로 설정
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 기본 에러처리
@app.exception_handler(Exception)
async def default_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    print(f"🚨 500 Internal Server Error: {error_msg}")

    response = common_schema.ApiResponse(success=False, 
                                         code=ErrorCode.INTERNAL_SERVER_ERROR, 
                                         message="서버 내부 오류가 발생했습니다.")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump()
    )

# 요청데이터가 pydantic검증에 실패하는 경우
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(str(exc.errors))
    error_msg = str(exc)
    print(f" Error: {error_msg}")
    for error in exc.errors():
        msg = error["msg"].replace("Value error, ", "")

    response = common_schema.ApiResponse(success=False, 
                                         code=ErrorCode.INVALID_INPUT_VALUE, 
                                         message=msg)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response.model_dump()
    )

@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    error_msg = str(exc)
    print(f" Error: {error_msg}")
    response = common_schema.ApiResponse(success=False, 
                                         code=exc.code, 
                                         message=exc.message)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response.model_dump()
    )

@app.get("/")
async def root():
    return {"message": "AI Model Server is running 🚀"}

# CORS 설정
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


api_router = APIRouter()
api_router.include_router(router=user_router.router)

app.include_router(api_router)