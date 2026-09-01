import pytest
import os
from tools.mcp_manager import (
    load_mcp_config,
    save_mcp_config,
    call_mcp_tool,
    create_mcp_tool_function,
    get_mcp_server_names,
    expand_mcp_tool_names,
    add_mcp_server,
    toggle_mcp_server,
    delete_mcp_server
)
from tools.registry import get_all_compiled_tools, execute_tool

def test_mcp_config_defaults():
    config = load_mcp_config()
    assert "servers" in config
    assert "filesystem" in config["servers"]
    assert "sqlite" in config["servers"]
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
    assert "mcp_sqlite" in servers
    
    # Test expanding server-level name to underlying tools
    expanded = expand_mcp_tool_names(["get_weather", "mcp_filesystem", "mcp_sqlite"])
    assert "get_weather" in expanded
    assert any(t.startswith("mcp_filesystem_") for t in expanded)
    assert any(t.startswith("mcp_sqlite_") for t in expanded)

def test_mcp_execute_tool_routing_disabled_or_invalid():
    res = execute_tool("mcp_unknownserver_some_tool", {"path": "test.txt"})
    assert "Error: MCP Server 'unknownserver' is not configured or disabled" in res or "MCP Tool Execution Error" in res

def test_dynamic_mcp_server_management():
    # Test adding a dummy server
    srv = add_mcp_server(
        name="test_memory",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-memory"],
        env={"TEST_KEY": "VAL"},
        enabled=True
    )
    assert srv["command"] == "npx"
    assert "mcp_test_memory" in get_mcp_server_names()

    # Test toggling server
    toggled = toggle_mcp_server("test_memory")
    assert toggled["enabled"] is False
    assert "mcp_test_memory" not in get_mcp_server_names()

    # Test deleting server
    deleted = delete_mcp_server("test_memory")
    assert deleted is True
    assert "mcp_test_memory" not in get_mcp_server_names()

def test_local_mcp_server_management():
    # Test adding a local-only server
    srv = add_mcp_server(
        name="my_private_server",
        command="uvx",
        args=["mcp-server-fetch"],
        is_local=True
    )
    assert srv["is_local"] is True
    assert "mcp_my_private_server" in get_mcp_server_names()

    # Cleanup local server
    deleted = delete_mcp_server("my_private_server")
    assert deleted is True
    assert "mcp_my_private_server" not in get_mcp_server_names()

