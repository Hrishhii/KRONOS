from typing import Dict, List, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field

class AggregationRequest(BaseModel):
    query: str = Field(description="The natural language query to parse and aggregate data for")

class NormalizedRecord(BaseModel):
    domain: Literal["geopolitics", "economics", "climate", "technology", "society", "context", "space"]
    source: str
    entity: str
    data_type: str
    title_or_label: str
    value: str | float | int | None
    timestamp: str  # ISO 8601 string
    raw_reference: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class ExtractedSignal(BaseModel):
    reasoning: str = Field(description="Step-by-step reasoning explaining exactly why this signal is highly relevant to the user's original query")
    entity: str = Field(description="The exact entity (e.g., country, ticker) this data belongs to")
    event_or_indicator: str = Field(description="The main event, metric, or indicator extracted")
    value: str | float | int | None = Field(default=None, description="Quantitative value if applicable (e.g. for economics)")
    source: str = Field(description="Source of the data")
    context: str | None = Field(default=None, description="Context retrieved from Tavily search")

class ExtractedSignalsDomains(BaseModel):
    geopolitics: List[ExtractedSignal] = Field(default_factory=list)
    economics: List[ExtractedSignal] = Field(default_factory=list)
    climate: List[ExtractedSignal] = Field(default_factory=list)
    technology: List[ExtractedSignal] = Field(default_factory=list)
    society: List[ExtractedSignal] = Field(default_factory=list)

class QueryPlan(BaseModel):
    primary_entity: str = Field(description="The main country or entity mentioned in the query")
    related_entities: List[str] = Field(description="Other entities or countries mentioned")
    domains: List[Literal["geopolitics", "economics", "climate", "technology", "society"]] = Field(description="Domains relevant to the query")
    topics: List[str] = Field(description="Specific topics or keywords extracted from the query")
    time_range: str = Field(default="recent", description="Time range for data retrieval")

class SourceAttribution(BaseModel):
    """Tracks which APIs provided data for transparency"""
    source_name: str = Field(description="Name of the API/source (e.g., NewsAPI, FRED, OpenWeatherMap)")
    domain: str = Field(description="Domain category (geopolitics, economics, climate, technology, space)")
    data_points: int = Field(description="Number of data points retrieved")
    status: str = Field(description="Success, NO_DATA, or FAIL")

class AggregationResponse(BaseModel):
    query: str
    domains_triggered: List[str]
    retrieved_at: datetime
    signals: ExtractedSignalsDomains
    api_status: Dict[str, Any]
    insight: str | None = Field(default=None, description="The final text synthesis and reasoning over all extracted domain data")
    sources_used: List[SourceAttribution] = Field(default_factory=list, description="Complete transparency: which sources provided data")
    data_quality_summary: str | None = Field(default=None, description="Brief assessment of data completeness and reliability")
