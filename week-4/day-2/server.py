import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

mcp = FastMCP(os.getenv("MCP_SERVER_NAME", "Week4Day2Server"))


@mcp.tool()
def echo(text: str) -> str:
    """Return the same text back to the client."""
    return text


@mcp.tool()
def server_health() -> dict[str, str]:
    """Return basic server metadata and health."""
    return {
        "server": os.getenv("MCP_SERVER_NAME", "Week4Day2Server"),
        "status": "healthy",
        "utc_time": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
