import httpx
from datetime import datetime, timezone
import logging
import feedparser
import urllib.parse

from backend.schemas import NormalizedRecord
from backend.config import settings

logger = logging.getLogger(__name__)

async def fetch_gdelt_data(country: str, timeframe: str = "recent") -> list[NormalizedRecord]:
    """
    Fetches recent news events related to the country from GDELT.
    """
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    
    # Timespan mapping: 'today'=24h, 'recent'=72h, '7d'=7d, '30d'=30d
    search_query = country
    if timeframe.isdigit() and len(timeframe) == 4:
        search_query = f'"{country}"'
        sort_order = "relevance"
        timespan = None
    elif timeframe in ["today", "1d", "24h", "now"]:
        timespan = "24h"
        sort_order = "datedesc"
    elif timeframe in ["recent", "current"]:
        timespan = "72h"   # 3 days — enough for meaningful coverage period
        sort_order = "datedesc"
    elif timeframe == "30d":
        timespan = "30d"
        sort_order = "datedesc"
    else:
        timespan = "7d"
        sort_order = "datedesc"

    params = {
        "query": search_query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": 10,   # increased from 5 for better clustering material
        "sort": sort_order
    }
    if timespan:
        params["timespan"] = timespan
    records = []
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = data.get("articles", [])
            for article in articles:
                # GDELT returns dates like "20260303T000000Z" (sometimes) or we can just use now
                # We'll use the current time for simplicity if we can't parse it
                date_str = str(article.get("seendate", ""))
                try:
                    if len(date_str) == 15 and date_str.endswith("Z"):
                        dt = datetime.strptime(date_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                    else:
                        dt = datetime.now(timezone.utc)
                except Exception:
                    dt = datetime.now(timezone.utc)
                
                records.append(NormalizedRecord(
                    domain="geopolitics",
                    source="GDELT",
                    entity=country,
                    data_type="event",
                    title_or_label=article.get("title", "No Title"),
                    value=article.get("domain", "Unknown Domain"), # using domain as string value
                    timestamp=dt.isoformat(),
                    raw_reference=article.get("url", "")
                ))
    except Exception as e:
        logger.error(f"GDELT fetch failed: {e}")
        raise e
        
    return records

async def fetch_newsapi_data(country: str, timeframe: str = "recent") -> list[NormalizedRecord]:
    """
    Fetches breaking news headlines related to the country from NewsAPI.
    """
    if not settings.NEWSAPI_KEY or settings.NEWSAPI_KEY == "your_newsapi_key":
        raise ValueError("NEWSAPI_KEY is missing or invalid")

    url = "https://newsapi.org/v2/everything"
    
    query = country
    from_date = None
    if timeframe.isdigit() and len(timeframe) == 4:
        query = f"{country} {timeframe}"
    elif timeframe in ["today", "1d", "24h"]:
        from datetime import timedelta
        from_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif timeframe in ["recent", "current", "now"]:
        from datetime import timedelta
        from_date = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif timeframe == "7d":
        from datetime import timedelta
        from_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif timeframe == "30d":
        from datetime import timedelta
        from_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": 10,     # increased from 5 for better clustering material
        "apiKey": settings.NEWSAPI_KEY
    }
    if from_date:
        params["from"] = from_date
    
    records = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = data.get("articles", [])
            for article in articles:
                dt_str = article.get("publishedAt")
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00")) if dt_str else datetime.now(timezone.utc)
                except Exception:
                    dt = datetime.now(timezone.utc)
                
                records.append(NormalizedRecord(
                    domain="geopolitics",
                    source="NewsAPI",
                    entity=country,
                    data_type="headline",
                    title_or_label=article.get("title", "No Title"),
                    value=article.get("source", {}).get("name", "Unknown Source"),
                    timestamp=dt.isoformat(),
                    raw_reference=article.get("url", "")
                ))
    except Exception as e:
        logger.error(f"NewsAPI fetch failed: {e}")
        raise e
        
    return records

async def fetch_googlenews_data(entity: str, timeframe: str = "recent") -> list[NormalizedRecord]:
    """
    Fetches breaking news from Google News RSS using async httpx (fixes blocking feedparser.parse(url) issue).
    """
    query_str = entity
    if timeframe in ["today", "1d", "24h", "now", "current", "recent"]:
        query_str += " when:1d"
    elif timeframe == "7d":
        query_str += " when:7d"
    elif timeframe.isdigit() and len(timeframe) == 4:
        query_str += f" {timeframe}"

    query = urllib.parse.quote(query_str)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    records = []
    try:
        # Use httpx for async fetch — feedparser.parse(url) is synchronous/blocking
        # and silently fails in async contexts
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            raw_xml = resp.text

        # Now parse the XML in-memory (no network call, just parsing)
        feed = feedparser.parse(raw_xml)

        if not feed.entries:
            logger.warning(f"Google News RSS returned 0 entries for '{entity}'")
            return []

        for article in feed.entries[:8]:
            dt_str = getattr(article, "published", None)
            try:
                if dt_str:
                    dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
                else:
                    dt = datetime.now(timezone.utc)
            except Exception:
                dt = datetime.now(timezone.utc)

            full_title = article.get("title", "No Title")
            title_parts = full_title.rsplit(" - ", 1)
            title = title_parts[0].strip()
            source = title_parts[1].strip() if len(title_parts) > 1 else "Google News"

            records.append(NormalizedRecord(
                domain="geopolitics",
                source="GoogleNews",
                entity=entity,
                data_type="headline",
                title_or_label=title,
                value=source,
                timestamp=dt.isoformat(),
                raw_reference=article.get("link", "")
            ))

    except Exception as e:
        logger.error(f"Google News RSS fetch failed for '{entity}': {e}")
        # Don't re-raise — let other sources still succeed

    return records

