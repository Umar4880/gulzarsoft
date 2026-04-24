import asyncio

from client import run_flow


def main() -> None:
    result = asyncio.run(run_flow())

    tools = result.get("tools", [])
    if "echo" not in tools or "server_health" not in tools:
        raise RuntimeError(f"Missing expected tools. Got: {tools}")

    echo_payload = result.get("echo")
    if not echo_payload:
        raise RuntimeError("Echo tool returned no payload.")

    print("Day-2 MCP tool invocation flow passed.")


if __name__ == "__main__":
    main()
