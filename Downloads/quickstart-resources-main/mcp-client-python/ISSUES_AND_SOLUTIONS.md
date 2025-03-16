# WeatherBot Python Client: Issues Encountered and Solutions

This document details the major issues encountered while integrating and debugging the WeatherBot Python client with Groq API tool-calling, and the step-by-step process used to resolve each one.

## 1. Groq API Integration
- **Issue:** The project originally supported only Anthropic, OpenAI, and Llama providers. Adding Groq required not only a new provider but also careful mapping of tool definitions and message formats to match OpenAI-compatible APIs.
- **How we solved it:**
  - Implemented a new `_process_with_groq` method in `client.py`.
  - Ensured tool definitions and message payloads matched Groq's OpenAI-compatible expectations.
  - Set Groq as the default provider for easy testing.

## 2. SSL Certificate Errors
- **Issue:** The client failed to connect to Groq due to SSL certificate verification errors, which are common in some dev environments or with new APIs.
- **How we solved it:**
  - Temporarily disabled SSL verification in the `requests.post` call to allow progress and isolate the problem.
  - Noted in documentation that SSL should be enabled for production.

## 3. Tool Call Argument Type Error
- **Issue:** The tool call arguments were sometimes passed as Python dicts instead of JSON strings, which caused the Groq/OpenAI API to reject the request.
- **How we solved it:**
  - Added logic to always serialize tool call arguments as JSON strings before including them in the payload.
  - Added checks and conversions in the message sanitization function.

## 4. Serialization Error for Tool Results
- **Issue:** Tool results returned from the weather server could be lists, objects, or other non-string types, causing serialization errors or unreadable output.
- **How we solved it:**
  - Ensured all tool result content is converted to a plain string before being sent to the LLM or displayed to the user.

## 5. Message Formatting for OpenAI/Groq
- **Issue:** The OpenAI-compatible APIs are strict about message structure, especially for tool-calling. Incorrect use of `tool_calls`, `content`, or message roles led to cryptic API errors.
- **How we solved it:**
  - Carefully studied OpenAI and Groq API docs and error messages.
  - Implemented a robust `sanitize_messages` function to ensure all messages are formatted exactly as required.
  - Added debug output to inspect the exact payload sent to Groq after each tool call.

## 6. Missing `content: null` in Assistant Tool-Calling Messages
- **Issue:** When the assistant message included a tool call, the API required `"content": null`, but this was sometimes omitted, causing errors.
- **How we solved it:**
  - Updated the message construction logic to always include `"content": null` for assistant tool-calling messages.

## 7. Fallback Logic for LLM Silence
- **Issue:** Sometimes the LLM would return an empty response or a placeholder like `<tool-use></tool-use>`, leaving the user with no answer.
- **How we solved it:**
  - Added fallback logic to detect these cases (using regex) and display the tool result directly to the user, ensuring a meaningful response every time.

## 8. Diagnostics for Groq API Errors
- **Issue:** When Groq returned an error, the client only showed a generic message, making it hard to debug issues like invalid payloads or API key problems.
- **How we solved it:**
  - Enhanced error handling to print the full HTTP status code, headers, and raw response body for every Groq API error.
  - This allowed us to see the exact error returned by Groq and quickly identify root causes.

## 9. Incorrect Tool Call Key (`parameters` vs `arguments`)
- **Issue:** The OpenAI-compatible API expects tool call arguments under the `arguments` key (as a JSON string), not `parameters`. Our code was sending `parameters`, causing Groq to fail tool calls.
- **How we solved it:**
  - Updated the message sanitization logic to always use `arguments` (never `parameters`) and ensure it is a JSON string.
  - Verified this by inspecting Groq's error diagnostics and matching the API docs.

## 10. User Experience Polishing
- **Issue:** The output was cluttered with debug lines, and users sometimes saw no result or confusing messages.
- **How we solved it:**
  - Cleaned up the output, added a welcome/help message, separators, and ensured that a meaningful result is always shown, even if the LLM is silent.

---

**Summary of our debugging process:**
- We started by enabling detailed diagnostics and printing all API responses.
- Each time an error was encountered, we used the new diagnostics to pinpoint the root cause (e.g., payload format, missing fields, wrong key names).
- We iteratively fixed each issue, re-tested, and confirmed the fix by observing the improved API response or successful tool call.
- The final result is a robust, user-friendly MCP client that works seamlessly with Groq's tool-calling API and provides clear diagnostics for any future issues.

*Document last updated: March 15, 2024*
