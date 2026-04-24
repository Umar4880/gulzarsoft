import asyncio

from client import run_flow


def main() -> None:
    result = asyncio.run(run_flow())

    tools = result.get("tools", [])
    if "add" not in tools or "get_status" not in tools:
        raise RuntimeError(f"Expected tools not found. Got: {tools}")

    add_payload = result.get("add")
    if not add_payload:
        raise RuntimeError("No payload returned from add tool.")

    print("Tool invocation flow passed.")


if __name__ == "__main__":
    main()
