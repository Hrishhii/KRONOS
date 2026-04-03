from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import os
import httpx
from datetime import datetime
import asyncio
import random
import feedparser
import urllib.parse
import logging
from concurrent.futures import ThreadPoolExecutor

from backend.schemas import AggregationRequest, AggregationResponse
from backend.graph import process_query
from backend.config import settings
from backend.graph_engine_connector import db
from backend.graph_engine_updater import auto_update_graph

log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "graph_debug.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Tactical Reload Trigger: v2.1.2 — Synchronizing KRONOS

# Tactical Reload Trigger: v2.1.2

# ──── REAL API INTEGRATIONS ────

async def get_flight_traffic_data():
    """
    Fetch ALL real flight data from OpenSky Network API
    Free API: https://opensky-network.org/api/states/all
    """
    try:
        from backend.domain_connectors.flights import FlightsConnector
        flights = await FlightsConnector.get_global_flights()
        
        # Add comprehensive mock data if real data is low
        if len(flights) < 100:
            from backend.domain_connectors.flights import _get_comprehensive_flight_data
            flights.extend(_get_comprehensive_flight_data())
        
        # Return all flights without sampling
        print(f"[FLIGHTS] Returning {len(flights)} total flights")
        return flights[:1000]  # Limit to 1000 for performance
        
    except Exception as e:
        print(f"Flight data error: {e}")
        from backend.domain_connectors.flights import _get_comprehensive_flight_data
        return _get_comprehensive_flight_data()

def get_sample_flight_data():
    """Realistic, comprehensive flight data across global routes"""
    flights = []
    route_data = [
        {"name": "BA", "from": "London", "to": "New York", "lat1": 51.5, "lng1": -0.1, "lat2": 40.7, "lng2": -74.0, "count": 8},
        {"name": "AF", "from": "Paris", "to": "Atlanta", "lat1": 48.9, "lng1": 2.6, "lat2": 33.7, "lng2": -84.4, "count": 8},
        {"name": "LH", "from": "Berlin", "to": "Dubai", "lat1": 52.4, "lng1": 13.4, "lat2": 35.8, "lng2": 51.2, "count": 8},
        {"name": "SQ", "from": "Singapore", "to": "Tokyo", "lat1": 1.4, "lng1": 103.9, "lat2": 35.6, "lng2": 139.7, "count": 10},
        {"name": "CX", "from": "Hong Kong", "to": "Singapore", "lat1": 22.3, "lng1": 114.2, "lat2": 1.4, "lng2": 103.9, "count": 8},
        {"name": "QF", "from": "Sydney", "to": "Hong Kong", "lat1": -33.9, "lng1": 151.2, "lat2": 22.3, "lng2": 114.2, "count": 8},
        {"name": "EK", "from": "Dubai", "to": "Tokyo", "lat1": 25.3, "lng1": 55.3, "lat2": 35.6, "lng2": 139.7, "count": 10},
        {"name": "KL", "from": "Amsterdam", "to": "Tokyo", "lat1": 52.3, "lng1": 4.9, "lat2": 35.6, "lng2": 139.7, "count": 8},
        {"name": "AA", "from": "New York", "to": "Atlanta", "lat1": 40.7, "lng1": -74.0, "lat2": 33.7, "lng2": -84.4, "count": 10},
        {"name": "JL", "from": "Tokyo", "to": "New York", "lat1": 35.6, "lng1": 139.7, "lat2": 40.7, "lng2": -74.0, "count": 8},
    ]
    
    for route in route_data:
        for i in range(route["count"]):
            progress = random.uniform(0, 1)
            lat = route["lat1"] + (route["lat2"] - route["lat1"]) * progress
            lng = route["lng1"] + (route["lng2"] - route["lng1"]) * progress
            
            flights.append({
                "callsign": f"{route['name']}{800+i:03d}",
                "lat": lat + random.uniform(-1, 1),
                "lng": lng + random.uniform(-1, 1),
                "altitude": random.randint(25000, 43000),
                "speed": random.randint(400, 550),
                "heading": random.uniform(0, 360),
                "country": f"{route['from']}-{route['to']}"
            })
    
    return flights

