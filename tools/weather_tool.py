"""
weather_tool.py
---------------
Simulated Weather / Environmental Monitoring Tool.

Used for facilities management, field technician dispatch decisions,
and data center environmental alerts.
"""

import random
from datetime import datetime
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool


# ---------------------------------------------------------------------------
# Pydantic Schema
# ---------------------------------------------------------------------------
class WeatherQuerySchema(BaseModel):
    location: str = Field(..., description="Office location, data center name, or city to query")
    query_type: str = Field(
        default="current",
        description="Type of query: 'current', 'forecast', 'datacenter_env', 'alerts'"
    )


# ---------------------------------------------------------------------------
# Simulated Environmental Data
# ---------------------------------------------------------------------------
LOCATION_DATA = {
    "headquarters": {
        "city": "San Francisco, CA",
        "temp_c": 18,
        "humidity": 62,
        "condition": "Partly Cloudy",
        "wind_kph": 14,
        "datacenter_temp": 21.4,
        "datacenter_humidity": 45,
        "ups_status": "Normal",
        "cooling_status": "Optimal"
    },
    "data center a": {
        "city": "Dallas, TX",
        "temp_c": 28,
        "humidity": 70,
        "condition": "Clear",
        "wind_kph": 8,
        "datacenter_temp": 22.1,
        "datacenter_humidity": 42,
        "ups_status": "Normal",
        "cooling_status": "Optimal"
    },
    "data center b": {
        "city": "Chicago, IL",
        "temp_c": 12,
        "humidity": 55,
        "condition": "Overcast",
        "wind_kph": 22,
        "datacenter_temp": 20.8,
        "datacenter_humidity": 48,
        "ups_status": "Normal",
        "cooling_status": "High Load"
    },
    "remote office": {
        "city": "Austin, TX",
        "temp_c": 32,
        "humidity": 80,
        "condition": "Thunderstorm Warning",
        "wind_kph": 45,
        "datacenter_temp": None,
        "datacenter_humidity": None,
        "ups_status": None,
        "cooling_status": None
    },
}

WEATHER_ALERTS = {
    "remote office": [
        "SEVERE: Thunderstorm Warning — High winds and lightning expected 14:00–20:00 local time.",
        "UPS recommended: Power fluctuations reported in Austin area grid.",
    ],
    "data center b": [
        "ADVISORY: Below-freezing temperatures overnight — check HVAC antifreeze systems.",
    ],
}

FORECAST_TEMPLATE = [
    ("Today", "Partly Cloudy", 18, 14),
    ("Tomorrow", "Sunny", 21, 10),
    ("Day 3", "Rain", 15, 18),
    ("Day 4", "Clear", 20, 9),
    ("Day 5", "Cloudy", 17, 13),
]


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------
class WeatherTool(BaseTool):
    name = "weather_service"
    description = (
        "Retrieves current weather conditions, environmental monitoring data for data centers, "
        "weather forecasts, and severe weather alerts for enterprise locations."
    )
    args_schema = WeatherQuerySchema

    def _execute(self, location: str, query_type: str = "current") -> str:
        loc_key = location.lower().strip()
        # Find best match
        matched_key = None
        for key in LOCATION_DATA:
            if loc_key in key or key in loc_key:
                matched_key = key
                break

        if query_type == "alerts":
            if matched_key and matched_key in WEATHER_ALERTS:
                alerts = WEATHER_ALERTS[matched_key]
                return f"Weather Alerts for {location}:\n" + "\n".join(f"  • {a}" for a in alerts)
            return f"No active weather alerts for '{location}'."

        if not matched_key:
            # Generic fallback
            return (
                f"Weather for {location}:\n"
                f"  Temperature: {random.randint(15, 30)}°C\n"
                f"  Humidity: {random.randint(40, 75)}%\n"
                f"  Condition: Clear\n"
                f"  Wind: {random.randint(5, 20)} km/h"
            )

        data = LOCATION_DATA[matched_key]

        if query_type == "current":
            return (
                f"Current Weather — {data['city']}:\n"
                f"  Temperature: {data['temp_c']}°C\n"
                f"  Humidity: {data['humidity']}%\n"
                f"  Condition: {data['condition']}\n"
                f"  Wind Speed: {data['wind_kph']} km/h"
            )

        elif query_type == "forecast":
            lines = [f"5-Day Forecast — {data['city']}:"]
            for day, cond, temp, wind in FORECAST_TEMPLATE:
                lines.append(f"  {day}: {cond}, {temp}°C, Wind {wind} km/h")
            return "\n".join(lines)

        elif query_type == "datacenter_env":
            if data["datacenter_temp"] is None:
                return f"No data center environmental data available for '{location}'."
            return (
                f"Data Center Environment — {data['city']}:\n"
                f"  Room Temperature: {data['datacenter_temp']}°C\n"
                f"  Relative Humidity: {data['datacenter_humidity']}%\n"
                f"  UPS Status: {data['ups_status']}\n"
                f"  Cooling System: {data['cooling_status']}"
            )

        return f"Unknown query type '{query_type}'. Use: current, forecast, datacenter_env, alerts."


# Singleton instance
weather_tool = WeatherTool()
