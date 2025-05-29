from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

async def get_global_forecast(lat: float, lon: float) -> str:
    """Get global weather forecast using Open-Meteo API."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current_weather=true&hourly=temperature_2m,precipitation,weathercode,wind_speed_10m"
    )
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            if "current_weather" in data:
                cw = data["current_weather"]
                return (
                    f"Current Weather:\n"
                    f"Temperature: {cw['temperature']}°C\n"
                    f"Wind: {cw['windspeed']} km/h\n"
                    f"Weather Code: {cw['weathercode']}\n"
                )
            else:
                return "Unable to fetch global forecast."
    except Exception:
        return "Unable to fetch global forecast."

app = FastAPI(title="Weather MCP Web UI")

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html>
    <head><title>Weather Chatbot</title></head>
    <body>
        <h2>Weather Chatbot (Groq-powered)</h2>
        <form id="chat-form">
            <input type="text" id="query" name="query" placeholder="Ask about weather..." style="width:300px;">
            <button type="submit">Send</button>
        </form>
        <pre id="response" style="margin-top:1em;background:#f0f0f0;padding:1em;"></pre>
        <script>
        document.getElementById('chat-form').onsubmit = async function(e) {
            e.preventDefault();
            const query = document.getElementById('query').value;
            const resp = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query})
            });
            const data = await resp.json();
            document.getElementById('response').textContent = data.response;
        };
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    query = data.get("query", "")
    # Use MCP tools for weather
    if query.lower().startswith("alerts in"):
        # e.g. "alerts in CA"
        state = query.split()[-1].upper()
        result = await get_alerts(state)
    elif query.lower().startswith("forecast for"):
        # e.g. "forecast for 40.7 -74.0" or "forecast for NewYork"
        parts = query.split()
        try:
            # Try lat/lon first
            lat, lon = float(parts[-2]), float(parts[-1])
            # Try US NWS first
            nws_result = await get_forecast(lat, lon)
            if "Unable to fetch forecast data for this location." not in nws_result:
                result = nws_result
            else:
                # Fallback to global
                result = await get_global_forecast(lat, lon)
        except Exception:
            # Try state/city name
            location = " ".join(parts[2:]).strip()
            location_map = {
                "alabama": (32.8067, -86.7911),
                "alaska": (61.3707, -152.4044),
                "arizona": (33.7298, -111.4312),
                "arkansas": (34.9697, -92.3731),
                "california": (36.7783, -119.4179),
                "colorado": (39.5501, -105.7821),
                "connecticut": (41.6032, -73.0877),
                "delaware": (38.9108, -75.5277),
                "florida": (27.9944, -81.7603),
                "georgia": (33.0406, -83.6431),
                "hawaii": (21.0943, -157.4983),
                "idaho": (44.2405, -114.4788),
                "illinois": (40.3495, -88.9861),
                "indiana": (39.8494, -86.2583),
                "iowa": (42.0115, -93.2105),
                "kansas": (38.5266, -96.7265),
                "kentucky": (37.6681, -84.6701),
                "louisiana": (31.1695, -91.8678),
                "maine": (44.6939, -69.3819),
                "maryland": (39.0639, -76.8021),
                "massachusetts": (42.2302, -71.5301),
                "michigan": (43.3266, -84.5361),
                "minnesota": (45.6945, -93.9002),
                "mississippi": (32.7416, -89.6787),
                "missouri": (38.4561, -92.2884),
                "montana": (46.9219, -110.4544),
                "nebraska": (41.1254, -98.2681),
                "nevada": (38.3135, -117.0554),
                "new hampshire": (43.4525, -71.5639),
                "new jersey": (40.2989, -74.5210),
                "new mexico": (34.8405, -106.2485),
                "new york": (40.7128, -74.0060),
                "north carolina": (35.6301, -79.8064),
                "north dakota": (47.5289, -99.7840),
                "ohio": (40.3888, -82.7649),
                "oklahoma": (35.5653, -96.9289),
                "oregon": (44.5720, -122.0709),
                "pennsylvania": (40.5908, -77.2098),
                "rhode island": (41.6809, -71.5118),
                "south carolina": (33.8569, -80.9450),
                "south dakota": (44.2998, -99.4388),
                "tennessee": (35.7478, -86.6923),
                "texas": (31.0545, -97.5635),
                "utah": (40.1500, -111.8624),
                "vermont": (44.0459, -72.7107),
                "virginia": (37.7693, -78.1700),
                "washington": (47.4009, -121.4905),
                "west virginia": (38.4912, -80.9546),
                "wisconsin": (44.2685, -89.6165),
                "wyoming": (42.7559, -107.3025),
                "district of columbia": (38.8974, -77.0268),
                # Common abbreviations
                "newyork": (40.7128, -74.0060),
            }
            coords = location_map.get(location.lower())
            if coords:
                lat, lon = coords
            else:
                coords = await geocode_location(location)
                if coords:
                    lat, lon = coords
                else:
                    result = f"Unknown location '{location}'. Try: forecast for <lat> <lon> or forecast for <city/state> (e.g. NewYork)"
                    return JSONResponse({"response": result})
            # Try US NWS first
            nws_result = await get_forecast(lat, lon)
            if "Unable to fetch forecast data for this location." not in nws_result:
                result = nws_result
            else:
                # Fallback to global
                result = await get_global_forecast(lat, lon)
    elif query.lower().startswith("history for"):
        # e.g. "history for 40.7 -74.0"
        parts = query.split()
        try:
            lat, lon = float(parts[-2]), float(parts[-1])
            result = await get_historical_weather(lat, lon)
        except Exception:
            result = "Invalid coordinates. Use: history for <lat> <lon>"
    else:
        result = "Try: alerts in <STATE>, forecast for <LAT> <LON>, or history for <LAT> <LON>"
    return JSONResponse({"response": result})

@mcp.tool()
async def get_historical_weather(latitude: float, longitude: float) -> str:
    """Get historical weather for a location (past 24h, mock data).

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # NWS API does not provide free historical data, so we mock it for demo
    # In production, use a paid API or NOAA CDO API
    return f"""
Yesterday at ({latitude}, {longitude}):
Temperature: 68°F
Wind: 5 mph NW
Conditions: Partly cloudy, no precipitation.
"""

async def geocode_location(location: str) -> tuple[float, float] | None:
    """Dynamically geocode a location name to (lat, lon) using Nominatim API."""
    url = f"https://nominatim.openstreetmap.org/search"
    params = {"q": location, "format": "json", "limit": 1}
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return lat, lon
        except Exception:
            pass
    return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        uvicorn.run("weather:app", host="0.0.0.0", port=8000, reload=True)
    else:
        mcp.run(transport='stdio')
