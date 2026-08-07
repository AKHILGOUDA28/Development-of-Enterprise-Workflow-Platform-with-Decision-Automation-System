"""
registry.py
-----------
Central tool registry. All tools are registered here.
Tracks call counts, success rates, and last invocation time for monitoring.
"""

import time
from typing import Dict, Any
from tools.knowledge_tool import KnowledgeTool
from tools.database_tool import DatabaseTool
from tools.ticket_tool import TicketTool
from tools.email_tool import EmailTool
from tools.notification_tool import NotificationTool
from tools.hr_tool import HRTool
from tools.weather_tool import WeatherTool
from tools.calendar_tool import CalendarTool
from tools.web_search_tool import WebSearchTool


class ToolRegistry:
    """
    Central registry for all enterprise tools.

    Wraps tool execution to track usage statistics:
      - total calls
      - successful calls
      - failed calls
      - average latency (ms)
      - last used timestamp
    """

    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._stats: Dict[str, Dict] = {}

        # Register all tools
        for tool in [
            KnowledgeTool(),
            DatabaseTool(),
            TicketTool(),
            EmailTool(),
            NotificationTool(),
            HRTool(),
            WeatherTool(),
            CalendarTool(),
            WebSearchTool(),
        ]:
            self.register(tool)

    def register(self, tool) -> None:
        """Register a tool and initialise its stats counter."""
        self._tools[tool.name] = tool
        self._stats[tool.name] = {
            "total_calls":   0,
            "success_calls": 0,
            "failed_calls":  0,
            "total_latency_ms": 0.0,
            "last_used":     None,
        }

    def get_tool(self, name: str):
        """Retrieve a tool by name. Raises ValueError if not found."""
        if name not in self._tools:
            raise ValueError(
                f"Tool '{name}' not found. Available tools: {', '.join(self._tools.keys())}"
            )
        return _MonitoredTool(self._tools[name], self._stats[name])

    def get_all_tools(self):
        """Return all registered tool instances."""
        return list(self._tools.values())

    def get_tool_names(self):
        """Return all registered tool names."""
        return list(self._tools.keys())

    def get_tool_stats(self) -> list:
        """
        Returns usage statistics for all registered tools.

        Each entry contains:
          name, total_calls, success_calls, failed_calls,
          success_rate (%), avg_latency_ms, last_used
        """
        result = []
        for name, stats in self._stats.items():
            total = stats["total_calls"]
            success_rate = (
                round(stats["success_calls"] / total * 100, 1) if total > 0 else 0.0
            )
            avg_latency = (
                round(stats["total_latency_ms"] / total, 1) if total > 0 else 0.0
            )
            result.append({
                "name":           name,
                "total_calls":    total,
                "success_calls":  stats["success_calls"],
                "failed_calls":   stats["failed_calls"],
                "success_rate":   success_rate,
                "avg_latency_ms": avg_latency,
                "last_used":      stats["last_used"],
            })
        return result


class _MonitoredTool:
    """
    Transparent wrapper that intercepts tool.run() to record statistics.
    Delegates all other attribute access to the underlying tool.
    """

    def __init__(self, tool, stats: dict):
        self._tool  = tool
        self._stats = stats

    def run(self, **kwargs):
        start = time.monotonic()
        result = self._tool.run(**kwargs)
        elapsed_ms = (time.monotonic() - start) * 1000

        self._stats["total_calls"]      += 1
        self._stats["total_latency_ms"] += elapsed_ms
        self._stats["last_used"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        if result.get("success"):
            self._stats["success_calls"] += 1
        else:
            self._stats["failed_calls"] += 1

        return result

    def __getattr__(self, item):
        return getattr(self._tool, item)


# Global singleton
tool_registry = ToolRegistry()
