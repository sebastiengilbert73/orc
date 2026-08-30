import pytest
import numpy as np
import math
from tools.security import safe_eval_math, validate_custom_tool_ast, is_safe_package_name

# --- 1. Tests for safe_eval_math ---

def test_safe_eval_math_basic_arithmetic():
    assert safe_eval_math("2 + 2") == 4
    assert safe_eval_math("10 - 3 * 2") == 4
    assert safe_eval_math("2 ** 3") == 8
    assert safe_eval_math("10 / 2") == 5.0
    assert safe_eval_math("10 % 3") == 1
    assert safe_eval_math("-5 + +3") == -2

def test_safe_eval_math_functions_and_constants():
    assert math.isclose(safe_eval_math("sin(pi / 2)"), 1.0)
    assert math.isclose(safe_eval_math("cos(0)"), 1.0)
    assert safe_eval_math("sqrt(16)") == 4.0
    assert safe_eval_math("abs(-42)") == 42
    assert math.isclose(safe_eval_math("exp(0)"), 1.0)

def test_safe_eval_math_with_variables():
    assert safe_eval_math("x**2 + 2*x + 1", {"x": 3}) == 16
    
    # Test with numpy array
    x_arr = np.array([1.0, 2.0, 3.0])
    res = safe_eval_math("x**2", {"x": x_arr})
    np.testing.assert_array_equal(res, np.array([1.0, 4.0, 9.0]))

def test_safe_eval_math_security_rejections():
    # Attempting code injection via __import__
    with pytest.raises(ValueError):
        safe_eval_math("__import__('os').system('dir')")

    # Attempting dunder attribute access
    with pytest.raises(ValueError):
        safe_eval_math("(''.__class__.__mro__[1].__subclasses__())")

    # Attempting giant exponentiation DOS
    with pytest.raises(ValueError, match="Exponent exceeds maximum"):
        safe_eval_math("10 ** 10000")

    # Attempting lambda
    with pytest.raises(ValueError):
        safe_eval_math("(lambda x: x + 1)(2)")


# --- 2. Tests for validate_custom_tool_ast ---

def test_validate_custom_tool_ast_valid():
    valid_code = """
def my_custom_tool(name: str, count: int) -> str:
    \"\"\"Valid tool docstring.\"\"\"
    res = name * count
    return res
"""
    # Should not raise any exception
    validate_custom_tool_ast(valid_code, "my_custom_tool")

def test_validate_custom_tool_ast_missing_function():
    code = "def wrong_name(): pass"
    with pytest.raises(ValueError, match="must define a function named 'expected_tool'"):
        validate_custom_tool_ast(code, "expected_tool")

def test_validate_custom_tool_ast_forbidden_imports():
    code_os = "import os\ndef test_tool(): pass"
    with pytest.raises(ValueError, match="Import of module 'os' is forbidden"):
        validate_custom_tool_ast(code_os, "test_tool")

    code_sub = "from subprocess import Popen\ndef test_tool(): pass"
    with pytest.raises(ValueError, match="Import from module 'subprocess' is forbidden"):
        validate_custom_tool_ast(code_sub, "test_tool")

def test_validate_custom_tool_ast_forbidden_functions():
    code_eval = "def test_tool(): eval('2+2')"
    with pytest.raises(ValueError, match="Call to function 'eval' is forbidden"):
        validate_custom_tool_ast(code_eval, "test_tool")

    code_exec = "def test_tool(): exec('pass')"
    with pytest.raises(ValueError, match="Call to function 'exec' is forbidden"):
        validate_custom_tool_ast(code_exec, "test_tool")

def test_validate_custom_tool_ast_dunder_access():
    code_dunder = "def test_tool(): x = (1).__class__.__subclasses__"
    with pytest.raises(ValueError, match="Access to special attribute"):
        validate_custom_tool_ast(code_dunder, "test_tool")


# --- 3. Tests for is_safe_package_name ---

def test_is_safe_package_name():
    assert is_safe_package_name("numpy") is True
    assert is_safe_package_name("beautifulsoup4") is True
    assert is_safe_package_name("scikit-learn") is True
    assert is_safe_package_name("python_dotenv") is True

    # Malicious inputs
    assert is_safe_package_name("requests; rm -rf /") is False
    assert is_safe_package_name("package && dir") is False
    assert is_safe_package_name("pkg|calc") is False
    assert is_safe_package_name("") is False
