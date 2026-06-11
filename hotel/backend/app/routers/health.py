"""
Sağlık kontrolü endpoint'i.
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health", summary="Sağlık kontrolü", description="Sistemin çalışıp çalışmadığını kontrol eder. Kimlik doğrulama gerektirmez.")
async def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok"}
    )
