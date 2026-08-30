# 🧪 Automated Testing — ORC (Agentic AI Orchestration Engine)

This directory contains the complete automated unit and integration test suite for the **ORC** project, built using `pytest` and `pytest-cov`.

---

## 🚀 How to Run Tests Manually

All commands should be executed from the root directory of the project (`c:\Users\sebas\Documents\projects\orc`).

### 1. Run All Tests
To execute the entire 26-test suite:
```powershell
.\.venv\orc\Scripts\python.exe -m pytest tests/
```

### 2. Run Tests with Code Coverage Report
To display code coverage by module (`pytest-cov`):
```powershell
.\.venv\orc\Scripts\python.exe -m pytest --cov=. tests/
```

### 3. Run Tests in Verbose Mode
To display individual test names and detailed execution duration:
```powershell
.\.venv\orc\Scripts\python.exe -m pytest -v tests/
```

### 4. Run a Specific Test File
Target a single test file when working on a specific component:
```powershell
# Example: Test AST security rules only
.\.venv\orc\Scripts\python.exe -m pytest tests/test_security.py

# Example: Test Subprocess Sandbox isolation only
.\.venv\orc\Scripts\python.exe -m pytest tests/test_sandbox.py

# Example: Test FastAPI REST API endpoints only
.\.venv\orc\Scripts\python.exe -m pytest tests/test_api.py
```

### 5. Run a Specific Test Function by Name (-k filter)
To execute a single test function:
```powershell
.\.venv\orc\Scripts\python.exe -m pytest tests/test_security.py -k "test_safe_eval_math_basic_arithmetic"
```

---

## 📂 Test Files Architecture

| File | Domain Tested | Description |
| :--- | :--- | :--- |
| **`test_security.py`** | AST Security | Code AST validation, `safe_eval_math` evaluator (without `eval`), `pip` injection regex filtering, and dunder attribute checks. |
| **`test_sandbox.py`** | Subprocess Sandbox | Execution of Custom Tools inside isolated native subprocesses, hard timeout enforcement (15s), and automatic termination of `while True` infinite loops. |
| **`test_api.py`** | REST API Endpoints | Integration tests for FastAPI endpoints (`/agents`, `/tasks`, `/custom-tools`, `/memory`, `/config`, toggle, wipe, delete, and security rejection). |
| **`test_memory.py`** | SQL Memory | CRUD operations for `MemoryManager` (add, retrieve by task/agent, and wipe memory). |
| **`test_tools.py`** | Native Static Tools | Document & plot generation (`write_to_md`, `write_to_pdf`, `create_1d_plot`), file reading (`read_text`, `list_directory`), and `calculator`. |
| **`test_task_manager.py`** | Async Task Engine | Asynchronous task lifecycle management and Human-in-the-Loop pause/resume (`ask_user`). |

---

## ⚙️ Prerequisites and Setup

Test dependencies are installed in the local virtual environment:
* `pytest` (v9.1+)
* `pytest-cov` (v7.1+)

If setting up a fresh environment, install test requirements using:
```powershell
.\.venv\orc\Scripts\python.exe -m pip install pytest pytest-cov
```
