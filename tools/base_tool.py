"""
base_tool.py
------------
Base tool class supporting Pydantic argument schemas, retries with exponential backoff,
failure simulation testing, and structured execution outputs.
"""

import time
from typing import Any, Dict, Type, Optional
from pydantic import BaseModel, ValidationError

class BaseTool:
    name: str = ""
    description: str = ""
    args_schema: Optional[Type[BaseModel]] = None
    tool_type: str = "CORE"  # "CORE" or "SUPPORTING"

    def __init__(self, timeout: float = 5.0, retries: int = 3, backoff_factor: float = 2.0):
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.simulate_failure = False

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
                    "result": None,
                    "retries": 0
                }

        # Check deliberate tool failure testing flag
        if self.simulate_failure:
            from agent_bus import bus
            bus.publish(
                publisher="tool_system",
                event_type="tool_failure_simulated",
                payload={"tool_name": self.name, "message": "Simulated tool connection failure triggered for testing."},
                session_id="global"
            )
            # Retry loop demonstrating resilience & backoff
            attempt = 0
            current_delay = 0.5
            while attempt < self.retries:
                attempt += 1
                time.sleep(0.1) # brief pause during simulation
                bus.publish(
                    publisher="tool_system",
                    event_type="tool_retry_attempt",
                    payload={"tool_name": self.name, "attempt": attempt, "max_retries": self.retries},
                    session_id="global"
                )
            return {
                "success": False,
                "error": f"Simulated Failure: Tool '{self.name}' timed out after {self.retries} retries.",
                "result": None,
                "retries": self.retries
            }

        # Normal execution with retry & backoff
        attempt = 0
        current_delay = 0.5
        last_error = ""

        while attempt < self.retries:
            try:
                result = self._execute(**kwargs)
                return {
                    "success": True,
                    "error": None,
                    "result": result,
                    "retries": attempt
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
            "result": None,
            "retries": self.retries
        }
