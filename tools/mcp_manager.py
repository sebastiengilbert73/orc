import os
import json
import asyncio
import shutil
import inspect
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_servers.json")

DEFAULT_MCP_CONFIG = {
    "servers": {
        "filesystem": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ],
            "env": {},
            "enabled": True
        }
    }
}

def resolve_command(command: str) -> str:
    """
    Resolves executable command path (e.g. npx -> npx.cmd on Windows).
    """
    resolved = shutil.which(command)
    return resolved if resolved else command

def load_mcp_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {CONFIG_PATH}: {e}")
    return DEFAULT_MCP_CONFIG

def save_mcp_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

async def _call_mcp_tool_async(command: str, args: list, env: dict, tool_name: str, arguments: dict) -> str:
    cmd_path = resolve_command(command)
    env_params = {**os.environ, **(env or {})}
    server_params = StdioServerParameters(
        command=cmd_path,
        args=args or [],
        env=env_params
    )
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments or {})
                
                output_parts = []
                if hasattr(result, 'content') and result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            output_parts.append(item.text)
                        else:
                            output_parts.append(str(item))
                
                if output_parts:
                    return "\n".join(output_parts)
                return "Tool executed successfully with empty output."
    except Exception as e:
        return f"MCP Tool Execution Error ({tool_name}): {e}"

async def _list_mcp_server_tools_async(command: str, args: list, env: dict) -> List[dict]:
    cmd_path = resolve_command(command)
    env_params = {**os.environ, **(env or {})}
    server_params = StdioServerParameters(
        command=cmd_path,
        args=args or [],
        env=env_params
    )
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                
                tools_list = []
                for tool in tools_result.tools:
                    schema = getattr(tool, 'input_schema', None) or getattr(tool, 'inputSchema', None) or {}
                    if hasattr(schema, 'model_dump'):
                        schema = schema.model_dump()
                    elif not isinstance(schema, dict):
                        schema = {}

                    tools_list.append({
                        "name": tool.name,
                        "description": tool.description or f"MCP tool {tool.name}",
                        "inputSchema": schema
                    })
                return tools_list
    except Exception as e:
        print(f"Error listing MCP tools for {command}: {e}")
        return []

from concurrent.futures import ThreadPoolExecutor

def run_async_in_event_loop(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def call_mcp_tool(server_name: str, tool_name: str, arguments: dict) -> str:
    config = load_mcp_config()
    servers = config.get("servers", {})
    srv = servers.get(server_name)
    if not srv or not srv.get("enabled", True):
        return f"Error: MCP Server '{server_name}' is not configured or disabled."
    
    coro = _call_mcp_tool_async(
        command=srv["command"],
        args=srv.get("args", []),
        env=srv.get("env", {}),
        tool_name=tool_name,
        arguments=arguments
    )
    
    try:
        return run_async_in_event_loop(coro)
    except Exception as e:
        return f"Error running MCP tool call: {e}"

_MCP_TOOLS_CACHE = None

def get_mcp_tools_metadata(use_cache: bool = True) -> List[dict]:
    global _MCP_TOOLS_CACHE
    if use_cache and _MCP_TOOLS_CACHE is not None:
        return _MCP_TOOLS_CACHE

    config = load_mcp_config()
    servers = config.get("servers", {})
    all_tools = []
    
    for server_name, srv in servers.items():
        if not srv.get("enabled", True):
            continue
            
        coro = _list_mcp_server_tools_async(
            command=srv["command"],
            args=srv.get("args", []),
            env=srv.get("env", {})
        )
        try:
            tools = run_async_in_event_loop(coro)
            for t in tools:
                t["server_name"] = server_name
                t["prefixed_name"] = f"mcp_{server_name}_{t['name']}"
                all_tools.append(t)
        except Exception as e:
            print(f"Failed to fetch tools for MCP server '{server_name}': {e}")
            
    _MCP_TOOLS_CACHE = all_tools
    return all_tools

def create_mcp_tool_function(server_name: str, tool_name: str, description: str, prefixed_name: str, input_schema: dict = None):
    def mcp_tool_wrapper(**kwargs) -> str:
        return call_mcp_tool(server_name, tool_name, kwargs)
        
    mcp_tool_wrapper.__name__ = prefixed_name
    mcp_tool_wrapper.__doc__ = description

    if input_schema and isinstance(input_schema, dict):
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        params = []
        for prop_name in properties.keys():
            default_val = inspect.Parameter.empty if prop_name in required else None
            param = inspect.Parameter(
                name=prop_name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default_val,
                annotation=str
            )
            params.append(param)
        if params:
            mcp_tool_wrapper.__signature__ = inspect.Signature(params)

    return mcp_tool_wrapper

def get_compiled_mcp_tools() -> list:
    metadata = get_mcp_tools_metadata()
    compiled = []
    for meta in metadata:
        func = create_mcp_tool_function(
            server_name=meta["server_name"],
            tool_name=meta["name"],
            description=meta["description"],
            prefixed_name=meta["prefixed_name"],
            input_schema=meta.get("inputSchema")
        )
        compiled.append(func)
    return compiled

def get_mcp_server_names() -> List[str]:
    config = load_mcp_config()
    servers = config.get("servers", {})
    return [f"mcp_{srv_name}" for srv_name, srv in servers.items() if srv.get("enabled", True)]

def expand_mcp_tool_names(tools_list: List[str]) -> List[str]:
    expanded = set()
    metadata = get_mcp_tools_metadata()
    server_to_tools = {}
    for meta in metadata:
        srv_key = f"mcp_{meta['server_name']}"
        if srv_key not in server_to_tools:
            server_to_tools[srv_key] = []
        server_to_tools[srv_key].append(meta["prefixed_name"])
        
    for item in tools_list:
        if item in server_to_tools:
            expanded.update(server_to_tools[item])
        else:
            expanded.add(item)
    return list(expanded)
