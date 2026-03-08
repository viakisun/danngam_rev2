"""단감(DAN-GAM) FastAPI 애플리케이션 엔트리포인트."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리."""
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="농작업 O2O 매칭 플랫폼 단감(DAN-GAM) API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """예기치 않은 예외를 처리하는 전역 핸들러."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "DNNG-SYS-500",
                "message": "서버 내부 오류가 발생했습니다.",
            },
        },
    )


# 헬스체크
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """서비스 상태 확인."""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        },
        "error": None,
    }


# 라우터 등록
from app.routers import admin, auth, chat, drying, jobs, notifications, payments, reviews, users

app.include_router(auth.router, prefix="/api/v1", tags=["M01 AUTH"])
app.include_router(users.router, prefix="/api/v1", tags=["M02 USER"])
app.include_router(jobs.router, prefix="/api/v1", tags=["M03 MATCHING"])
app.include_router(drying.router, prefix="/api/v1", tags=["M04 DRYING"])
app.include_router(chat.router, prefix="/api/v1", tags=["M05 CHAT"])
app.include_router(notifications.router, prefix="/api/v1", tags=["M06 NOTIFY"])
app.include_router(reviews.router, prefix="/api/v1", tags=["M07 REVIEW"])
app.include_router(payments.router, prefix="/api/v1", tags=["M08 PAYMENT"])
app.include_router(admin.router, prefix="/api/v1", tags=["M09 ADMIN"])
