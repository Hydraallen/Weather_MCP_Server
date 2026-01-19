# Weather MCP Server

A Python-based Model Context Protocol (MCP) server for weather data, running in a Docker container and connecting to Claude Desktop via Stdio.

## Quick Start

### 1. Build the Docker Image
Run the following command in the project root. This packages the Python environment.
```bash
docker-compose build
```
> **Note:** You do not need to run `docker-compose up`. Claude will launch the container automatically.

### 2. Configure Claude Desktop
Copy the content from the included `claude_desktop_config.json` to your system's configuration file.

**Config File Locations:**
*   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
*   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "weather-docker": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "MCP_TRANSPORT=stdio",
        "weather-mcp-weather-mcp"
      ]
    }
  }
}
```
> **⚠️ Important:** Ensure the image name in `args` (`weather-mcp-weather-mcp`) matches the one built by your docker-compose. Check it via `docker images`.

### 3. Restart & Test
1.  **Fully Quit** Claude Desktop and restart it.
2.  Ask Claude: 
    1.  *"What is the current weather in Chicago?"*
    2.  *"What is the weather forecast for Chicago for the next 5 days?"*
    3.  *"Are there any severe weather alerts for Chicago?"*
