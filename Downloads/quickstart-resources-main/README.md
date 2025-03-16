# WeatherBot Python Client with Groq API Tool-Calling Support

This project demonstrates how to use the WeatherBot Python client with an OpenAI-compatible LLM API (Groq) for tool-calling, specifically for weather alerts and forecasts.

## Features
- Supports Groq API as an LLM provider (default)
- Tool-calling for weather alerts and forecasts
- Robust message formatting for OpenAI/Groq compatibility
- Detailed error diagnostics for LLM API issues
- User-friendly output and fallback logic

## Setup
1. **Clone the repository** and create a Python virtual environment:
   ```sh
   python3 -m venv mcp_venv
   source mcp_venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Set up your `.env` file** in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
3. **Run the weather server and client:**
   ```sh
   python mcp-client-python/client.py weather-server-python/weather.py
   ```

## Usage
- Enter queries like:
  - `Weather alerts in Texas`
  - `Weather forecast for 40.7 -74.0`
  - `Weather alerts in California`
- Type `quit` to exit.

## Troubleshooting
- If you encounter errors, the client will print detailed diagnostics including HTTP status, headers, and raw response from Groq.
- Ensure your API key is valid and your `.env` file is correctly configured.

## Notes
- The client disables SSL verification for debugging. For production, enable SSL verification.
- The client is robust against LLM silence and placeholder responses, and will always show a meaningful result or diagnostic.

## License
See [LICENSE](LICENSE).

*Document last updated: March 15, 2024*
