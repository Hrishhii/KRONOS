import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME = "AI Global Ontology Engine V2"
    
    # API Keys
    FRED_API_KEY = os.getenv("FRED_API_KEY")
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    NASA_API_KEY = os.getenv("NASA_API_KEY")
    
    # Database Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") # Strictly from environment
    
    # Internal Flags
    OPENSKY_ENABLED = os.getenv("OPENSKY_API_ENABLED", "true").lower() == "true"
    AISHUB_ENABLED = os.getenv("AIS_HUB_API_ENABLED", "true").lower() == "true"

settings = Settings()
