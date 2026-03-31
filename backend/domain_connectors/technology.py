import asyncio
import httpx
from datetime import datetime, timezone
import logging

from backend.schemas import NormalizedRecord

logger = logging.getLogger(__name__)

async def fetch_github_data(country: str) -> list[NormalizedRecord]:
    """
    Fetches trending/searched repositories on GitHub based on country topic.
    """
    url = "https://api.github.com/search/repositories"
    params = {
        "q": country,
        "sort": "stars",
        "order": "desc",
        "per_page": 5
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GlobalOntologyEngine/1.0"
    }
    
    records = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            for item in items:
                # Use current time as retrieval time
                dt = datetime.now(timezone.utc)
                
                records.append(NormalizedRecord(
                    domain="technology",
                    source="GitHub",
                    entity=country,
                    data_type="repo",
                    title_or_label=item.get("full_name", "Unknown Repo"),
                    value=f"{item.get('stargazers_count', 0)} stars",
                    timestamp=dt.isoformat(),
                    raw_reference=item.get("html_url", "")
                ))
    except Exception as e:
        logger.error(f"GitHub fetch failed: {e}")
        raise e
        
    return records

async def fetch_hackernews_data(topic: str) -> list[NormalizedRecord]:
    """
    Fetches latest stories from HackerNews Algolia Search API matching the topic.
    """
    import urllib.parse
    query = urllib.parse.quote(topic)
    url = f"https://hn.algolia.com/api/v1/search_by_date?query={query}&tags=story&hitsPerPage=5"
    
    records = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            for hit in data.get("hits", []):
                dt_str = hit.get("created_at")
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00")) if dt_str else datetime.now(timezone.utc)
                except Exception:
                    dt = datetime.now(timezone.utc)
                    
                records.append(NormalizedRecord(
                    domain="technology",
                    source="HackerNews",
                    entity=topic,
                    data_type="post",
                    title_or_label=hit.get("title", "No Title"),
                    value=f"Points: {hit.get('points', 0)}",
                    timestamp=dt.isoformat(),
                    raw_reference=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                ))
    except Exception as e:
        logger.error(f"HackerNews Algolia fetch failed: {e}")
        raise e
        
    return records

async def fetch_nasa_apod_data() -> list[NormalizedRecord]:
    """
    Fetches the Astronomy Picture of the Day from NASA.
    """
    from backend.config import settings
    
    # Use the key from settings or default to DEMO_KEY
    api_key = settings.NASA_API_KEY or "DEMO_KEY"
    url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
    
    records = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            dt_str = data.get("date")
            try:
                dt = datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception:
                dt = datetime.now(timezone.utc)
                
            
            exp_val = data.get("explanation", "No Explanation")
            val_str = str(exp_val) if exp_val else "No Explanation"
            val_str = val_str[:300] + "..." if len(val_str) > 300 else val_str
            
            records.append(NormalizedRecord(
                domain="technology",
                source="NASA_APOD",
                entity="Space",
                data_type="image",
                title_or_label=data.get("title", "No Title"),
                value=val_str,
                timestamp=dt.isoformat(),
                raw_reference=data.get("url", "")
            ))
    except Exception as e:
        logger.error(f"NASA APOD fetch failed: {e}")
        
    return records
