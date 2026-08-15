"""
weather_tool.py
--------------
Backward-compatibility wrapper. Exposes WeatherTool / weather_service alias pointing to InfrastructureTool.
"""

from tools.infrastructure_tool import InfrastructureTool as WeatherTool, infrastructure_tool as weather_tool

__all__ = ["WeatherTool", "weather_tool"]
