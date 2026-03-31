import logging
from datetime import datetime, timezone
from tavily import AsyncTavilyClient
from backend.schemas import NormalizedRecord
from backend.config import settings

logger = logging.getLogger(__name__)

async def fetch_tavily_data(query: str) -> list[NormalizedRecord]:
    """
    Fetches universal background context using the Tavily Search API.
    Used to ground the specialized domain metrics with broad, real-world narrative.
    """
    if not settings.TAVILY_API_KEY or settings.TAVILY_API_KEY == "your_tavily_api_key":
        logger.warning("TAVILY_API_KEY is missing. Broad context will be skipped.")
        return []

    records = []
    try:
        tavily_client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
        
        # We request a short answer to serve as precise context, plus top 3 results
        response = await tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=True
        )
        
        dt = datetime.now(timezone.utc).isoformat()
        
        # If Tavily synthesized an answer, use it as the primary context paragraph
        answer = response.get("answer")
        if answer:
            records.append(NormalizedRecord(
                domain="context",
                source="Tavily",
                entity="Global Context",
                data_type="summary",
                title_or_label="Background Synthesis",
                value=answer,
                timestamp=dt,
                raw_reference="Tavily Answer"
            ))
            
        # Also include the top 3 results for granular entity verification
        for result in response.get("results", []):
            records.append(NormalizedRecord(
                domain="context",
                source="Tavily",
                entity="Global Context",
                data_type="search_result",
                title_or_label=result.get("title", "No Title"),
                value=result.get("content", ""),
                timestamp=dt,
                raw_reference=result.get("url", "")
            ))
            
    except Exception as e:
        logger.error(f"Tavily fetch failed: {e}")
        raise e
        
    return records
