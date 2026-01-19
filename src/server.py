import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WeatherMCP", dependencies=["httpx"])

# Hardcoded city coordinates database 
CITIES_DB = {
    "london": {"lat": 51.5074, "lon": -0.1278, "name": "London"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York"},
    "chicago": {"lat": 41.8781, "lon": -87.6298, "name": "Chicago"},
    "san francisco": {"lat": 37.7749, "lon": -122.4194, "name": "San Francisco"},
    "miami": {"lat": 25.7617, "lon": -80.1918, "name": "Miami"},
    "seattle": {"lat": 47.6062, "lon": -122.3321, "name": "Seattle"},
    "austin": {"lat": 30.2672, "lon": -97.7431, "name": "Austin"},
    "sydney": {"lat": -33.8688, "lon": 151.2093, "name": "Sydney"},
    "berlin": {"lat": 52.5200, "lon": 13.4050, "name": "Berlin"},
    "beijing": {"lat": 39.9042, "lon": 116.4074, "name": "Beijing"},
    "shanghai": {"lat": 31.2304, "lon": 121.4737, "name": "Shanghai"}
}

BASE_URL = "https://api.open-meteo.com/v1/forecast"

def get_coords(city_name: str):
    """Helper function: Normalize city name and get coordinates."""
    if not city_name:
        return None
    city_key = city_name.lower().strip()
    return CITIES_DB.get(city_key)

# ---------------------------------------------------------
# 1. Resource: Provide a list of supported cities
# ---------------------------------------------------------
@mcp.resource("weather://cities/supported")
def list_supported_cities() -> str:
    """Returns a list of all cities supported by this weather server."""
    city_list = [data["name"] for data in CITIES_DB.values()]
    return f"Supported cities: {', '.join(city_list)}"

# ---------------------------------------------------------
# 2. Tool: Get current weather
# ---------------------------------------------------------
@mcp.tool()
async def get_current_weather(city: str) -> str:
    """
    Get current weather conditions (temperature, humidity, wind speed) for a specific city.
    Args:
        city: City name (e.g., 'London', 'New York', 'Shanghai')
    """
    location = get_coords(city)
    if not location:
        return f"Error: City '{city}' not found. Please check weather://cities/supported for the list."

    params = {
        "latitude": location["lat"],
        "longitude": location["lon"],
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json().get("current", {})
            
            return (
                f"Current Weather in {location['name']}:\n"
                f"- Temperature: {data.get('temperature_2m')}°C\n"
                f"- Humidity: {data.get('relative_humidity_2m')}%\n"
                f"- Wind Speed: {data.get('wind_speed_10m')} km/h\n"
                f"- Condition Code: {data.get('weather_code')} (WMO)"
            )
        except Exception as e:
            return f"Failed to fetch weather data: {str(e)}"

# ---------------------------------------------------------
# 3. Tool: Get weather forecast
# ---------------------------------------------------------
@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """
    Get weather forecast for the next few days.
    Args:
        city: City name.
        days: Number of days to forecast (1 to 7).
    """
    if not 1 <= days <= 7:
        return "Error: Days must be between 1 and 7."

    location = get_coords(city)
    if not location:
        return f"Error: City '{city}' not found."

    params = {
        "latitude": location["lat"],
        "longitude": location["lon"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": days
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params, timeout=10.0)
            data = response.json().get("daily", {})
            
            report = [f"Forecast for {location['name']} ({days} days):"]
            time = data.get("time", [])
            max_temp = data.get("temperature_2m_max", [])
            min_temp = data.get("temperature_2m_min", [])
            precip = data.get("precipitation_sum", [])

            # Simple alignment formatting
            for i in range(len(time)):
                report.append(
                    f"- {time[i]}: High {max_temp[i]}°C | Low {min_temp[i]}°C | Rain {precip[i]}mm"
                )
            return "\n".join(report)
        except Exception as e:
            return f"API Error: {str(e)}"

# ---------------------------------------------------------
# 4. Tool: Get weather alerts
# ---------------------------------------------------------
@mcp.tool()
async def get_weather_alerts(city: str) -> str:
    """
    Check for severe weather alerts (based on wind speed and rainfall thresholds).
    """
    location = get_coords(city)
    if not location:
        return f"Error: City '{city}' not found."

    params = {
        "latitude": location["lat"],
        "longitude": location["lon"],
        "current": "wind_speed_10m,precipitation"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params, timeout=10.0)
            data = response.json().get("current", {})
            
            wind = data.get("wind_speed_10m", 0)
            rain = data.get("precipitation", 0)

            alerts = []
            if wind > 80:
                alerts.append(f"⚠️ HIGH WIND WARNING: {wind} km/h detected.")
            if rain > 30:
                alerts.append(f"⚠️ HEAVY RAIN ALERT: {rain} mm detected.")
            
            if not alerts:
                return f"No active severe weather alerts for {location['name']}."
            return "\n".join(alerts)
        except Exception as e:
            return f"API Error: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    import os
    transport_mode = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport_mode == "sse":
        try:
            app = mcp._create_sse_app()
            uvicorn.run(app, host="0.0.0.0", port=8000)
        except AttributeError:
            print("Warning: Custom bind failed, falling back to default run().")
            mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
