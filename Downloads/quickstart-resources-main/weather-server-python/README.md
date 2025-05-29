# A Simple MCP Weather Server written in Python

See the [Quickstart](https://modelcontextprotocol.io/quickstart) tutorial for more information.

## Features
- Weather alerts for any US state
- Weather forecasts for any US state, US city, or global location
- Dynamic geocoding for arbitrary city/state/country names
- Global weather support via Open-Meteo API (fallback)
- FastAPI web UI for interactive chat
- **Flexible natural language queries**: Ask about the weather using natural phrasing, e.g.:
  - "What is the weather in Texas?"
  - "Show me the weather for Paris"
  - "Weather in Tokyo"
  - "Forecast for 40.7 -74.0"
  - "alerts in CA"
- Automated unit tests for all endpoints and features

## Usage

You can now ask about the weather using a wide variety of natural language queries. Examples:

- `What is the weather in Texas?`
- `Show me the weather for Paris`
- `Weather in Tokyo`
- `Forecast for 40.7 -74.0`
- `alerts in CA`
- `history for 40.7 -74.0`

The backend will extract the intent and location from your query and return the appropriate weather information.

## How it works

The `/chat` endpoint now uses regex-based intent and location extraction. Any query containing the words "weather" or "forecast" and a location (e.g., city, state, or country) will be routed to the correct weather lookup, regardless of phrasing. This allows for much more flexible and natural user queries.
