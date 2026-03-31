import httpx
from datetime import datetime, timezone
import logging

from backend.config import settings
from backend.schemas import NormalizedRecord

logger = logging.getLogger(__name__)

async def fetch_openweathermap_data(country: str) -> list[NormalizedRecord]:
    """
    Fetches comprehensive current weather for the city/capital from OpenWeatherMap.
    Returns individual records for each metric: temp, feels_like, humidity, wind, pressure, etc.
    """
    if not settings.OPENWEATHERMAP_API_KEY or settings.OPENWEATHERMAP_API_KEY == "your_openweathermap_api_key":
        raise ValueError("OPENWEATHERMAP_API_KEY is missing or invalid")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": country,
        "appid": settings.OPENWEATHERMAP_API_KEY,
        "units": "metric"
    }

    records = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            dt = datetime.now(timezone.utc)
            city_name = data.get("name", country)
            country_code = data.get("sys", {}).get("country", "")
            location_label = f"{city_name}, {country_code}" if country_code else city_name

            main = data.get("main", {})
            wind = data.get("wind", {})
            clouds = data.get("clouds", {})
            weather_list = data.get("weather", [{}])
            weather_desc = weather_list[0].get("description", "Unknown").capitalize()
            weather_icon = weather_list[0].get("main", "")

            def add(label, value, ref="OWM_current"):
                records.append(NormalizedRecord(
                    domain="climate", source="OpenWeatherMap",
                    entity=location_label, data_type="weather",
                    title_or_label=label, value=value,
                    timestamp=dt.isoformat(), raw_reference=ref
                ))

            add("Condition", f"{weather_icon} — {weather_desc}")
            add("Temperature", f"{main.get('temp', 'N/A')} °C")
            add("Feels Like", f"{main.get('feels_like', 'N/A')} °C")
            add("Temp Min / Max", f"{main.get('temp_min', 'N/A')} °C / {main.get('temp_max', 'N/A')} °C")
            add("Humidity", f"{main.get('humidity', 'N/A')} %")
            add("Pressure", f"{main.get('pressure', 'N/A')} hPa")
            if data.get("visibility") is not None:
                add("Visibility", f"{data['visibility'] / 1000:.1f} km")
            add("Wind Speed", f"{wind.get('speed', 'N/A')} m/s")
            if wind.get("deg") is not None:
                dirs = ["N","NE","E","SE","S","SW","W","NW"]
                compass = dirs[round(wind["deg"] / 45) % 8]
                add("Wind Direction", f"{compass} ({wind['deg']}°)")
            add("Cloud Cover", f"{clouds.get('all', 'N/A')} %")
            if data.get("rain"):
                add("Rainfall (1h)", f"{data['rain'].get('1h', 0)} mm")
            if data.get("snow"):
                add("Snowfall (1h)", f"{data['snow'].get('1h', 0)} mm")

    except Exception as e:
        logger.error(f"OpenWeatherMap fetch failed: {e}")
        raise e

    return records


async def fetch_nasa_power_data(country: str) -> list[NormalizedRecord]:
    """
    Fetches historical weather data (last 7 days) from NASA POWER API.
    Since NASA POWER needs lat/lon, we use OpenWeatherMap Geocoding first.
    """
    if not settings.OPENWEATHERMAP_API_KEY or settings.OPENWEATHERMAP_API_KEY == "your_openweathermap_api_key":
        logger.error("Skipping NASA POWER: Missing OWM API Key for Geocoding")
        return []

    from datetime import timedelta
    
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    geo_params = {"q": country, "limit": 1, "appid": settings.OPENWEATHERMAP_API_KEY}
    
    records = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            geo_resp = await client.get(geo_url, params=geo_params)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            
            if not geo_data:
                return []
                
            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]
            
            end_dt = datetime.now(timezone.utc)
            start_dt = end_dt - timedelta(days=7)
            
            start_str = start_dt.strftime("%Y%m%d")
            end_str = end_dt.strftime("%Y%m%d")
            
            nasa_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
            nasa_params = {
                "parameters": "T2M,PRECTOTCORR",
                "community": "RE",
                "longitude": lon,
                "latitude": lat,
                "start": start_str,
                "end": end_str,
                "format": "JSON"
            }
            
            nasa_resp = await client.get(nasa_url, params=nasa_params)
            nasa_resp.raise_for_status()
            nasa_data = nasa_resp.json()
            
            params_data = nasa_data.get("properties", {}).get("parameter", {})
            t2m_data = params_data.get("T2M", {})
            precip_data = params_data.get("PRECTOTCORR", {})
            
            # T2M and PRECTOTCORR are dictionaries keyed by 'YYYYMMDD'
            # Let's take the most recent 3 days of valid data (filter out -999.0 which is fill value)
            valid_dates = sorted([d for d in t2m_data.keys() if t2m_data[d] != -999.0], reverse=True)[:3]
            
            for d in valid_dates:
                dt = datetime.strptime(d, "%Y%m%d").replace(tzinfo=timezone.utc)
                temp = t2m_data.get(d)
                precip = precip_data.get(d)
                
                date_label = dt.strftime("%d-%b-%Y")
                records.append(NormalizedRecord(
                    domain="climate",
                    source="NASA_POWER",
                    entity=country,
                    data_type="historical_weather",
                    title_or_label=f"Avg Temp [{date_label}]",
                    value=f"{temp} °C" if temp is not None else "Unknown",
                    timestamp=dt.isoformat(),
                    raw_reference="NASA_POWER_API"
                ))
                
                if precip is not None and precip != -999.0:
                    records.append(NormalizedRecord(
                        domain="climate",
                        source="NASA_POWER",
                        entity=country,
                        data_type="historical_precip",
                        title_or_label=f"Precipitation [{date_label}]",
                        value=f"{precip} mm",
                        timestamp=dt.isoformat(),
                        raw_reference="NASA_POWER_API"
                    ))
                    
    except Exception as e:
        logger.error(f"NASA POWER fetch failed: {e}")
        
    return records
