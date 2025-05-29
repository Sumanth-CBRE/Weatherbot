# WeatherBot Python Client with Groq API Tool-Calling Support

This project demonstrates a Python-based WeatherBot client and server with:
- Groq LLM-powered chat (default)
- Tool-calling for weather alerts, forecasts, and historical data
- Web UI (FastAPI) for chat
- Global weather support (US NWS for US, Open-Meteo for worldwide)
- Dynamic geocoding for any city/state/country
- Automated unit tests

## Features
- Supports Groq API as an LLM provider (default)
- Tool-calling for weather alerts, forecasts, and historical data
- Web UI for chat (http://localhost:8000)
- Global weather support: US NWS for US, Open-Meteo for worldwide
- Dynamic geocoding: just type a city, state, or country
- Automated unit tests (pytest)
- Robust message formatting and error diagnostics

## Setup
1. **Clone the repository** and create a Python virtual environment:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install ./weather-server-python
   pip install ./mcp-client-python
   pip install requests pytest
   ```
2. **Set up your `.env` file** in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
3. **Run the weather server (web UI):**
   ```sh
   cd weather-server-python
   python weather.py web
   # Visit http://localhost:8000 in your browser
   ```
4. **Or run the CLI client:**
   ```sh
   python mcp-client-python/client.py weather-server-python/weather.py
   ```

## Usage
- Enter queries like:
  - `Weather alerts in Texas`
  - `Weather forecast for 40.7 -74.0`
  - `Weather forecast for New York`
  - `Weather forecast for Paris`
  - `Weather forecast for Tokyo`
  - `Weather alerts in California`
  - `history for 40.7 -74.0`
- Type `quit` to exit the CLI.

## Testing
- Run all automated tests:
  ```sh
  cd weather-server-python
  pytest test_weather.py
  ```

## Troubleshooting
- If you encounter errors, the client will print detailed diagnostics including HTTP status, headers, and raw response from Groq or weather APIs.
- Ensure your API key is valid and your `.env` file is correctly configured.
- The client disables SSL verification for debugging. For production, enable SSL verification.

## Notes
- US forecasts use the National Weather Service (NWS) API.
- Global forecasts use the Open-Meteo API.
- Geocoding uses OpenStreetMap Nominatim.
- The project is robust against LLM silence and placeholder responses, and will always show a meaningful result or diagnostic.

## License
See [LICENSE](LICENSE).

*Document last updated: May 29, 2025*
