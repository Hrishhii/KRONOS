from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# STRICT ONTOLOGY TYPES
NodeType = Literal["Country", "Leader", "Organization", "Asset", "Technology", "Company", "Infrastructure", "MilitaryBase", "Event", "Policy", "ScientificDevelopment"]
EdgeType = Literal["ALLIED_WITH", "IN_CONFLICT_WITH", "SANCTIONS", "EXPORTS", "IMPORTS", "DEPENDS_ON", "LEADS", "INVESTS_IN", "THREATENS", "HOSTS", "TRANSITS_THROUGH", "MEMBER_OF", "PART_OF"]

class GraphNode(BaseModel):
    id: str = Field(description="The unique canonical ID for this node (e.g., 'country_usa', 'leader_modi', 'tech_ai'). Must be snake_case, strictly normalized.")
    label: NodeType = Field(description="The category of the node")
    name: str = Field(description="The human-readable name of the entity")
    cluster: Optional[str] = Field(default=None, description="Optional macro-cluster (e.g., 'Global South', 'NATO', 'Energy Sector')")

class GraphEdge(BaseModel):
    source_id: str = Field(description="The canonical ID of the source node")
    target_id: str = Field(description="The canonical ID of the target node")
    relationship: EdgeType = Field(description="The strict relationship type")
    description: Optional[str] = Field(default=None, description="A brief 1-sentence explanation of why this relationship exists based on the text")

class GraphExtraction(BaseModel):
    nodes: List[GraphNode] = Field(description="All distinct entities found in the text that map to our ontology.")
    edges: List[GraphEdge] = Field(description="All directional relationships between the extracted nodes.")

# Pre-defined aliases for the resolver to ensure correct canonical IDs
GLOBAL_ALIASES = {
    # Countries
    "usa": "country_usa", "united states": "country_usa", "us": "country_usa", "america": "country_usa",
    "china": "country_china", "prc": "country_china",
    "russia": "country_russia", "russian federation": "country_russia",
    "india": "country_india", "bharat": "country_india",
    "taiwan": "country_taiwan", "roc": "country_taiwan",
    "ukraine": "country_ukraine",
    "israel": "country_israel",
    "iran": "country_iran",
    "cuba": "country_cuba",
    
    # Leaders
    "modi": "leader_modi", "narendra modi": "leader_modi", "pm modi": "leader_modi",
    "biden": "leader_biden", "joe biden": "leader_biden",
    "xi": "leader_xi", "xi jinping": "leader_xi",
    "putin": "leader_putin", "vladimir putin": "leader_putin",
    "zelensky": "leader_zelensky", "zelenskyy": "leader_zelensky",
    "trump": "leader_trump", "donald trump": "leader_trump",
    
    # Orgs
    "nato": "org_nato", "north atlantic treaty organization": "org_nato",
    "un": "org_un", "united nations": "org_un",
    "eu": "org_eu", "european union": "org_eu",
    "brics": "org_brics",
    "opec": "org_opec",
    
    # Assets/Tech
    "oil": "asset_oil", "crude oil": "asset_oil", "petroleum": "asset_oil", "oil exports": "asset_oil",
    "lng": "asset_lng", "natural gas": "asset_lng",
    "gold": "asset_gold",
    "semiconductors": "tech_semiconductors", "chips": "tech_semiconductors", "microchips": "tech_semiconductors",
    "ai": "tech_ai", "artificial intelligence": "tech_ai",
    
    # Infrastructure
    "suez canal": "infra_suez_canal", "suez": "infra_suez_canal",
    "panama canal": "infra_panama_canal",
    "strait of hormuz": "infra_hormuz_strait",
    "nord stream": "infra_nord_stream",
    "starlink": "infra_starlink",
    
    # Companies
    "tsmc": "company_tsmc", "taiwan semiconductor": "company_tsmc",
    "nvidia": "company_nvidia",
    "spacex": "company_spacex",
}

def resolve_alias(raw_entity: str, label: str) -> str:
    """Attempt to resolve a raw string to a canonical ID. If unknown, create a safe ID.
    Includes aggressive normalization to merge 'US Sanctions on X' into 'US Sanctions'.
    """
    import re
    clean = raw_entity.lower().strip()
    
    # Check direct aliases first
    if clean in GLOBAL_ALIASES:
        return GLOBAL_ALIASES[clean]
    
    # AGGRESSIVE NORMALIZATION for Policies and Events
    if label in ["Policy", "Event"]:
        # 1. Remove common target/locational suffixes (e.g., 'US Sanctions on Russia' -> 'US Sanctions')
        clean = re.sub(r"\s+(on|in|against|at|for)\s+.*$", "", clean)
        # 2. Standardize 'War in Iran' -> 'Iran War'
        war_match = re.search(r"^war\s+in\s+(.+)$", clean)
        if war_match:
            clean = f"{war_match.group(1)} war"
            
    # Check again after normalization
    if clean in GLOBAL_ALIASES:
        return GLOBAL_ALIASES[clean]
    
    # Fallback safe ID genesis
    safe_name = "".join([c if c.isalnum() else "_" for c in clean])
    while "__" in safe_name: safe_name = safe_name.replace("__", "_")
    return f"{label.lower()}_{safe_name.strip('_')}"
