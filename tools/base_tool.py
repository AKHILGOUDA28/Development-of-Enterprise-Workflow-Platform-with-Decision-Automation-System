import time
import inspect
from typing import Any, Dict, Type, Optional, Callable
from pydantic import BaseModel, ValidationError

class BaseTool:
    name: str = ""
    description: str = ""
    args_schema: Optional[Type[BaseModel]] = None

    def __init__(self, timeout: float = 5.0, retries: int = 3, backoff_factor: float = 2.0):
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor

    def _execute(self, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement _execute")

    def run(self, **kwargs) -> Dict[str, Any]:
        # Input Validation
        if self.args_schema:
            try:
                validated = self.args_schema(**kwargs)
                kwargs = validated.model_dump()
            except ValidationError as ve:
                return {
                    "success": False,
                    "error": f"Schema Validation Error: {str(ve)}",
                    "result": None
                }

        # Execution with retry & backoff & timeout mock/thread handling
        attempt = 0
        current_delay = 1.0
        last_error = ""

        while attempt < self.retries:
            try:
                # Execution
                result = self._execute(**kwargs)
                return {
                    "success": True,
                    "error": None,
                    "result": result
                }
            except Exception as e:
                attempt += 1
                last_error = str(e)
                if attempt < self.retries:
                    time.sleep(current_delay)
                    current_delay *= self.backoff_factor

        return {
            "success": False,
            "error": f"Failed after {self.retries} attempts. Last error: {last_error}",
            "result": None
        }
