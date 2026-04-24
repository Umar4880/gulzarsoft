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
            add_result = await session.call_tool("add", {"a": 7, "b": 5})
            status_result = await session.call_tool("get_status", {})

    return {
        "tools": [tool.name for tool in tools_result.tools],
        "add": add_result.content,
        "status": status_result.content,
    }


def _to_json(data: dict[str, object]) -> str:
    return json.dumps(data, indent=2, default=str)


if __name__ == "__main__":
    result = asyncio.run(run_flow())
    print(_to_json(result))
