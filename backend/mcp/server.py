"""
NewsMind AI - MCP Server
Exposes MCP tools via stdio for external agent integration.
"""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from backend.mcp.tools import MCP_TOOLS
from backend.utils.logging import setup_logger

logger = setup_logger("mcp_server")

app = Server("newsmind-mcp")


def _build_tools() -> list[Tool]:
    tools = []
    for name, spec in MCP_TOOLS.items():
        tools.append(Tool(
            name=name,
            description=spec["description"],
            inputSchema={
                "type": "object",
                "properties": spec.get("parameters", {}),
            },
        ))
    return tools


@app.list_tools()
async def list_tools() -> list[Tool]:
    return _build_tools()


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name not in MCP_TOOLS:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    fn = MCP_TOOLS[name]["function"]
    try:
        result = await fn(**arguments)
        return [TextContent(type="text", text=json.dumps(result, default=str))]
    except Exception as e:
        logger.error(f"MCP tool {name} failed: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
