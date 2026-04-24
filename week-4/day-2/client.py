import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_flow() -> dict[str, object]:
    base_dir = Path(__file__).resolve().parent
    server_script = str(base_dir / "server.py")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            echo_result = await session.call_tool("echo", {"text": "Hello MCP from day-2"})
            health_result = await session.call_tool("server_health", {})

    return {
        "tools": [tool.name for tool in tools_result.tools],
        "echo": echo_result.content,
        "server_health": health_result.content,
    }


def to_json(data: dict[str, object]) -> str:
    return json.dumps(data, indent=2, default=str)


if __name__ == "__main__":
    output = asyncio.run(run_flow())
    print(to_json(output))
