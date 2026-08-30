import ast
import math
import re
from typing import Dict, Any, Union
import numpy as np

# Allowed math functions for AST evaluation
ALLOWED_FUNCTIONS: Dict[str, Any] = {
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'asin': np.arcsin,
    'acos': np.arccos,
    'atan': np.arctan,
    'exp': np.exp,
    'log': np.log,
    'log10': np.log10,
    'sqrt': np.sqrt,
    'abs': np.abs,
    'sinc': lambda val: np.where(val == 0, 1.0, np.sin(val) / val) if isinstance(val, np.ndarray) else (1.0 if val == 0 else math.sin(val) / val),
    'min': np.minimum,
    'max': np.maximum,
}

ALLOWED_CONSTANTS: Dict[str, Any] = {
    'pi': math.pi,
    'e': math.e,
}

def _eval_node(node: ast.AST, variables: Dict[str, Any]) -> Union[int, float, np.ndarray]:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, variables)

    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, bool)):
            return node.value
        raise ValueError(f"Literal value '{node.value}' of type {type(node.value).__name__} is not allowed in math expressions.")

    elif hasattr(ast, "Num") and isinstance(node, getattr(ast, "Num")):
        return node.n

    elif isinstance(node, ast.Name):
        if variables and node.id in variables:
            return variables[node.id]
        if node.id in ALLOWED_CONSTANTS:
            return ALLOWED_CONSTANTS[node.id]
        raise ValueError(f"Variable or identifier '{node.id}' is not defined or allowed.")

    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, variables)
        if isinstance(node.op, ast.USub):
            return -operand
        elif isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError(f"Unary operator '{type(node.op).__name__}' is not supported.")

    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left, variables)
        right = _eval_node(node.right, variables)
        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        elif isinstance(node.op, ast.Div):
            return left / right
        elif isinstance(node.op, ast.Pow):
            if isinstance(right, (int, float)) and right > 1000:
                raise ValueError("Exponent exceeds maximum allowed limit (1000).")
            return left ** right
        elif isinstance(node.op, ast.Mod):
            return left % right
        elif isinstance(node.op, ast.FloorDiv):
            return left // right
        raise ValueError(f"Binary operator '{type(node.op).__name__}' is not supported.")

    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct math function calls (e.g., sin(x)) are allowed.")
        func_name = node.func.id
        if func_name not in ALLOWED_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not in the allowed math functions list.")

        args = [_eval_node(arg, variables) for arg in node.args]
        return ALLOWED_FUNCTIONS[func_name](*args)

    else:
        raise ValueError(f"Syntax element '{type(node).__name__}' is not allowed in math expressions.")

def safe_eval_math(expression: str, variables: Dict[str, Any] = None) -> Union[int, float, np.ndarray]:
    """
    Safely evaluates a mathematical expression string using Python's AST module.
    Does NOT use eval(). Rejects any dangerous attributes, imports, or statement nodes.
    """
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Expression must be a non-empty string.")

    tree = ast.parse(expression.strip(), mode='eval')
    return _eval_node(tree, variables or {})


FORBIDDEN_MODULES = {
    'os', 'sys', 'subprocess', 'shutil', 'importlib', 'builtins',
    'ctypes', 'socket', 'threading', 'multiprocessing', 'signal',
    'pty', 'tty', 'winreg', 'msvcrt'
}

FORBIDDEN_FUNCTIONS = {
    'eval', 'exec', 'compile', '__import__', 'globals', 'locals',
    'getattr', 'setattr', 'delattr', 'breakpoint', 'input'
}

def validate_custom_tool_ast(python_code: str, expected_name: str) -> None:
    """
    Validates Python code for custom tools using AST parsing.
    Enforces security constraints and ensures function definition exists.
    """
    try:
        tree = ast.parse(python_code)
    except SyntaxError as se:
        raise ValueError(f"Syntax error in custom tool code: {se}")

    function_found = False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == expected_name:
                function_found = True

        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__") and node.attr.endswith("__"):
                raise ValueError(f"Access to special attribute '{node.attr}' is forbidden for security reasons.")

        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_root = alias.name.split('.')[0]
                if mod_root in FORBIDDEN_MODULES:
                    raise ValueError(f"Import of module '{alias.name}' is forbidden for security reasons.")

        if isinstance(node, ast.ImportFrom):
            if node.module:
                mod_root = node.module.split('.')[0]
                if mod_root in FORBIDDEN_MODULES:
                    raise ValueError(f"Import from module '{node.module}' is forbidden for security reasons.")

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_FUNCTIONS:
                    raise ValueError(f"Call to function '{node.func.id}' is forbidden for security reasons.")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'open':
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
                if any(m in mode for m in ('w', 'a', '+')):
                    if len(node.args) >= 1 and isinstance(node.args[0], ast.Constant):
                        filepath = str(node.args[0].value)
                        if not ("output/" in filepath or "output\\" in filepath):
                            raise ValueError(f"Writing to files outside 'output/' directory is forbidden.")

    if not function_found:
        raise ValueError(f"The Python code must define a function named '{expected_name}'.")


SAFE_PACKAGE_NAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-]+$')

def is_safe_package_name(package_name: str) -> bool:
    """
    Validates package name format to prevent shell injection during pip install.
    """
    if not isinstance(package_name, str):
        return False
    return bool(SAFE_PACKAGE_NAME_REGEX.match(package_name.strip()))
