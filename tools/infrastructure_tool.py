"""
infrastructure_tool.py
----------------------
Enterprise Infrastructure & Environmental Monitoring Tool.

Used for data center environmental monitoring, facility health, server room thermal alerts,
UPS power status, and severe environmental/weather condition alerts.
"""

import random
from datetime import datetime
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool


# ---------------------------------------------------------------------------
# Pydantic Schema
# ---------------------------------------------------------------------------
class InfrastructureQuerySchema(BaseModel):
    location: str = Field(..., description="Data center name, server room, or facility location to query")
    query_type: str = Field(
        default="datacenter_env",
        description="Type of query: 'datacenter_env', 'current_weather', 'forecast', 'alerts'"
    )


# ---------------------------------------------------------------------------
# Infrastructure & Environmental Data Store
# ---------------------------------------------------------------------------
LOCATION_DATA = {
    "headquarters": {
        "facility": "Headquarters Main Server Room",
        "city": "San Francisco, CA",
        "temp_c": 18,
        "humidity": 62,
        "condition": "Partly Cloudy",
        "wind_kph": 14,
        "datacenter_temp": 21.4,
        "datacenter_humidity": 45,
        "ups_status": "Normal (100% capacity)",
        "cooling_status": "Optimal (CRAC Unit 1 & 2 Active)"
    },
    "data center a": {
        "facility": "Enterprise Data Center A (DC-DAL-01)",
        "city": "Dallas, TX",
        "temp_c": 28,
        "humidity": 70,
        "condition": "Clear",
        "wind_kph": 8,
        "datacenter_temp": 22.1,
        "datacenter_humidity": 42,
        "ups_status": "Normal (Battery Health 98%)",
        "cooling_status": "Optimal (Chill Water Loop Normal)"
    },
    "data center b": {
        "facility": "Enterprise Data Center B (DC-CHI-02)",
        "city": "Chicago, IL",
        "temp_c": 12,
        "humidity": 55,
        "condition": "Overcast",
        "wind_kph": 22,
        "datacenter_temp": 20.8,
        "datacenter_humidity": 48,
        "ups_status": "Normal",
        "cooling_status": "High Thermal Load (Secondary Fan Engaged)"
    },
    "remote office": {
        "facility": "Austin Remote Branch IDF Closet",
        "city": "Austin, TX",
        "temp_c": 32,
        "humidity": 80,
        "condition": "Severe Weather Warning",
        "wind_kph": 45,
        "datacenter_temp": 26.5,
        "datacenter_humidity": 65,
        "ups_status": "Warning (Utility Grid Voltage Fluctuation)",
        "cooling_status": "Elevated Temp Warning"
    },
}

ENVIRONMENTAL_ALERTS = {
    "remote office": [
        "CRITICAL: Grid Voltage Spike detected — UPS Battery Backup Engaged.",
        "WARNING: IDF Closet Ambient Temp reached 26.5°C — Aux Fan triggered.",
    ],
    "data center b": [
        "ADVISORY: Below-freezing external temperatures — HVAC Antifreeze Loop active.",
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
class InfrastructureTool(BaseTool):
    name = "infrastructure_monitor"
    description = (
        "Retrieves data center environmental telemetry, server room temperatures, "
        "UPS power status, cooling system health, and severe environmental alerts for enterprise locations."
    )
    args_schema = InfrastructureQuerySchema

    def _execute(self, location: str, query_type: str = "datacenter_env") -> str:
        loc_key = location.lower().strip()
        matched_key = None
        for key in LOCATION_DATA:
            if loc_key in key or key in loc_key:
                matched_key = key
                break

        if query_type == "alerts":
            if matched_key and matched_key in ENVIRONMENTAL_ALERTS:
                alerts = ENVIRONMENTAL_ALERTS[matched_key]
                return f"Infrastructure Alerts for {location}:\n" + "\n".join(f"  • {a}" for a in alerts)
            return f"No active infrastructure/environmental alerts for '{location}'."

        if not matched_key:
            return (
                f"Infrastructure Status for {location}:\n"
                f"  Data Center Temp: 21.8°C (Normal)\n"
                f"  Humidity: 45%\n"
                f"  UPS Status: Operational\n"
                f"  Cooling System: Normal\n"
                f"  Ambient Weather: 22°C Clear"
            )

        data = LOCATION_DATA[matched_key]

        if query_type == "datacenter_env":
            return (
                f"Facility Telemetry — {data['facility']} ({data['city']}):\n"
                f"  Server Room Temp: {data['datacenter_temp']}°C\n"
                f"  Relative Humidity: {data['datacenter_humidity']}%\n"
                f"  UPS Power Status: {data['ups_status']}\n"
                f"  HVAC / Cooling Loop: {data['cooling_status']}\n"
                f"  External Weather: {data['temp_c']}°C, {data['condition']}"
            )

        elif query_type == "current_weather":
            return (
                f"Facility External Weather — {data['city']}:\n"
                f"  Temperature: {data['temp_c']}°C\n"
                f"  Humidity: {data['humidity']}%\n"
                f"  Condition: {data['condition']}\n"
                f"  Wind Speed: {data['wind_kph']} km/h"
            )

        elif query_type == "forecast":
            lines = [f"5-Day Facility Environmental Forecast — {data['city']}:"]
            for day, cond, temp, wind in FORECAST_TEMPLATE:
                lines.append(f"  {day}: {cond}, {temp}°C, Wind {wind} km/h")
            return "\n".join(lines)

        return f"Unknown query type '{query_type}'. Use: datacenter_env, current_weather, forecast, or alerts."


# Singleton instance
infrastructure_tool = InfrastructureTool()
