"""
registry.py
-----------
Central Tool Registry. Categorizes tools into Core vs Supporting,
tracks usage statistics, latency, retries, and supports failure testing mode.
"""

import time
from typing import Dict, Any, List
from langchain_core.tools import StructuredTool

from tools.knowledge_tool import KnowledgeTool
from tools.database_tool import DatabaseTool
from tools.ticket_tool import TicketTool
from tools.email_tool import EmailTool
from tools.notification_tool import NotificationTool
from tools.hr_tool import HRTool
from tools.infrastructure_tool import InfrastructureTool
from tools.calendar_tool import CalendarTool
from tools.web_search_tool import WebSearchTool


class ToolRegistry:
    """
    Central registry for enterprise tools.
    Categorizes tools:
      - Core Functional: Knowledge Base, Incident DB, Ticket System, Email, Web Search
      - Supporting: HR, Infrastructure Monitor, Calendar, Notification
    """

    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._stats: Dict[str, Dict] = {}

        # Core Tools
        t_kb = KnowledgeTool()
        t_kb.tool_type = "CORE"
        
        t_db = DatabaseTool()
        t_db.tool_type = "CORE"
        
        t_tkt = TicketTool()
        t_tkt.tool_type = "CORE"
        
        t_email = EmailTool()
        t_email.tool_type = "CORE"
        
        t_web = WebSearchTool()
        t_web.tool_type = "CORE"

        # Supporting Tools
        t_hr = HRTool()
        t_hr.tool_type = "SUPPORTING"
        
        t_infra = InfrastructureTool()
        t_infra.tool_type = "SUPPORTING"
        
        t_cal = CalendarTool()
        t_cal.tool_type = "SUPPORTING"
        
        t_notif = NotificationTool()
        t_notif.tool_type = "SUPPORTING"

        for tool in [t_kb, t_db, t_tkt, t_email, t_web, t_hr, t_infra, t_cal, t_notif]:
            self.register(tool)

    def register(self, tool) -> None:
        self._tools[tool.name] = tool
        self._stats[tool.name] = {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "total_latency_ms": 0.0,
            "last_used": None,
            "tool_type": getattr(tool, "tool_type", "CORE"),
            "simulate_failure": False
        }

    def get_tool(self, name: str):
        if name not in self._tools:
            raise ValueError(
                f"Tool '{name}' not found. Available tools: {', '.join(self._tools.keys())}"
            )
        return _MonitoredTool(self._tools[name], self._stats[name])

    def get_all_tools(self):
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def set_tool_failure(self, name: str, fail: bool) -> bool:
        if name in self._tools:
            self._tools[name].simulate_failure = fail
            self._stats[name]["simulate_failure"] = fail
            return True
        return False

    def get_langchain_tools(self) -> List[StructuredTool]:
        """Converts registered tools into LangChain StructuredTool instances for LLM bind_tools."""
        lc_tools = []
        for name, tool_obj in self._tools.items():
            # Monitored runner wrapper
            def make_runner(t_name=name):
                def runner(**kwargs):
                    monitored = self.get_tool(t_name)
                    res = monitored.run(**kwargs)
                    if res["success"]:
                        return str(res["result"])
                    return f"Error: {res['error']}"
                return runner

            lc_tool = StructuredTool.from_function(
                func=make_runner(name),
                name=tool_obj.name,
                description=tool_obj.description,
                args_schema=tool_obj.args_schema
            )
            lc_tools.append(lc_tool)
        return lc_tools

    def get_tool_stats(self) -> list:
        result = []
        for name, stats in self._stats.items():
            total = stats["total_calls"]
            success_rate = (
                round(stats["success_calls"] / total * 100, 1) if total > 0 else 100.0
            )
            avg_latency = (
                round(stats["total_latency_ms"] / total, 1) if total > 0 else 0.0
            )
            result.append({
                "name": name,
                "tool_type": stats.get("tool_type", "CORE"),
                "total_calls": total,
                "success_calls": stats["success_calls"],
                "failed_calls": stats["failed_calls"],
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency,
                "last_used": stats["last_used"],
                "simulate_failure": stats.get("simulate_failure", False)
            })
        return result


class _MonitoredTool:
    def __init__(self, tool, stats: dict):
        self._tool = tool
        self._stats = stats

    def run(self, **kwargs):
        start = time.monotonic()
        result = self._tool.run(**kwargs)
        elapsed_ms = (time.monotonic() - start) * 1000

        self._stats["total_calls"] += 1
        self._stats["total_latency_ms"] += elapsed_ms
        self._stats["last_used"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        if result.get("success"):
            self._stats["success_calls"] += 1
        else:
            self._stats["failed_calls"] += 1

        # Persist tool execution logs in DB
        try:
            from database.connection import db_manager
            import json
            db_manager.execute("""
                INSERT INTO tool_executions (tool_name, success, error, latency_ms, args, result, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self._tool.name,
                1 if result.get("success") else 0,
                result.get("error"),
                elapsed_ms,
                json.dumps(kwargs),
                json.dumps(result.get("result")) if result.get("success") else None,
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            ))
        except Exception:
            pass

        return result

    def __getattr__(self, item):
        return getattr(self._tool, item)


# Shared singleton instance
tool_registry = ToolRegistry()
