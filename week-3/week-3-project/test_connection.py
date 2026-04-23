import sys
import asyncio

print("=== Starting connection test ===", file=sys.stderr)

try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage
    
    print("✓ Imports successful", file=sys.stderr)
    
    llm = ChatOllama(
        model="llama3.2:latest", 
        base_url="http://192.168.10.11:11434"
    )
    print("✓ ChatOllama instance created", file=sys.stderr)
    
    # Try a simple invoke
    response = llm.invoke([
        HumanMessage(content="explain redis in simple terms")
    ])
    print(f"✓ Response: {response}", file=sys.stderr)
    
except Exception as e:
    print(f"✗ ERROR: {type(e).__name__}: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("=== Test complete ===", file=sys.stderr)
