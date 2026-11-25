"""MCP_Adapter: MCP_BACKEND değerine göre stub veya fefo_mcp modülünü stdio alt süreci olarak başlatır."""
import importlib.util
import logging
import os
import sys
from pathlib import Path

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from strands.tools.mcp import MCPClient

import config

logger = logging.getLogger("fefo_agent.mcp_adapter")
APP_DIR = str(Path(__file__).resolve().parent)
PASSTHROUGH_KEYS = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
                    "AWS_REGION", "AWS_DEFAULT_REGION", "REPORTS_BUCKET")


def module_name(backend: str) -> str:
    return "fefo_mcp_stub" if backend == "stub" else "fefo_mcp"


def _libpython_dirs() -> list[str]:
    """AgentCore runtime'da sys.executable sarmalayıcının arkasındaki gerçek binary'dir ve
    libpython için LD_LIBRARY_PATH gerekir. Yorumlayıcının üst dizinlerindeki lib klasörleri aranır."""
    found = []
    for parent in Path(sys.executable).resolve().parents:
        lib = parent / "lib"
        if lib.is_dir() and any(lib.glob("libpython*.so*")):
            found.append(str(lib))
    return found


def build_child_env() -> dict[str, str]:
    """Mevcut ortamın kopyası. İçerik asla loglanmaz."""
    env = dict(os.environ)
    for key in PASSTHROUGH_KEYS:
        if key in os.environ:
            env[key] = os.environ[key]
    libs = _libpython_dirs()
    if libs:
        env["LD_LIBRARY_PATH"] = os.pathsep.join(libs + [p for p in [env.get("LD_LIBRARY_PATH")] if p])
    env["PYTHONPATH"] = os.pathsep.join(p for p in (APP_DIR, env.get("PYTHONPATH", "")) if p)
    return env


def build_mcp_client() -> MCPClient:
    module = module_name(config.get_mcp_backend())
    if importlib.util.find_spec(module) is None:
        logger.error("MCP modülü içe aktarılamadı: %s", module)
        raise ImportError(f"MCP modülü bulunamadı: {module}")
    params = StdioServerParameters(command=sys.executable, args=["-m", module],
                                   env=build_child_env())
    return MCPClient(lambda: stdio_client(params))
