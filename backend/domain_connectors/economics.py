import httpx
import yfinance as yf
from datetime import datetime, timezone
import logging

from backend.config import settings
from backend.schemas import NormalizedRecord

logger = logging.getLogger(__name__)

# Map countries to major ETF or index tickers for Yahoo Finance representation
TICKER_MAP = {
    "india": "^BSESN", # BSE SENSEX
    "united states": "^GSPC", # S&P 500
    "uk": "^FTSE", # FTSE 100
    "united kingdom": "^FTSE",
    "canada": "^GSPTSE", # S&P/TSX
    "australia": "^AXJO", # S&P/ASX 200
    "japan": "^N225", # Nikkei 225
    "china": "000001.SS", # SSE Composite
    "brazil": "^BVSP", # Bovespa
    "mexico": "^MXX", # IPC
    "south korea": "^KS11", # KOSPI
}

async def fetch_fred_data() -> list[NormalizedRecord]:
    """
    Fetches latest interest rate from FRED (FEDFUNDS).
    """
    if not settings.FRED_API_KEY or settings.FRED_API_KEY == "your_fred_api_key":
        raise ValueError("FRED_API_KEY is missing or invalid")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "FEDFUNDS",
        "api_key": settings.FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1
    }
    
    records = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            observations = data.get("observations", [])
            for obs in observations:
                records.append(NormalizedRecord(
                    domain="economics",
                    source="FRED",
                    entity="United States",
                    data_type="indicator",
                    title_or_label="Federal Funds Effective Rate",
                    value=float(obs.get("value", 0.0)),
                    timestamp=datetime.strptime(obs.get("date"), "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat(),
                    raw_reference="FEDFUNDS"
                ))
    except Exception as e:
        logger.error(f"FRED fetch failed: {e}")
        raise e
        
    return records

async def fetch_yahoo_finance_data(ticker_or_country: str) -> list[NormalizedRecord]:
    """
    Fetches market data for a Yahoo Finance ticker symbol or country name.
    New: accepts raw ticker symbols directly (e.g. '^GSPC', 'CL=F', 'GC=F').
    Falls back to TICKER_MAP for country name inputs.
    """
    import asyncio

    # If it's a recognized country name, map it to the default index
    raw = ticker_or_country.strip()
    if raw.lower() in TICKER_MAP:
        ticker_symbol = TICKER_MAP[raw.lower()]
        entity_label = ticker_or_country
    else:
        # Assume it's a direct ticker (e.g., UPL.NS, SMH, CL=F, ^GSPC)
        ticker_symbol = raw
        entity_label = raw

    records = []
    try:
        # yfinance is synchronous — run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        def _fetch():
            import yfinance as yf
            try:
                t = yf.Ticker(ticker_symbol)
                # Use a larger period for cryptos as they often have missing gaps in '5d'
                hist = t.history(period="1wk")
                if hist.empty or "Close" not in hist.columns:
                    logger.warning(f"YahooFinance: Empty or malformed data for '{ticker_symbol}'")
                    return None
                    
                latest = hist.iloc[-1]
                if latest.get("Close") is None:
                    return None
                    
                pct_change = 0.0
                if len(hist) >= 2:
                    prev = hist.iloc[-2]
                    if prev.get("Close") and prev["Close"] > 0:
                        pct_change = ((latest["Close"] - prev["Close"]) / prev["Close"]) * 100
                        
                dt = latest.name.to_pydatetime().replace(tzinfo=timezone.utc)
                return {
                    "close": float(latest["Close"]),
                    "pct_change": float(pct_change),
                    "volume": int(latest["Volume"]) if "Volume" in latest and latest["Volume"] else None,
                    "dt": dt,
                }
            except Exception as inner_e:
                logger.error(f"Internal YahooFinance fetch error for '{ticker_symbol}': {inner_e}")
                return None
        data = await loop.run_in_executor(None, _fetch)
        if data:
            label = ticker_symbol
            records.append(NormalizedRecord(
                domain="economics",
                source="YahooFinance",
                entity=entity_label,
                data_type="market",
                title_or_label=f"{label} (close)",
                value=data["close"],
                timestamp=data["dt"].isoformat(),
                metadata={"pct_change": data["pct_change"]},
                raw_reference=ticker_symbol,
            ))
    except Exception as e:
        logger.error(f"YahooFinance fetch failed for '{ticker_or_country}': {e}")
        raise e

    return records

