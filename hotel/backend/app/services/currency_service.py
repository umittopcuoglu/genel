"""
Döviz kuru entegrasyonu: Ülke tabanlı döviz kurları gerçek zamanlı gösterimi.
Dış misafirler için alış/satış işlemlerinde güncel kurlar.
"""
import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Cache for exchange rates (expires after 1 hour)
class ExchangeRateCache:
    def __init__(self):
        self.rates: Dict[str, Any] = {}
        self.updated_at: Optional[datetime] = None
        self.ttl_minutes = 60

    def is_valid(self) -> bool:
        if not self.updated_at:
            return False
        age = datetime.utcnow() - self.updated_at
        return age < timedelta(minutes=self.ttl_minutes)

    def set(self, rates: Dict[str, Any]):
        self.rates = rates
        self.updated_at = datetime.utcnow()

    def get(self) -> Optional[Dict[str, Any]]:
        if self.is_valid():
            return self.rates
        return None

_cache = ExchangeRateCache()

# Supported currencies with symbols and countries
SUPPORTED_CURRENCIES = {
    "USD": {"symbol": "$", "country": "United States", "ülke": "Amerika Birleşik Devletleri"},
    "EUR": {"symbol": "€", "country": "European Union", "ülke": "Avrupa Birliği"},
    "GBP": {"symbol": "£", "country": "United Kingdom", "ülke": "Birleşik Krallık"},
    "JPY": {"symbol": "¥", "country": "Japan", "ülke": "Japonya"},
    "CHF": {"symbol": "CHF", "country": "Switzerland", "ülke": "İsviçre"},
    "CAD": {"symbol": "C$", "country": "Canada", "ülke": "Kanada"},
    "AUD": {"symbol": "A$", "country": "Australia", "ülke": "Avustralya"},
    "SEK": {"symbol": "kr", "country": "Sweden", "ülke": "İsveç"},
    "NZD": {"symbol": "NZ$", "country": "New Zealand", "ülke": "Yeni Zelanda"},
    "MXN": {"symbol": "Mex$", "country": "Mexico", "ülke": "Meksika"},
    "SGD": {"symbol": "S$", "country": "Singapore", "ülke": "Singapur"},
    "HKD": {"symbol": "HK$", "country": "Hong Kong", "ülke": "Hong Kong"},
    "NOK": {"symbol": "kr", "country": "Norway", "ülke": "Norveç"},
    "KRW": {"symbol": "₩", "country": "South Korea", "ülke": "Güney Kore"},
    "TRY": {"symbol": "₺", "country": "Turkey", "ülke": "Türkiye"},
    "INR": {"symbol": "₹", "country": "India", "ülke": "Hindistan"},
    "BRL": {"symbol": "R$", "country": "Brazil", "ülke": "Brezilya"},
    "ZAR": {"symbol": "R", "country": "South Africa", "ülke": "Güney Afrika"},
}

async def get_exchange_rates(base_currency: str = "TRY") -> Dict[str, Any]:
    """
    Döviz kurlarını gerçek zamanlı kaynaktan al.
    Mock-first: API kullanılabilir olduğunda gerçek kur, yoksa default değerler.
    """
    # Önce cache kontrol et
    cached = _cache.get()
    if cached:
        return cached

    rates_data = await _fetch_rates(base_currency)
    _cache.set(rates_data)
    return rates_data

async def _fetch_rates(base_currency: str) -> Dict[str, Any]:
    """
    Gerçek kur API'sinden veri al. Şu an mock-first (default kurlar).

    Üretim: exchangerate-api.com, openexchangerates.org, vb. entegrasyon
    """
    try:
        # Mock rates (gerçek API bağlantısı .env ile yapılandırılabilir)
        # DEFAULT: TRY tabanlı, diğer para birimlerine göre
        mock_rates = {
            "TRY": {
                "USD": Decimal("32.50"),  # 1 USD = 32.50 TRY
                "EUR": Decimal("35.20"),  # 1 EUR = 35.20 TRY
                "GBP": Decimal("40.80"),
                "JPY": Decimal("0.22"),
                "CHF": Decimal("36.50"),
                "CAD": Decimal("23.80"),
                "AUD": Decimal("21.30"),
                "SEK": Decimal("3.10"),
                "NZD": Decimal("19.80"),
                "MXN": Decimal("1.90"),
                "SGD": Decimal("24.10"),
                "HKD": Decimal("4.16"),
                "NOK": Decimal("3.10"),
                "KRW": Decimal("0.025"),
                "INR": Decimal("0.39"),
                "BRL": Decimal("6.50"),
                "ZAR": Decimal("1.76"),
            },
            "USD": {
                "TRY": Decimal("0.0308"),
                "EUR": Decimal("0.92"),
                "GBP": Decimal("0.79"),
                "JPY": Decimal("149.00"),
                "CHF": Decimal("0.88"),
                "CAD": Decimal("1.35"),
                "AUD": Decimal("1.51"),
                "SEK": Decimal("10.50"),
                "NZD": Decimal("1.67"),
                "MXN": Decimal("17.00"),
                "SGD": Decimal("1.33"),
                "HKD": Decimal("7.82"),
                "NOK": Decimal("10.50"),
                "KRW": Decimal("1290"),
                "INR": Decimal("83.00"),
                "BRL": Decimal("4.95"),
                "ZAR": Decimal("18.35"),
            },
            "EUR": {
                "TRY": Decimal("0.0284"),
                "USD": Decimal("1.09"),
                "GBP": Decimal("0.86"),
                "JPY": Decimal("161.50"),
                "CHF": Decimal("0.96"),
                "CAD": Decimal("1.47"),
                "AUD": Decimal("1.64"),
                "SEK": Decimal("11.40"),
                "NZD": Decimal("1.82"),
                "MXN": Decimal("18.50"),
                "SGD": Decimal("1.45"),
                "HKD": Decimal("8.50"),
                "NOK": Decimal("11.40"),
                "KRW": Decimal("1400"),
                "INR": Decimal("90.20"),
                "BRL": Decimal("5.38"),
                "ZAR": Decimal("19.93"),
            }
        }

        return {
            "base": base_currency,
            "rates": mock_rates.get(base_currency, mock_rates["TRY"]),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock",  # Gerçek API entegre edilince "external" olur
        }
    except Exception as e:
        logger.error(f"Kur alma hatası: {e}")
        # Fallback: default mock rates
        return {
            "base": base_currency,
            "rates": mock_rates.get(base_currency, mock_rates["TRY"]),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "fallback",
        }

def convert_currency(amount: Decimal, from_currency: str, to_currency: str, rate: Decimal) -> Decimal:
    """
    Para birimi dönüştür.

    Args:
        amount: Dönüştürülecek miktar
        from_currency: Kaynak para birimi
        to_currency: Hedef para birimi
        rate: Döviz kuru

    Returns:
        Dönüştürülen miktar
    """
    if from_currency == to_currency:
        return amount
    return (amount * rate).quantize(Decimal("0.01"))

def get_currency_info(currency_code: str) -> Dict[str, Any]:
    """Para birimi bilgisini al"""
    return SUPPORTED_CURRENCIES.get(currency_code, {})
