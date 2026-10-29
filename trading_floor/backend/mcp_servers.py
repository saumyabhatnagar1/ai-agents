import os
from pathlib import Path
from .market import massive_api_key
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio, create_static_tool_filter


load_dotenv(override=True)

PROJECT_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = PROJECT_DIR / "memory"
tavily_env = {"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")}
TIMEOUT = 120


market_params = {
    "command": "uvx",
        "args": [
            "--with", "mcp<2",
            "--from", "git+https://github.com/massive-com/mcp_massive@v0.10.0",
            "mcp_massive"
        ],
    "env": {"MASSIVE_API_KEY": massive_api_key},
}

def trader_mcp_servers() -> list[MCPServerStdio]:
    """ The trader's MCP servers. """
    params_list = [
        {"command": "uv", "args": ["run", "-m", "backend.accounts_server"], "cwd": str(PROJECT_DIR)},
        {"command": "uv", "args": ["run", "-m", "backend.push_server"], "cwd": str(PROJECT_DIR)},
        market_params,
    ]
    return [MCPServerStdio(p, client_session_timeout_seconds=TIMEOUT) for p in params_list]

def researcher_mcp_servers(name: str) -> list[MCPServerStdio]:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    memory_db = MEMORY_DIR / f"{name}.db"
    fetch = MCPServerStdio(
        {"command": "uvx", "args": ["--with", "mcp<2","mcp-server-fetch"]},
        client_session_timeout_seconds=TIMEOUT,
    )
    search = MCPServerStdio(
        {"command": "npx", "args": ["-y", "tavily-mcp@latest"], "env": tavily_env},
        client_session_timeout_seconds=TIMEOUT,
        tool_filter=create_static_tool_filter(allowed_tool_names=["tavily_search"]),
    )

    memory = MCPServerStdio(
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {
                "LIBSQL_URL": f"file:{memory_db}",
                "NODE_OPTIONS": f"--require {PROJECT_DIR / 'backend' / 'custom_event_polyfill.cjs'}",
            },
        },
        client_session_timeout_seconds=TIMEOUT,
    )

    return [fetch, search, memory]
