"""
Döviz kuru endpoint'leri: gerçek zamanlı kurlar, dönüştürme.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from decimal import Decimal
from app.services.currency_service import (
    get_exchange_rates,
    convert_currency,
    get_currency_info,
    SUPPORTED_CURRENCIES,
)

router = APIRouter(prefix="/api/v1/currency", tags=["Currency"])

class ExchangeRateResponse(BaseModel):
    base: str = Field(..., description="Base currency code")
    rates: dict = Field(..., description="Exchange rates")
    timestamp: str = Field(..., description="UTC timestamp")
    source: str = Field(..., description="Rate source (mock, external, fallback)")

class ConvertRequest(BaseModel):
    amount: Decimal = Field(..., description="Amount to convert")
    from_currency: str = Field(..., description="Source currency code")
    to_currency: str = Field(..., description="Target currency code")

class ConvertResponse(BaseModel):
    original_amount: Decimal
    from_currency: str
    to_currency: str
    converted_amount: Decimal
    rate: Decimal

class SupportedCurrenciesResponse(BaseModel):
    currencies: dict

@router.get("/rates", response_model=ExchangeRateResponse, summary="Get exchange rates")
async def get_rates(base: str = "TRY"):
    """
    Güncel döviz kurlarını al.

    - **base**: Base para birimi (default: TRY)
    """
    if base not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen para birimi: {base}"
        )
    return await get_exchange_rates(base)

@router.post("/convert", response_model=ConvertResponse, summary="Convert currency")
async def convert(request: ConvertRequest):
    """
    Bir para biriminden diğerine dönüştür.
    """
    if request.from_currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unknown currency: {request.from_currency}")
    if request.to_currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unknown currency: {request.to_currency}")

    rates_data = await get_exchange_rates(request.from_currency)
    rates = rates_data["rates"]

    if request.to_currency not in rates:
        raise HTTPException(status_code=400, detail=f"No rate available for {request.to_currency}")

    rate = rates[request.to_currency]
    converted = convert_currency(request.amount, request.from_currency, request.to_currency, rate)

    return ConvertResponse(
        original_amount=request.amount,
        from_currency=request.from_currency,
        to_currency=request.to_currency,
        converted_amount=converted,
        rate=rate,
    )

@router.get("/supported", response_model=SupportedCurrenciesResponse, summary="Get supported currencies")
async def get_supported():
    """Desteklenen tüm para birimlerini al"""
    return SupportedCurrenciesResponse(currencies=SUPPORTED_CURRENCIES)
