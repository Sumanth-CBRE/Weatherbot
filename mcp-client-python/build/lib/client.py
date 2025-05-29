import asyncio
import os
import json
import requests
import re
from typing import Optional, Literal
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self, llm_provider: Literal["anthropic", "openai", "llama", "groq"] = "openai"):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm_provider = llm_provider
        self.anthropic = Anthropic() if llm_provider == "anthropic" else None
        self.openai = OpenAI() if llm_provider == "openai" else None
        self.llama_api_key = os.getenv("LLAMA_API_KEY", "")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> tuple:
        """Process a query using available LLM (Claude, OpenAI, Llama, or Groq) and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        last_tool_result = None
        # Process with selected provider
        if self.llm_provider == "anthropic":
            llm_response = await self._process_with_claude(query, messages, available_tools)
        elif self.llm_provider == "llama":
            llm_response = await self._process_with_llama(query, messages, available_tools)
        elif self.llm_provider == "groq":
            llm_response = await self._process_with_groq(query, messages, available_tools)
        else:
            llm_response = await self._process_with_openai(query, messages, available_tools)
        # Find the last tool message content
        for m in reversed(messages):
            if m.get("role") == "tool":
                last_tool_result = m.get("content", None)
                break
        return llm_response, last_tool_result

    async def _process_with_claude(self, query: str, messages: list, available_tools: list) -> str:
        """Process a query using Claude"""
        # Print debugging information
        print(f"Making API request to Claude with {len(available_tools)} tools available")
        
        try:
            # Initial Claude API call
            response = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",  # Using a more recent Claude model
                max_tokens=1000,
                messages=messages,
                tools=available_tools
            )
        except Exception as e:
            print(f"Claude API Error: {str(e)}")
            return f"Sorry, I encountered an error when connecting to Claude: {str(e)}"

        # Process response and handle tool calls
        final_text = []

        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input
                
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Continue conversation with tool results
                if hasattr(content, 'text') and content.text:
                    messages.append({
                      "role": "assistant",
                      "content": content.text
                    })
                messages.append({
                    "role": "user", 
                    "content": result.content
                })

                # Get next response from Claude
                try:
                    response = self.anthropic.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=1000,
                        messages=messages,
                    )
                    final_text.append(response.content[0].text)
                except Exception as e:
                    final_text.append(f"Error getting follow-up response: {str(e)}")

        return "\n".join(final_text)
        
    async def _process_with_openai(self, query: str, messages: list, available_tools: list) -> str:
        """Process a query using OpenAI"""
        # Print debugging information
        print(f"Making API request to OpenAI with {len(available_tools)} tools available")
        
        # Convert MCP tools to OpenAI format
        openai_tools = []
        for tool in available_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
            
        try:
            # Initial OpenAI API call
            response = self.openai.chat.completions.create(
                model="gpt-3.5-turbo",  # Using a standard OpenAI model
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                max_tokens=1000
            )
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            return f"Sorry, I encountered an error when connecting to OpenAI: {str(e)}"

        # Process response and handle tool calls
        final_text = []
        response_message = response.choices[0].message

        if response_message.content:
            final_text.append(response_message.content)
            
        # Handle tool calls if present
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
                
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Continue conversation with tool results
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function", 
                            "function": {"name": tool_name, "arguments": tool_args}
                        }
                    ]
                })
                
                messages.append({
                    "role": "tool",
                    "content": result.content,
                    "tool_call_id": tool_call.id
                })

                # Get next response from OpenAI
                try:
                    response = self.openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        max_tokens=1000
                    )
                    final_text.append(response.choices[0].message.content)
                except Exception as e:
                    final_text.append(f"Error getting follow-up response: {str(e)}")

        return "\n".join(final_text)
    
    async def _process_with_llama(self, query: str, messages: list, available_tools: list) -> str:
        """Process a query using Llama API"""
        # Print debugging information
        print(f"Making API request to Llama API with {len(available_tools)} tools available")
        
        # Convert MCP tools to function calling format
        functions = []
        for tool in available_tools:
            functions.append({
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            })
            
        # Format messages for Llama API
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
            
        # API endpoint for Together AI
        api_url = "https://api.together.xyz/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llama_api_key}"
        }
        
        payload = {
            "model": "Meta-Llama-3-8B-Instruct",  # Use an appropriate Llama model
            "messages": formatted_messages,
            "tools": functions,
            "tool_choice": "auto",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            # Initial Llama API call
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            
            if "error" in response_data:
                print(f"Llama API Error: {response_data['error']}")
                return f"Sorry, I encountered an error when connecting to Llama API: {response_data['error']}"
                
        except requests.exceptions.RequestException as e:
            print(f"Llama API Request Error: {str(e)}")
            return f"Sorry, I encountered an error when connecting to Llama API: {str(e)}"
        except json.JSONDecodeError as e:
            print(f"Llama API JSON Error: {str(e)}")
            return f"Sorry, I encountered an error parsing the response from Llama API: {str(e)}"

        # Process response and handle tool calls
        final_text = []
        
        # Extract the assistant's message
        assistant_message = response_data["choices"][0]["message"]
        
        if "content" in assistant_message and assistant_message["content"]:
            final_text.append(assistant_message["content"])
            
        # Handle tool calls if present
        if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
            for tool_call in assistant_message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]
                
                # Execute tool call
                result = await self.session.call_tool(tool_name, json.loads(tool_args))
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Continue conversation with tool results
                formatted_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call["id"],
                            "type": "function", 
                            "function": {"name": tool_name, "arguments": tool_args}
                        }
                    ]
                })
                
                formatted_messages.append({
                    "role": "tool",
                    "content": result.content,
                    "tool_call_id": tool_call["id"]
                })

                # Get next response from Llama
                try:
                    payload["messages"] = formatted_messages
                    response = requests.post(api_url, json=payload, headers=headers)
                    response.raise_for_status()
                    response_data = response.json()
                    assistant_message = response_data["choices"][0]["message"]
                    final_text.append(assistant_message["content"])
                except Exception as e:
                    final_text.append(f"Error getting follow-up response: {str(e)}")

        return "\n".join(final_text)

    async def _process_with_groq(self, query: str, messages: list, available_tools: list) -> str:
        """Process a query using Groq API"""
        print(f"Making API request to Groq with {len(available_tools)} tools available")
        # Convert MCP tools to OpenAI-compatible format (Groq is OpenAI-compatible)
        groq_tools = []
        for tool in available_tools:
            groq_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_api_key}"
        }
        payload = {
            "model": "llama3-8b-8192",  # You can change to another Groq-supported model
            "messages": messages,
            "tools": groq_tools,
            "tool_choice": "auto",
            "max_tokens": 1000
        }
        def sanitize_messages(msgs):
            sanitized = []
            for m in msgs:
                role = m.get("role")
                m = {k: v for k, v in m.items() if k != "tool_call_step"}
                if role == "user":
                    entry = {"role": role, "content": m.get("content", "")}
                    sanitized.append(entry)
                elif role == "assistant":
                    if m.get("tool_calls") is not None:
                        tool_calls = []
                        for tc in m["tool_calls"]:
                            func = tc["function"].copy()
                            # Always use 'arguments' as a JSON string, not 'parameters'
                            if "parameters" in func:
                                func.pop("parameters")
                            if isinstance(func.get("arguments"), dict):
                                func["arguments"] = json.dumps(func["arguments"])
                            elif not isinstance(func.get("arguments"), str):
                                # If arguments are missing or not a string, default to empty JSON
                                func["arguments"] = "{}"
                            tool_calls.append({
                                "id": tc["id"],
                                "type": tc["type"],
                                "function": func
                            })
                        entry = {"role": role, "content": None, "tool_calls": tool_calls}
                        sanitized.append(entry)
                    elif isinstance(m.get("content"), str) and m["content"].strip():
                        entry = {"role": role, "content": m["content"]}
                        sanitized.append(entry)
                elif role == "tool":
                    entry = {
                        "role": "tool",
                        "content": m.get("content", ""),
                        "tool_call_id": m.get("tool_call_id")
                    }
                    sanitized.append(entry)
            return sanitized
        try:
            response = requests.post(api_url, json={**payload, "messages": sanitize_messages(messages)}, headers=headers, verify=False)
            print(f"[Groq API Raw Response] Status code: {response.status_code}")
            print(f"[Groq API Raw Response] Headers: {response.headers}")
            print(f"[Groq API Raw Response] Raw body: {response.text!r}")
            if not response.text.strip():
                print("[Groq API Raw Response] The response body is completely empty.")
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Groq API Request Error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[Groq API Diagnostics] Status code: {e.response.status_code}")
                print(f"[Groq API Diagnostics] Headers: {e.response.headers}")
                print(f"[Groq API Diagnostics] Raw body: {e.response.text!r}")
                if not e.response.text.strip():
                    print("[Groq API Diagnostics] The response body is completely empty.")
            return f"Sorry, I encountered an error when connecting to Groq API: {str(e)}"
        except json.JSONDecodeError as e:
            print(f"Groq API JSON Error: {str(e)}")
            print(f"[Groq API Diagnostics] Status code: {response.status_code}")
            print(f"[Groq API Diagnostics] Headers: {response.headers}")
            print(f"[Groq API Diagnostics] Raw body: {response.text!r}")
            if not response.text.strip():
                print("[Groq API Diagnostics] The response body is completely empty.")
            return f"Sorry, I encountered an error parsing the response from Groq API: {str(e)}"
        final_text = []
        response_message = response_data["choices"][0]["message"]
        if response_message.get("content"):
            final_text.append(response_message["content"])
        # Handle tool calls if present
        if response_message.get("tool_calls"):
            for tool_call in response_message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]
                if isinstance(tool_args, str):
                    tool_args = json.loads(tool_args)
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                # Add assistant message with tool_calls (mark as tool_call_step, NO content)
                messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call["id"],
                            "type": "function",
                            "function": {"name": tool_name, "arguments": tool_args}
                        }
                    ]
                })
                # Add tool message
                # Ensure result.content is a plain string (not repr of object/list)
                tool_content = result.content
                if isinstance(tool_content, list):
                    # Join all .text fields if list of objects
                    tool_content = "".join(getattr(item, "text", str(item)) for item in tool_content)
                elif hasattr(tool_content, "text"):
                    tool_content = tool_content.text
                else:
                    tool_content = str(tool_content)
                messages.append({
                    "role": "tool",
                    "content": tool_content,
                    "tool_call_id": tool_call["id"]
                })
                # For follow-up, add a plain assistant message (no tool_calls, only content if present)
                try:
                    sanitized_payload = {**payload, "messages": sanitize_messages(messages)}
                    print("\n[DEBUG] Payload for Groq follow-up request:")
                    print(json.dumps(sanitized_payload, indent=2, default=str))
                    response = requests.post(api_url, json=sanitized_payload, headers=headers, verify=False)
                    response.raise_for_status()
                    response_data = response.json()
                    response_message = response_data["choices"][0]["message"]
                    if response_message.get("content"):
                        messages.append({
                            "role": "assistant",
                            "content": response_message["content"]
                        })
                    else:
                        messages.append({"role": "assistant"})
                    final_text.append(response_message.get("content", ""))
                except Exception as e:
                    final_text.append(f"Error getting follow-up response: {str(e)}")
        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        print("\nExample queries:")
        print("  - Weather alerts in Texas")
        print("  - Weather forecast for 40.7 -74.0")
        print("  - Weather alerts in California\n")
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                llm_response, last_tool_result = await self.process_query(query)
                print("\n" + "="*40)
                cleaned = "\n".join(line for line in llm_response.splitlines() if not line.startswith("[Calling tool "))
                cleaned_stripped = cleaned.strip().lower()
                # Treat any <tool-use ...> tag as empty
                tool_use_pattern = re.compile(r"^<tool-use.*?>.*?</tool-use>$|^<tool-use\s*/?>$", re.IGNORECASE | re.DOTALL)
                if (not cleaned_stripped or tool_use_pattern.match(cleaned_stripped)) and last_tool_result:
                    print("[Tool Result] " + last_tool_result)
                else:
                    print(cleaned.strip())
                print("\n" + "="*40)
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
    
    # Optionally set Groq API key from environment or .env
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "")
    
    client = MCPClient(llm_provider="groq")  # Default to Groq API
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
