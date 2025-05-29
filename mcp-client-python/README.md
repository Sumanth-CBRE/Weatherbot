# An LLM-Powered Weather Chatbot MCP Client (Groq Only)

This project is a Python-based chatbot client for interacting with an MCP weather server. It now exclusively uses the Groq LLM provider for all queries (OpenAI and Anthropic support have been removed for simplicity).

## Features
- Query weather alerts for any US state
- Get weather forecasts for any latitude/longitude
- Uses Groq LLM for natural language understanding and tool selection
- Easy to run locally with a single command

## How to Run
1. **Clone the repository and navigate to the project root:**
   ```sh
   cd /Users/SSurneni/Weatherbot/Downloads/quickstart-resources-main
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install ./weather-server-python
   pip install ./mcp-client-python
   pip install requests
   ```
4. **Set your Groq API key in a `.env` file at the project root:**
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```
5. **Run the client:**
   ```sh
   cd mcp-client-python
   python3 client.py ../weather-server-python/weather.py
   ```

## Example Queries
- Weather alerts in Texas
- Weather forecast for 40.7 -74.0
- Weather alerts in California

## Suggestion for New Features
- **Add a simple web UI**: Use Flask or FastAPI to provide a web-based chat interface for weather queries.
- **Support for more LLM providers**: If needed, add back Anthropic or Llama, or support other Groq models.
- **Historical weather data**: Add a tool to fetch and display past weather data for a location.
- **Weather notifications**: Allow users to subscribe to weather alerts for a region and receive notifications (email or webhook).
- **Unit tests**: Add automated tests for the client and server logic.

See the [Building MCP clients](https://modelcontextprotocol.io/tutorials/building-a-client) tutorial for more information.
