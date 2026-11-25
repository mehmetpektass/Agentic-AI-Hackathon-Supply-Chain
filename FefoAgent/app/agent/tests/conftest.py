"""Backend'i yapılandırmayla seçen MCP fixture'ı (varsayılan: stub). Aynı testler sonradan fefo_mcp ile koşar."""
import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

APP_DIR = Path(__file__).resolve().parents[1]


class McpHarness:
    def __init__(self, module: str):
        self.module = module
        self.stray_stdout: list[str] = []

    async def _call_async(self, name: str, args: dict):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(APP_DIR)
        params = StdioServerParameters(command=sys.executable, args=["-m", self.module],
                                       env=env, cwd=str(APP_DIR))
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as session:
                await session.initialize()
                res = await session.call_tool(name, args)
                text = "".join(c.text for c in res.content if getattr(c, "text", None))
                return json.loads(text)

    def call(self, name: str, **args):
        return asyncio.run(self._call_async(name, args))


@pytest.fixture(scope="session")
def mcp_backend() -> McpHarness:
    backend = os.environ.get("MCP_BACKEND", "stub")
    return McpHarness("fefo_mcp_stub" if backend == "stub" else "fefo_mcp")
