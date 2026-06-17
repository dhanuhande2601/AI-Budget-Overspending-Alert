import requests
from datetime import datetime, timedelta
 
SUPPORTED_CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'AUD', 'CAD', 'JPY', 'AED']
 
# Simple in-memory cache so we don't hit the exchange rate API on
# every single dashboard load. Refreshes once every 6 hours.
_rate_cache = {
    "base": "INR",
    "rates": {},
    "fetched_at": None,
}
 
CACHE_DURATION = timedelta(hours=6)
 
 
def _is_cache_valid():
    if not _rate_cache["fetched_at"]:
        return False
    return datetime.utcnow() - _rate_cache["fetched_at"] < CACHE_DURATION
 
 
def get_exchange_rates(base="INR"):
    """
    Returns a dict of exchange rates relative to INR, e.g.
    {"INR": 1, "USD": 0.012, "EUR": 0.011, ...}
    Falls back to last cached values (or safe defaults) if the API fails.
    """
    if _is_cache_valid() and _rate_cache["base"] == base:
        return _rate_cache["rates"]
 
    try:
        response = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{base}",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
 
        # Keep only currencies we support, always include base = 1
        filtered_rates = {base: 1.0}
        for currency in SUPPORTED_CURRENCIES:
            if currency in rates:
                filtered_rates[currency] = rates[currency]
 
        _rate_cache["base"] = base
        _rate_cache["rates"] = filtered_rates
        _rate_cache["fetched_at"] = datetime.utcnow()
 
        return filtered_rates
 
    except Exception as error:
        print("Currency API fetch failed:", error)
 
        # Fallback to last known cache, or rough static defaults if cache is empty
        if _rate_cache["rates"]:
            return _rate_cache["rates"]
 
        return {
            "INR": 1.0,
            "USD": 0.012,
            "EUR": 0.011,
            "GBP": 0.0095,
            "AUD": 0.018,
            "CAD": 0.016,
            "JPY": 1.8,
            "AED": 0.044,
        }
 
 
def convert_amount(amount, from_currency, to_currency):
    """Convert an amount from one currency to another using INR as the pivot."""
    if from_currency == to_currency:
        return round(amount, 2)
 
    rates = get_exchange_rates(base="INR")
 
    # Convert amount -> INR -> target currency
    rate_from = rates.get(from_currency, 1.0)
    rate_to = rates.get(to_currency, 1.0)
 
    amount_in_inr = amount / rate_from if rate_from else amount
    converted = amount_in_inr * rate_to
 
    return round(converted, 2)
 