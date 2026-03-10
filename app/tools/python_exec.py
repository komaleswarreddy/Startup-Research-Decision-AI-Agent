import ast
import multiprocessing as mp
from dataclasses import dataclass
from typing import Any

from app.config.settings import get_settings

def cagr(start_value: float, end_value: float, years: float) -> float:
    if start_value <= 0 or years <= 0:
        return 0.0
    return ((end_value / start_value) ** (1 / years) - 1) * 100


def project_revenue(
    base_revenue: float, growth_rate: float, years: int = 3
) -> list[float]:
    values: list[float] = []
    current = base_revenue
    for _ in range(years):
        current = current * (1 + growth_rate / 100)
        values.append(round(current, 2))
    return values


@dataclass
class PythonExecutionResult:
    success: bool
    output: dict[str, Any]
    error: str = ""


def _run_user_code(code: str, context: dict[str, Any], output_queue: mp.Queue) -> None:
    try:
        safe_globals: dict[str, Any] = {
            "__builtins__": {
                "len": len,
                "min": min,
                "max": max,
                "sum": sum,
                "round": round,
                "range": range,
                    "int": int,
                    "float": float,
                    "str": str,
            },
            "cagr": cagr,
            "project_revenue": project_revenue,
        }
        safe_locals: dict[str, Any] = dict(context)
        tree = ast.parse(code)
        exec(compile(tree, "<safe-python>", "exec"), safe_globals, safe_locals)
        output_queue.put(PythonExecutionResult(success=True, output=safe_locals))
    except Exception as exc:
        output_queue.put(PythonExecutionResult(success=False, output={}, error=str(exc)))


class SafePythonExecutor:
    FORBIDDEN_NODES = (
        ast.Import,
        ast.ImportFrom,
        ast.With,
        ast.AsyncWith,
        ast.Try,
        ast.ClassDef,
        ast.Lambda,
    )
    FORBIDDEN_NAMES = {"eval", "exec", "open", "__import__", "compile", "input", "globals", "locals"}

    def __init__(self) -> None:
        self.settings = get_settings()

    def execute(self, code: str, context: dict[str, Any] | None = None) -> PythonExecutionResult:
        context = context or {}
        if len(code) > self.settings.python_exec_max_code_chars:
            return PythonExecutionResult(
                success=False,
                output={},
                error="Code exceeds maximum allowed size.",
            )

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, self.FORBIDDEN_NODES):
                    return PythonExecutionResult(
                        success=False,
                        output={},
                        error="Forbidden Python construct detected.",
                    )
                if isinstance(node, ast.Name) and node.id in self.FORBIDDEN_NAMES:
                    return PythonExecutionResult(
                        success=False,
                        output={},
                        error=f"Forbidden name detected: {node.id}",
                    )

            queue: mp.Queue = mp.Queue()
            process = mp.Process(target=_run_user_code, args=(code, context, queue))
            process.start()
            process.join(timeout=self.settings.python_exec_timeout_seconds)
            if process.is_alive():
                process.terminate()
                process.join()
                return PythonExecutionResult(
                    success=False,
                    output={},
                    error="Python execution timed out.",
                )
            if not queue.empty():
                return queue.get()
            return PythonExecutionResult(success=False, output={}, error="Python execution failed.")
        except Exception as exc:
            return PythonExecutionResult(success=False, output={}, error=str(exc))
