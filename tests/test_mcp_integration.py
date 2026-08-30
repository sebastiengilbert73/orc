import pytest
import os
from tools.mcp_manager import (
    load_mcp_config,
    save_mcp_config,
    call_mcp_tool,
    create_mcp_tool_function,
    get_mcp_server_names,
    expand_mcp_tool_names
)
from tools.registry import get_all_compiled_tools, execute_tool

def test_mcp_config_defaults():
    config = load_mcp_config()
    assert "servers" in config
    assert "filesystem" in config["servers"]
    srv = config["servers"]["filesystem"]
    assert srv["command"] == "npx"

def test_mcp_wrapper_function_creation():
    wrapper = create_mcp_tool_function(
        server_name="filesystem",
        tool_name="read_file",
        description="Reads a file from disk",
        prefixed_name="mcp_filesystem_read_file"
    )
    assert wrapper.__name__ == "mcp_filesystem_read_file"
    assert wrapper.__doc__ == "Reads a file from disk"

def test_mcp_server_names_and_expansion():
    servers = get_mcp_server_names()
    assert "mcp_filesystem" in servers
    
    # Test expanding server-level name to underlying tools
    expanded = expand_mcp_tool_names(["get_weather", "mcp_filesystem"])
    assert "get_weather" in expanded
    # Check that individual filesystem tools were expanded
    assert any(t.startswith("mcp_filesystem_") for t in expanded)

def test_mcp_execute_tool_routing_disabled_or_invalid():
    res = execute_tool("mcp_unknownserver_some_tool", {"path": "test.txt"})
    assert "Error: MCP Server 'unknownserver' is not configured or disabled" in res or "MCP Tool Execution Error" in res
