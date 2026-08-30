import multiprocessing
import sys
import traceback
from typing import Dict, Any, Tuple, Optional

def _custom_tool_worker(python_code: str, func_name: str, kwargs: dict, result_queue: multiprocessing.Queue):
    """
    Worker function executed inside an isolated subprocess.
    Compiles the code, calls the target function, and sends the result back via Queue.
    """
    try:
        local_scope = {}
        compiled = compile(python_code, "<string>", "exec")
        exec(compiled, local_scope)
        func = local_scope.get(func_name)
        if not func:
            result_queue.put({"success": False, "error": f"Function '{func_name}' not found in compiled code."})
            return

        result = func(**kwargs)
        result_queue.put({"success": True, "result": str(result)})
    except Exception as e:
        tb = traceback.format_exc()
        result_queue.put({"success": False, "error": f"Error executing {func_name}: {e}"})

def run_custom_tool_in_sandbox(python_code: str, func_name: str, kwargs: dict, timeout_seconds: int = 15) -> str:
    """
    Executes a custom tool function in an isolated subprocess with a hard timeout.
    If the execution exceeds timeout_seconds (e.g. infinite loop), the process is forcefully killed.
    """
    ctx = multiprocessing.get_context("spawn")
    result_queue = ctx.Queue()

    proc = ctx.Process(
        target=_custom_tool_worker,
        args=(python_code, func_name, kwargs, result_queue)
    )

    try:
        proc.start()
        proc.join(timeout=timeout_seconds)

        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=1)
            if proc.is_alive():
                proc.kill()
            return f"Error: Custom tool '{func_name}' exceeded maximum execution timeout ({timeout_seconds}s) and was terminated."

        if not result_queue.empty():
            data = result_queue.get_nowait()
            if data.get("success"):
                return data.get("result", "")
            else:
                return data.get("error", f"Execution of '{func_name}' failed.")

        return f"Error: Custom tool '{func_name}' finished without returning a result."

    except Exception as e:
        if proc.is_alive():
            proc.kill()
        return f"Error running sandbox process for '{func_name}': {e}"
