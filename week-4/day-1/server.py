import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

mcp = FastMCP(os.getenv("MCP_SERVER_NAME", "Week4PracticeServer"))


@mcp.tool()
def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


@mcp.tool()
def get_status() -> dict[str, str]:
    """Return basic server status details."""
    return {
        "server": os.getenv("MCP_SERVER_NAME", "Week4PracticeServer"),
        "utc_time": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
