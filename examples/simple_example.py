"""Minimal example showing DrasiTool configuration without requiring a running server.

This example demonstrates:
1. How to configure the tool
2. Tool structure and methods
3. Expected usage patterns

To actually run queries, you need a running Drasi MCP server.
"""

import os
import sys
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    stream=sys.stdout
)

from langchain_drasi import create_drasi_tool, MCPConnectionConfig
from langchain_drasi.handlers import ConsoleHandler

# Load environment variables
load_dotenv()


def main():
    """Demonstrate tool configuration."""
    print("=" * 60)
    print("Drasi Tool Configuration Example")
    print("=" * 60)

    # Configure connection to Drasi MCP server
    config = MCPConnectionConfig(
        server_url=os.getenv("DRASI_SERVER_URL", "http://localhost:8083"),
        headers={
            "Authorization": f"Bearer {os.getenv('DRASI_API_TOKEN')}"
        } if os.getenv("DRASI_API_TOKEN") else None,
        timeout=30.0,
    )

    print(f"\nServer URL: {config.server_url}")
    print(f"Has auth headers: {config.headers is not None}")
    print(f"Timeout: {config.timeout}s")

    # Create notification handler
    handler = ConsoleHandler(include_timestamp=True, pretty_print=True)

    # Create the tool
    tool = create_drasi_tool(
        mcp_config=config,
        notification_handlers=[handler],
    )

    print(f"\n✓ Tool created successfully!")
    print(f"  Tool name: {tool.name}")
    print(f"  Description: {tool.description}")
    print(f"\nTool operations:")
    print(f"  - discover: List available queries")
    print(f"  - read: Read current query results")
    print(f"  - subscribe: Subscribe to query updates")
    print(f"  - unsubscribe: Unsubscribe from query")

    print(f"\nTo use this tool with an agent:")
    print(f"  1. Ensure your Drasi MCP server is running at {config.server_url}")
    print(f"  2. Pass the tool to your LangChain agent")
    print(f"  3. The agent can invoke it with query_name and operation parameters")

    print(f"\nExample tool invocation (requires running server):")
    print(f'  await tool.ainvoke({{"query_name": "my-query", "operation": "read"}})')

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