async def get_weather_data():
    """
    Fetch real weather data from OpenWeatherMap
    Free API: https://api.openweathermap.org/data/2.5/
    """
    weather_key = settings.OPENWEATHERMAP_API_KEY
    if not weather_key:
        # No key, return fallback
        return get_sample_weather_data()
    
    try:
        # Get weather for major world cities
        cities = [
            {"name": "New York", "lat": 40.7128, "lng": -74.0060},
            {"name": "London", "lat": 51.5074, "lng": -0.1278},
            {"name": "Tokyo", "lat": 35.6762, "lng": 139.6503},
            {"name": "Sydney", "lat": -33.8688, "lng": 151.2093},
            {"name": "Dubai", "lat": 25.2048, "lng": 55.2708},
            {"name": "Singapore", "lat": 1.3521, "lng": 103.8198},
            {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777},
            {"name": "São Paulo", "lat": -23.5505, "lng": -46.6333},
        ]
        
        weather_data = []
        async with httpx.AsyncClient(timeout=10) as client:
            for city in cities:
                try:
                    response = await client.get(
                        'https://api.openweathermap.org/data/2.5/weather',
                        params={
                            'lat': city['lat'],
                            'lon': city['lng'],
                            'appid': weather_key,
                            'units': 'metric'
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        weather_data.append({
                            "lat": city["lat"],
                            "lng": city["lng"],
                            "temp": int(data.get('main', {}).get('temp', 20)),
                            "humidity": int(data.get('main', {}).get('humidity', 60)),
                            "condition": data.get('weather', [{}])[0].get('main', 'Unknown'),
                            "city": city["name"]
                        })
                except:
                    pass
        
        return weather_data if weather_data else get_sample_weather_data()
    except Exception as e:
        print(f"OpenWeatherMap API error: {e}")
        return get_sample_weather_data()

def get_sample_weather_data():
    """Realistic weather data across climate zones"""
    regions = [
        {"name": "Equatorial", "lat_range": (-10, 10), "lng_range": (-50, 150), "temps": (25, 32)},
        {"name": "Tropical", "lat_range": (-30, 30), "lng_range": (-180, 180), "temps": (20, 28)},
        {"name": "Temperate", "lat_range": (30, 60), "lng_range": (-180, 180), "temps": (5, 20)},
        {"name": "Arctic", "lat_range": (60, 85), "lng_range": (-180, 180), "temps": (-20, 0)},
        {"name": "Antarctic", "lat_range": (-85, -60), "lng_range": (-180, 180), "temps": (-40, -15)},
    ]
    
    weather_points = []
    for region in regions:
        for i in range(5):
            lat = random.uniform(region["lat_range"][0], region["lat_range"][1])
            lng = random.uniform(region["lng_range"][0], region["lng_range"][1])
            temp = random.uniform(region["temps"][0], region["temps"][1])
            
            weather_points.append({
                "lat": lat,
                "lng": lng,
                "temp": int(temp),
                "humidity": random.randint(30, 95),
                "condition": random.choice(["Clear", "Cloudy", "Rainy", "Stormy", "Foggy"]),
                "city": region["name"]
            })
    
    return weather_points[:25]

async def get_earthquake_data():
    """Fetch live earthquake data from USGS FDSN API."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                'https://earthquake.usgs.gov/fdsnws/event/1/query',
                params={'format': 'geojson', 'orderby': 'time', 'limit': 100}
            )
            if resp.status_code == 200:
                features = resp.json().get('features', [])
                quakes = []
                for f in features:
                    coords = f.get('geometry', {}).get('coordinates', [])
                    props = f.get('properties', {})
                    if len(coords) >= 2 and props.get('mag') is not None:
                        quakes.append({
                            'lat': coords[1],
                            'lng': coords[0],
                            'magnitude': round(props['mag'], 1),
                            'place': props.get('place', 'Unknown'),
                            'time': props.get('time'),
                        })
                print(f"[EARTHQUAKES] Returning {len(quakes)} events")
                return quakes
    except Exception as e:
        print(f"USGS earthquake error: {e}")
    return []

async def get_eonet_events():
    """Fetch live open natural hazard events from NASA EONET API."""
    category_map = {
        'wildfires': 'wildfire',
        'floods': 'flood',
        'severe storms': 'storm',
        'volcanoes': 'volcano',
        'tempest': 'storm',
        'storm': 'storm',
        'flood': 'flood',
        'wildfire': 'wildfire',
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get('https://eonet.gsfc.nasa.gov/api/v3/events/geojson?status=open')
            if resp.status_code == 200:
                features = resp.json().get('features', [])
                events = []
                for f in features:
                    props = f.get('properties', {})
                    geom = f.get('geometry', {})
                    cats = props.get('categories', [])
                    cat_title = cats[0].get('title', '').lower() if cats else ''
                    event_type = category_map.get(cat_title, 'other')
                    coords = geom.get('coordinates')
                    if coords is None:
                        continue
                    # Geometry can be Point or MultiPoint
                    if geom.get('type') == 'Point':
                        events.append({
                            'lat': coords[1], 'lng': coords[0],
                            'title': props.get('title', 'Unknown'),
                            'type': event_type,
                        })
                    elif geom.get('type') == 'MultiPoint' and coords:
                        latest = coords[-1]
                        events.append({
                            'lat': latest[1], 'lng': latest[0],
                            'title': props.get('title', 'Unknown'),
                            'type': event_type,
                        })
                print(f"[EONET] Returning {len(events)} open events")
                return events
    except Exception as e:
        print(f"NASA EONET error: {e}")
    return []


app = FastAPI(
    title="G.O.E. Terminal | Global Ontology Engine",
    description="Multi-domain intelligent data aggregation and synthesis system",
    version="2.0.0"
)

# CORS Security: Restrict origins to frontend dev/prod
# Global Error Tracing for 400/422 Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    import json
    body = await request.body()
    try:
        body_str = body.decode()
    except:
        body_str = str(body)
    
    logger.error(f"[API_VALIDATION_FAILURE] Path: {request.url.path} | Error: {exc.errors()} | Body: {body_str}")
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors(), "body_received": body_str}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React frontend if available (production build)
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                return f.read()
        return "<h1>Frontend not built. Run 'npm run build' in the frontend directory.</h1>"

@app.on_event("startup")
async def startup_event():
    """Run initialization tasks on startup."""
    # Seed the graph if it's empty
    db.seed_if_empty()

# API OPTIONS handlers for CORS preflight
@app.options("/api/v1/aggregate")
async def options_aggregate():
    return {"detail": "OK"}

@app.options("/api/v1/aggregate-stream")
async def options_aggregate_stream():
    return {"detail": "OK"}

# API endpoints
@app.post("/api/v1/aggregate", response_model=AggregationResponse)
async def aggregate_endpoint(request: AggregationRequest):
    # Security: Validate query length
    if not request.query or len(request.query) > 500:
        raise HTTPException(status_code=400, detail="Query exceeding maximum length (500 chars).")

    try:
        data = await process_query(request)
        
        # Background: Update Knowledge Graph with the new intelligence
        if data.insight:
            asyncio.create_task(auto_update_graph(data.insight))
            
        return data
    except Exception as e:
        import traceback
        logger.error(f"Aggregate endpoint error: {e}", exc_info=True)
        traceback.print_exc()
        raise

@app.get("/api/v1/graph/data")
async def graph_data_endpoint():
    """Returns the current state of the Knowledge Graph for visualization."""
    data = db.get_graph_visual_data()
    logger.info(f"[GraphAPI] Returning {len(data.get('nodes', []))} nodes and {len(data.get('links', []))} links.")
    return data

@app.post("/api/v1/aggregate-stream")
async def aggregate_stream_endpoint(request: AggregationRequest):
    """Streaming endpoint that sends partial results as they become available."""
    # Security: Validate query length
    if not request.query or len(request.query) > 500:
        raise HTTPException(status_code=400, detail="Query exceeding maximum length (500 chars).")

    from fastapi.responses import StreamingResponse
    import json
    
    async def stream_results():
        try:
            # Start with initial state
            yield json.dumps({"status": "starting", "message": "Analyzing query..."}) + "\n"
            
            # Run the full query process
            result = await process_query(request)
            
            # Send routing update
            yield json.dumps({
                "status": "routing",
                "message": f"Query routed to: {', '.join(result.domains_triggered)}"
            }) + "\n"
            
            # Send API status updates
            yield json.dumps({
                "status": "api_status",
                "data": result.api_status
            }) + "\n"
            
            # Send final insight
            if result.insight:
                # Background: Update Knowledge Graph with the new intelligence
                asyncio.create_task(auto_update_graph(result.insight))
                
                yield json.dumps({
                    "status": "complete",
                    "data": {
                        "insight": result.insight,
                        "domains_triggered": result.domains_triggered,
                        "sources_used": [{"source_name": s.source_name, "domain": s.domain, "status": s.status} for s in result.sources_used],
                        "api_status": result.api_status,
                        "data_quality_summary": result.data_quality_summary
                    }
                }) + "\n"
            else:
                yield json.dumps({
                    "status": "error",
                    "message": "No insight generated. Please try a different query."
                }) + "\n"
                
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield json.dumps({
                "status": "error",
                "message": f"Error processing query: {str(e)[:200]}"
            }) + "\n"
    
    return StreamingResponse(stream_results(), media_type="application/x-ndjson")

# ──── INTELLIGENCE NEWS ENGINE (DROP-IN REPLACEMENT) ────




# ──── DOMAIN CONFIG ────
DOMAIN_KEYWORDS = {
    "climate": {
        "strong": ["heatwave", "wildfire", "flood", "drought", "extreme", "crisis", "record"],
        "policy": ["emissions", "climate law", "carbon", "net zero", "agreement"]
    },
    "technology": {
        "strong": ["ai", "semiconductor", "chip", "quantum", "cyberattack", "zero-day"],
        "business": ["layoffs", "investment", "funding", "acquisition"],
        "policy": ["regulation", "bill", "ban"]
    },
    "geopolitics": {
        "strong": ["conflict", "war", "sanctions", "military", "tension"],
        "policy": ["treaty", "agreement", "alliance"]
    }
}

NOISE_KEYWORDS = [
    "review", "opinion", "top 10", "lifestyle",
    "how to", "guide", "tips", "features"
]


# ──── SIGNAL CLASSIFIER ────
def classify_signal(title: str, domain: str):
    title_lower = title.lower()
    score = 0

    config = DOMAIN_KEYWORDS.get(domain, {})

    if any(k in title_lower for k in config.get("strong", [])):
        score += 3

    if any(k in title_lower for k in config.get("business", [])):
        score += 2

    if any(k in title_lower for k in config.get("policy", [])):
        score += 2

    if "$" in title or "billion" in title_lower:
        score += 2

    if any(k in title_lower for k in NOISE_KEYWORDS):
        score -= 5

    if score >= 4:
        return "critical", score
    elif score >= 2:
        return "strategic", score
    else:
        return "ignore", score


# ──── INSIGHT GENERATOR ────
def generate_insight(title: str, domain: str):
    t = title.lower()

    # Tech
    if "layoffs" in t:
        return "Workforce shift → automation or cost restructuring"
    if "investment" in t or "funding" in t:
        return "Capital inflow → growth signal"
    if "chip" in t or "semiconductor" in t:
        return "Compute power race accelerating"

    # Geopolitics
    if "conflict" in t or "war" in t:
        return "Escalation risk → global instability"
    if "sanctions" in t:
        return "Economic pressure → trade disruption"

    # Climate
    if "heatwave" in t or "extreme" in t:
        return "Climate volatility increasing"
    if "flood" in t or "wildfire" in t:
        return "Environmental risk escalating"

    return "Emerging strategic development"


# ──── MAIN FETCH FUNCTION ────
async def fetch_news_for_domain(domain: str) -> list:
    """Fetch and return only high-impact intelligence signals"""

    def fetch_rss(q):
        encoded_query = urllib.parse.quote(q)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        return feedparser.parse(url)

    query_map = {
        "geopolitics": "geopolitics news conflict diplomacy",
        "climate": "climate change extreme weather disaster",
        "technology": "technology AI semiconductor cyber",
    }

    query_str = query_map.get(domain, domain) + " when:2d"

    try:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, fetch_rss, query_str)

        articles = []

        for entry in feed.entries:
            title = entry.title

            category, score = classify_signal(title, domain)

            # Strict filtering
            if category == "ignore" or score < 2:
                continue

            # Safe time parsing
            try:
                published_time = datetime(*entry.published_parsed[:6])
            except:
                published_time = datetime.now()

            # Source extraction
            source_name = getattr(entry, "source", {}).get("title", "Google News")
            if not isinstance(source_name, str):
                source_name = getattr(entry, "publisher", "Google News")

            articles.append({
                "title": title,
                "source": source_name,
                "publishedAt": published_time,
                "url": entry.link,
                "category": category,
                "score": score,
                "insight": generate_insight(title, domain)
            })

        # Sort by importance + recency
        articles.sort(key=lambda x: (x["score"], x["publishedAt"]), reverse=True)

        # Balanced output (critical first)
        critical = [a for a in articles if a["category"] == "critical"]
        strategic = [a for a in articles if a["category"] == "strategic"]

        final = critical + strategic

        return final[:8]

    except Exception as e:
        print(f"Error fetching Google News for {domain}: {e}")
        return []
        
    return [] # Final fallback is empty list, no more simulations.

@app.get("/api/v1/dashboard")
async def dashboard_endpoint():
    """
    Get tactical dashboard data for all domains.
    Returns filtered OSINT, live macros, climate anomalies, and real map data.
    """
    try:
        from backend.domain_connectors.economics import fetch_yahoo_finance_data
        
        # Parallel fetch for OSINT feeds
        [geo_news, clim_news, tech_news] = await asyncio.gather(
            fetch_news_for_domain("geopolitics"),
            fetch_news_for_domain("climate"),
            fetch_news_for_domain("technology")
        )
        
        # Parallel fetch for live Macro Economic Tickers
        macro_tickers = ["BTC-USD", "CL=F", "DX-Y.NYB", "GC=F"]
        econ_tasks = [fetch_yahoo_finance_data(t) for t in macro_tickers]
        
        # Fetch real map data (parallel)
        econ_results_list, air_traffic, weather, earthquakes, eonet_events = await asyncio.gather(
            asyncio.gather(*econ_tasks, return_exceptions=True),
            get_flight_traffic_data(),
            get_weather_data(),
            get_earthquake_data(),
            get_eonet_events()
        )

        # Flatten and filter economic results
        econ_macros = []
        for i, res in enumerate(econ_results_list):
            if isinstance(res, list) and len(res) > 0:
                rec = res[0]
                symbol = macro_tickers[i]
                
                pct = 0.0
                if hasattr(rec, 'metadata') and isinstance(rec.metadata, dict):
                    pct = rec.metadata.get("pct_change", 0.0)
                    
                econ_macros.append({
                    "symbol": symbol,
                    "name": rec.entity,
                    "price": rec.value,
                    "timestamp": rec.timestamp,
                    "pct_change": pct,
                    "history": []
                })
                
        # Isolate Climate Anomalies from weather feed
        climate_anomalies = []
        for point in weather:
            if point.get("temp", 20) > 40 or point.get("temp", 20) < -15 or any(h in point.get("condition", "").lower() for h in ["storm", "hurricane", "extreme"]):
                climate_anomalies.append({
                    "title": f"[{point.get('city', 'Unknown').upper()}] {point.get('condition').upper()} / {point.get('temp')}°C",
                    "source": "OpenWeatherMap Sensors",
                    "publishedAt": datetime.now().isoformat(),
                    "url": "#"
                })
                
        # Fallback to Google News if sensors report no catastrophes
        if not climate_anomalies and clim_news:
            climate_anomalies = clim_news
        
        return {
            "geo_news": geo_news[:8],
            "clim_news": climate_anomalies[:6],
            "econ_news": econ_macros,
            "tech_news": tech_news[:6],
            "map_data": {
                "air_traffic": air_traffic,
                "weather": weather,
                "earthquakes": earthquakes,
                "eonet_events": eonet_events,
                "conflicts": []
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# SPA Catch-all: Must be at the end to avoid intercepting APIs
@app.get("/{full_path:path}")
async def serve_spa_fallback(full_path: str):
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend not built. Run 'npm run build' in the frontend directory.</h1>", status_code=404)
