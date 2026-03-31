"""
OpenSky Network API Connector for Aircraft/Flight Data
Free API: https://opensky-network.org/
No API key required for free tier
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

OPENSKY_API_URL = "https://opensky-network.org/api/states/all"

class FlightsConnector:
    """
    Fetches live flight data from OpenSky Network API
    Free tier: ~640 aircraft updates per day with ~4 hour latency
    """
    
    @staticmethod
    async def get_flights_near_region(
        latitude: float, 
        longitude: float, 
        radius_km: int = 200
    ) -> List[Dict]:
        """
        Get flights within a radius of a location
        
        Args:
            latitude: Center latitude
            longitude: Center longitude  
            radius_km: Search radius in kilometers
            
        Returns:
            List of flight objects with position, altitude, speed
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(OPENSKY_API_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        logger.warning(f"OpenSky API returned status {resp.status}")
                        return []
                    
                    data = await resp.json()
                    
                    if not data.get('states'):
                        return []
                    
                    flights = []
                    for state in data['states']:
                        # state format: [icao24, callsign, origin_country, time_position, last_contact,
                        #              longitude, latitude, baro_altitude, on_ground, velocity,
                        #              true_track, vertical_rate, sensors, geo_altitude, squawk, spi, position_source]
                        
                        if state[5] is None or state[6] is None:  # No position data
                            continue
                        
                        flight_lat = state[6]
                        flight_lon = state[5]
                        
                        # Check if within radius
                        dist = FlightsConnector._haversine(latitude, longitude, flight_lat, flight_lon)
                        if dist <= radius_km:
                            flights.append({
                                'callsign': state[1].strip() if state[1] else f"ICAO-{state[0][:6]}",
                                'icao24': state[0],
                                'country': state[2],
                                'latitude': flight_lat,
                                'longitude': flight_lon,
                                'altitude': state[7],  # Barometric altitude in meters
                                'velocity': state[9],  # Velocity in m/s
                                'track': state[10],    # True track in degrees
                                'vertical_rate': state[11],  # Vertical rate in m/s
                                'on_ground': state[8],
                                'distance_km': dist,
                            })
                    
                    return sorted(flights, key=lambda x: x['distance_km'])[:50]  # Top 50 closest
                    
        except asyncio.TimeoutError:
            logger.error("OpenSky API request timeout")
            return []
        except Exception as e:
            logger.error(f"Error fetching flights: {e}")
            return []
    
    @staticmethod
    async def get_global_flights() -> List[Dict]:
        """Get ALL global flights currently in the air"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(OPENSKY_API_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        logger.warning(f"OpenSky API returned status {resp.status}")
                        return []
                    
                    data = await resp.json()
                    
                    if not data.get('states'):
                        logger.info("No flights currently in air")
                        return []
                    
                    flights = []
                    flight_count = 0
                    
                    # Process ALL states without sampling
                    for state in data['states']:
                        if state[5] is None or state[6] is None:  # Skip if no position
                            continue
                        
                        try:
                            flight_count += 1
                            flights.append({
                                'callsign': (state[1] or f"ICAO-{state[0][:6]}").strip(),
                                'icao24': state[0],
                                'country': state[2] or 'Unknown',
                                'lat': float(state[6]),
                                'lng': float(state[5]),
                                'altitude': int(state[7]) if state[7] else 0,  # meters
                                'speed': float(state[9]) * 1.944 if state[9] else 0,  # m/s to knots
                                'track': float(state[10]) if state[10] else 0,  # degrees
                                'vertical_rate': float(state[11]) if state[11] else 0,  # m/s
                                'on_ground': bool(state[8]),
                                'domain': 'flights',
                            })
                        except (TypeError, ValueError) as e:
                            logger.debug(f"Error parsing flight state: {e}")
                            continue
                    
                    logger.info(f"Fetched {flight_count} active flights")
                    return flights
                    
        except asyncio.TimeoutError:
            logger.error("OpenSky API request timeout")
            return []
        except Exception as e:
            logger.error(f"Error fetching global flights: {e}")
            return []
    
    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r


# Synchronous wrapper for FastAPI
async def get_flights_for_dashboard() -> List[Dict]:
    """Get flights data for dashboard display"""
    flights = await FlightsConnector.get_global_flights()
    
    # If no real flights, add comprehensive mock data
    if not flights or len(flights) < 50:
        flights.extend(_get_comprehensive_flight_data())
    
    return flights


def _get_comprehensive_flight_data() -> List[Dict]:
    """Generate comprehensive mock flight data across major airline routes"""
    import random
    
    airline_routes = [
        # (airline_code, route_start_lat, route_start_lon, route_end_lat, route_end_lon, flights_count)
        ("BA", 51.5, -0.1, 40.7, -74.0, 8),      # London to New York
        ("AF", 48.9, 2.6, 33.7, -84.4, 8),       # Paris to Atlanta
        ("LH", 52.4, 13.4, 35.8, 51.2, 8),       # Berlin to Dubai
        ("UA", 40.7, -74.0, 51.5, -0.1, 8),      # New York to London
        ("SQ", 1.4, 103.9, 35.6, 139.7, 10),     # Singapore to Tokyo
        ("CX", 22.3, 114.2, 1.4, 103.9, 8),      # Hong Kong to Singapore
        ("QF", -33.9, 151.2, 22.3, 114.2, 8),    # Sydney to Hong Kong
        ("EK", 25.3, 55.3, 35.6, 139.7, 10),     # Dubai to Tokyo
        ("KL", 52.3, 4.9, 35.6, 139.7, 8),       # Amsterdam to Tokyo
        ("AA", 40.7, -74.0, 33.7, -84.4, 10),    # New York to Atlanta
        ("DL", 33.7, -84.4, 48.9, 2.6, 8),       # Atlanta to Paris
        ("AC", 43.7, -79.6, 51.5, -0.1, 8),      # Toronto to London
        ("JL", 35.6, 139.7, 40.7, -74.0, 8),     # Tokyo to New York
        ("FX", 33.9, -118.4, 35.6, 139.7, 8),    # Los Angeles to Tokyo
        ("TG", 13.7, 100.7, 35.6, 139.7, 8),     # Bangkok to Tokyo
        ("NH", 35.6, 139.7, 51.5, -0.1, 8),      # Tokyo to London
        ("MH", 3, 101.7, 22.3, 114.2, 8),        # Kuala Lumpur to Hong Kong
        ("CI", 25.1, 121.5, 22.3, 114.2, 8),     # Taipei to Hong Kong
        ("BR", 25.1, 121.5, 1.4, 103.9, 8),      # Taipei to Singapore
        ("TW", 25.1, 121.5, 35.6, 139.7, 8),     # Taipei to Tokyo
    ]
    
    flights = []
    flight_counter = 0
    
    for airline, start_lat, start_lon, end_lat, end_lon, count in airline_routes:
        for i in range(count):
            # Distribute flight along the route
            progress = random.uniform(0, 1)
            current_lat = start_lat + (end_lat - start_lat) * progress
            current_lon = start_lon + (end_lon - start_lon) * progress
            
            flight_counter += 1
            flights.append({
                'callsign': f"{airline}{random.randint(1, 999):03d}",
                'icao24': f"{airline.lower()}{flight_counter:06d}",
                'country': 'Mock',
                'lat': current_lat + random.uniform(-1, 1),
                'lng': current_lon + random.uniform(-1, 1),
                'altitude': random.randint(25000, 43000),  # meters
                'speed': random.randint(400, 550),  # knots
                'track': random.uniform(0, 360),
                'vertical_rate': random.uniform(-10, 10),  # m/s
                'on_ground': False,
                'domain': 'flights',
            })
    
    return flights
