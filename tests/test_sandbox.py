import pytest
from tools.sandbox import run_custom_tool_in_sandbox

def test_sandbox_normal_execution():
    code = """
def test_add(a: int, b: int) -> int:
    return a + b
"""
    res = run_custom_tool_in_sandbox(code, "test_add", {"a": 10, "b": 20}, timeout_seconds=5)
    assert res == "30"

def test_sandbox_infinite_loop_timeout():
    code = """
import time
def infinite_loop() -> str:
    while True:
        time.sleep(0.1)
    return "done"
"""
    res = run_custom_tool_in_sandbox(code, "infinite_loop", {}, timeout_seconds=2)
    assert "exceeded maximum execution timeout" in res

def test_sandbox_exception_handling():
    code = """
def failing_tool() -> str:
    raise ValueError("Something went wrong inside tool!")
"""
    res = run_custom_tool_in_sandbox(code, "failing_tool", {}, timeout_seconds=5)
    assert "Error executing failing_tool" in res
    assert "Something went wrong inside tool!" in res
