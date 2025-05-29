import pytest
from fastapi.testclient import TestClient
from weather import app

client = TestClient(app)

def test_index():
    r = client.get("/")
    assert r.status_code == 200
    assert "Weather Chatbot" in r.text

def test_chat_forecast():
    r = client.post("/chat", json={"query": "forecast for 40.7 -74.0"})
    assert r.status_code == 200
    assert "Temperature" in r.json()["response"]

def test_chat_alerts():
    r = client.post("/chat", json={"query": "alerts in CA"})
    assert r.status_code == 200
    assert "Event:" in r.json()["response"] or "No active alerts" in r.json()["response"]

def test_chat_history():
    r = client.post("/chat", json={"query": "history for 40.7 -74.0"})
    assert r.status_code == 200
    assert "Yesterday at" in r.json()["response"]

def test_chat_invalid():
    r = client.post("/chat", json={"query": "nonsense"})
    assert r.status_code == 200
    assert "Try:" in r.json()["response"]

def test_chat_forecast_states():
    # Test all US state names for forecast
    state_coords = {
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
        # DC
        "district of columbia": (38.8974, -77.0268),
        # Common abbreviations
        "newyork": (40.7128, -74.0060),
        "texas": (31.0545, -97.5635),
        "california": (36.7783, -119.4179),
    }
    for state in state_coords:
        r = client.post("/chat", json={"query": f"forecast for {state}"})
        assert r.status_code == 200
        # Should not return unknown location for mapped states
        assert "Unknown location" not in r.json()["response"], f"Failed for {state}: {r.json()['response']}"

def test_chat_forecast_dynamic_geocoding():
    # Test dynamic geocoding for a few locations not in static map
    dynamic_places = [
        "Paris", "London", "Berlin", "Sydney", "Tokyo", "Mumbai", "Toronto", "Cape Town", "Beijing", "Moscow"
    ]
    for place in dynamic_places:
        r = client.post("/chat", json={"query": f"forecast for {place}"})
        assert r.status_code == 200
        # Should not return unknown location for valid cities
        assert "Unknown location" not in r.json()["response"], f"Failed for {place}: {r.json()['response']}"
        # Should contain 'Temperature' or 'Forecast' in the response
        assert "Temperature" in r.json()["response"] or "Forecast" in r.json()["response"], f"No forecast for {place}: {r.json()['response']}"
