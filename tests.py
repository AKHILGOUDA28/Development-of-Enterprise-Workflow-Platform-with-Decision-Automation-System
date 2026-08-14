import uuid_utils_compat  # noqa: F401 — must come before any langchain import
import unittest
import time
import os
import sqlite3

# Original tools
from tools.knowledge_tool import KnowledgeTool
from tools.database_tool import DatabaseTool
from tools.ticket_tool import TicketTool
from tools.email_tool import EmailTool
from tools.notification_tool import NotificationTool

# New enterprise tools (Milestone 2)
from tools.hr_tool import HRTool
from tools.weather_tool import WeatherTool
from tools.calendar_tool import CalendarTool
from tools.web_search_tool import WebSearchTool

# Registry with monitoring
from tools.registry import ToolRegistry

# Agents & workflow (Milestone 3)
from workflow import run_workflow
from agent_bus import AgentEventBus
from memory import LongTermMemory


class TestOriginalTools(unittest.TestCase):
    """Milestone 1: original tool suite."""

    def setUp(self):
        db_dir = os.path.join(os.path.dirname(__file__), "database")
        os.makedirs(db_dir, exist_ok=True)
        kb_path = os.path.join(db_dir, "knowledge_base.json")
        if not os.path.exists(kb_path):
            with open(kb_path, "w") as f:
                f.write('[{"issue": "VPN not connecting", "solution": ["Restart VPN service", "Clear DNS cache"]}]')

    def test_knowledge_base_success(self):
        """Knowledge Base tool retrieves known solutions."""
        kb = KnowledgeTool()
        res = kb.run(query="VPN")
        self.assertTrue(res["success"])
        self.assertIn("Restart VPN", res["result"])
        self.assertIsNone(res["error"])

    def test_schema_validation(self):
        """Tools reject calls missing required parameters."""
        kb = KnowledgeTool()
        res = kb.run()  # Missing required parameter 'query'
        self.assertFalse(res["success"])
        self.assertIn("Schema Validation Error", res["error"])

    def test_database_incident_query(self):
        """Incident database retrieves past tickets."""
        db = DatabaseTool()
        res = db.run(query="Printer")
        self.assertTrue(res["success"])
        self.assertIn("Printer spooler offline", res["result"])

    def test_ticket_creation(self):
        """Ticket system creates and stores a ticket."""
        ticket = TicketTool()
        res = ticket.run(user="Akhil", issue="Laptop screen broken", priority="High")
        self.assertTrue(res["success"])
        self.assertIn("INC", res["result"])
        self.assertIn("Ticket Created Successfully", res["result"])

    def test_email_retry_and_timeout(self):
        """Email simulates retry backoff and handles timeout connection error safely."""
        email = EmailTool(timeout=1.0, retries=3, backoff_factor=1.1)
        start_time = time.time()
        res = email.run(to="timeout@example.com", subject="Alert", body="Action required")
        elapsed = time.time() - start_time
        self.assertFalse(res["success"])
        self.assertIn("Failed after 3 attempts", res["error"])
        self.assertIn("SMTP connection timed out", res["error"])
        self.assertTrue(elapsed >= 0.5)

    def test_notification_alert(self):
        """Notification triggers alert logging successfully."""
        notifier = NotificationTool()
        res = notifier.run(message="Ticket INC1001 created")
        self.assertTrue(res["success"])
        self.assertIn("System Notification Logged", res["result"])


class TestNewEnterpriseTools(unittest.TestCase):
    """Milestone 2: new enterprise simulation tools."""

    def test_hr_employee_lookup(self):
        """HR tool retrieves employee record by name."""
        hr = HRTool()
        res = hr.run(query="Alice", lookup_type="employee")
        self.assertTrue(res["success"])
        self.assertIn("Alice Johnson", res["result"])
        self.assertIn("IT Infrastructure", res["result"])

    def test_hr_department_lookup(self):
        """HR tool retrieves department info."""
        hr = HRTool()
        res = hr.run(query="Network Operations", lookup_type="department")
        self.assertTrue(res["success"])
        self.assertIn("Frank Lee", res["result"])

    def test_hr_oncall_lookup(self):
        """HR tool retrieves on-call schedule."""
        hr = HRTool()
        res = hr.run(query="IT Infrastructure", lookup_type="oncall")
        self.assertTrue(res["success"])
        self.assertIn("Alice Johnson", res["result"])

    def test_weather_current(self):
        """Weather tool returns current conditions."""
        weather = WeatherTool()
        res = weather.run(location="headquarters", query_type="current")
        self.assertTrue(res["success"])
        self.assertIn("Temperature", res["result"])
        self.assertIn("San Francisco", res["result"])

    def test_weather_datacenter_env(self):
        """Weather tool returns data center environmental data."""
        weather = WeatherTool()
        res = weather.run(location="data center a", query_type="datacenter_env")
        self.assertTrue(res["success"])
        self.assertIn("Room Temperature", res["result"])

    def test_weather_alerts(self):
        """Weather tool returns active weather alerts."""
        weather = WeatherTool()
        res = weather.run(location="remote office", query_type="alerts")
        self.assertTrue(res["success"])
        self.assertIn("Thunderstorm", res["result"])

    def test_calendar_maintenance_windows(self):
        """Calendar tool returns upcoming maintenance windows."""
        cal = CalendarTool()
        res = cal.run(query="Network Operations", action="maintenance_windows")
        self.assertTrue(res["success"])
        self.assertIn("MW-", res["result"])

    def test_calendar_blackout_dates(self):
        """Calendar tool returns blackout dates."""
        cal = CalendarTool()
        res = cal.run(query="all", action="blackout_dates")
        self.assertTrue(res["success"])
        self.assertIn("Blackout Dates", res["result"])

    def test_calendar_schedule_work(self):
        """Calendar tool schedules a work order and returns reference ID."""
        cal = CalendarTool()
        res = cal.run(query="VPN patch deployment", action="schedule_work")
        self.assertTrue(res["success"])
        self.assertIn("WO-", res["result"])

    def test_web_search_vpn(self):
        """Web search tool returns relevant IT articles."""
        ws = WebSearchTool()
        res = ws.run(query="VPN connectivity windows update", max_results=2)
        self.assertTrue(res["success"])
        self.assertIn("VPN", res["result"])

    def test_web_search_no_results(self):
        """Web search tool handles no-match gracefully."""
        ws = WebSearchTool()
        res = ws.run(query="quantum tunnelling refrigerator banana", max_results=3)
        self.assertTrue(res["success"])
        self.assertIn("No relevant articles found", res["result"])

    def test_hr_schema_validation(self):
        """HR tool rejects missing required 'query' parameter."""
        hr = HRTool()
        res = hr.run()  # Missing required 'query'
        self.assertFalse(res["success"])
        self.assertIn("Schema Validation Error", res["error"])


class TestToolRegistryMonitoring(unittest.TestCase):
    """Milestone 2: tool registry with usage statistics."""

    def test_registry_has_nine_tools(self):
        """Registry registers all 9 tools."""
        reg = ToolRegistry()
        self.assertEqual(len(reg.get_all_tools()), 9)

    def test_registry_tool_stats_structure(self):
        """Tool stats returns expected fields."""
        reg = ToolRegistry()
        stats = reg.get_tool_stats()
        self.assertIsInstance(stats, list)
        self.assertEqual(len(stats), 9)
        for entry in stats:
            self.assertIn("name", entry)
            self.assertIn("total_calls", entry)
            self.assertIn("success_rate", entry)
            self.assertIn("avg_latency_ms", entry)

    def test_registry_call_tracking(self):
        """Tool calls are recorded in stats."""
        reg = ToolRegistry()
        tool = reg.get_tool("web_search")
        initial_stats = next(s for s in reg.get_tool_stats() if s["name"] == "web_search")
        initial_calls = initial_stats["total_calls"]
        tool.run(query="VPN", max_results=1)
        updated_stats = next(s for s in reg.get_tool_stats() if s["name"] == "web_search")
        self.assertEqual(updated_stats["total_calls"], initial_calls + 1)

    def test_registry_unknown_tool_raises(self):
        """Getting unknown tool raises ValueError."""
        reg = ToolRegistry()
        with self.assertRaises(ValueError):
            reg.get_tool("nonexistent_tool_xyz")


class TestAgentEventBus(unittest.TestCase):
    """Milestone 3: agent communication event bus."""

    def test_publish_and_retrieve(self):
        """Published events are retrievable."""
        bus = AgentEventBus()
        bus.publish("planner_agent", "plan_ready", {"steps": 4}, session_id="test-1")
        events = bus.get_events(session_id="test-1")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["publisher"], "planner_agent")
        self.assertEqual(events[0]["event_type"], "plan_ready")

    def test_event_type_filter(self):
        """Event type filtering returns only matching events."""
        bus = AgentEventBus()
        bus.publish("planner_agent",    "plan_ready",         {"steps": 4},    session_id="test-2")
        bus.publish("researcher_agent", "research_complete",  {"mode": "llm"}, session_id="test-2")
        bus.publish("decision_agent",   "decision_complete",  {"action": "escalate"}, session_id="test-2")

        plan_events = bus.get_events(session_id="test-2", event_type="plan_ready")
        self.assertEqual(len(plan_events), 1)
        self.assertEqual(plan_events[0]["event_type"], "plan_ready")

    def test_subscriber_callback(self):
        """Subscriber callbacks fire on matching events."""
        bus = AgentEventBus()
        received = []
        bus.subscribe("test_event", lambda e: received.append(e))
        bus.publish("test_publisher", "test_event", {"value": 42})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].payload["value"], 42)

    def test_stats_tracking(self):
        """Bus stats track total events and event type breakdown."""
        bus = AgentEventBus()
        bus.publish("a1", "type_x", {})
        bus.publish("a2", "type_x", {})
        bus.publish("a3", "type_y", {})
        stats = bus.get_stats()
        self.assertGreaterEqual(stats["total_events"], 3)
        self.assertGreaterEqual(stats["event_type_breakdown"].get("type_x", 0), 2)

    def test_session_isolation(self):
        """Events from different sessions are correctly isolated."""
        bus = AgentEventBus()
        bus.publish("agent", "event_a", {"x": 1}, session_id="session-A")
        bus.publish("agent", "event_b", {"x": 2}, session_id="session-B")
        events_a = bus.get_events(session_id="session-A")
        events_b = bus.get_events(session_id="session-B")
        self.assertEqual(len(events_a), 1)
        self.assertEqual(len(events_b), 1)
        self.assertEqual(events_a[0]["event_type"], "event_a")
        self.assertEqual(events_b[0]["event_type"], "event_b")


class TestPersistentLongTermMemory(unittest.TestCase):
    """Milestone 3: SQLite-backed long-term memory."""

    def setUp(self):
        """Use a fresh isolated memory DB path for each test run."""
        import tempfile
        self._tmpdir = tempfile.mkdtemp()
        self._mem = LongTermMemory.__new__(LongTermMemory)
        self._mem._lock = __import__("threading").Lock()
        self._mem.DB_PATH = os.path.join(self._tmpdir, "test_memory.db")
        self._mem._init_db()

    def test_save_and_recall(self):
        """Saved facts can be recalled by key."""
        self._mem.save("server_patch_policy", "Patch every Tuesday at 02:00")
        val = self._mem.recall("server_patch_policy")
        self.assertEqual(val, "Patch every Tuesday at 02:00")

    def test_recall_missing_key_returns_none(self):
        """Recalling a non-existent key returns None."""
        val = self._mem.recall("does_not_exist_key_xyz")
        self.assertIsNone(val)

    def test_overwrite_existing_key(self):
        """Saving to an existing key updates the value."""
        self._mem.save("vpn_provider", "Cisco AnyConnect")
        self._mem.save("vpn_provider", "Palo Alto GlobalProtect")
        val = self._mem.recall("vpn_provider")
        self.assertEqual(val, "Palo Alto GlobalProtect")

    def test_delete_key(self):
        """Deleting a key removes it from memory."""
        self._mem.save("temp_key", "temp_value")
        deleted = self._mem.delete("temp_key")
        self.assertTrue(deleted)
        self.assertIsNone(self._mem.recall("temp_key"))

    def test_delete_nonexistent_key_returns_false(self):
        """Deleting a missing key returns False without error."""
        result = self._mem.delete("never_existed_key")
        self.assertFalse(result)

    def test_show_all(self):
        """show_all returns all stored entries."""
        self._mem.save("key1", "val1")
        self._mem.save("key2", "val2")
        all_entries = self._mem.show_all()
        keys = [e["key"] for e in all_entries]
        self.assertIn("key1", keys)
        self.assertIn("key2", keys)

    def test_search(self):
        """Text search finds entries by key or value substring."""
        self._mem.save("network_policy", "Firewalls must use IPS in blocking mode")
        self._mem.save("backup_policy",  "Daily backups at midnight")
        results = self._mem.search("firewall")
        self.assertTrue(any("network_policy" in r["key"] for r in results))

    def test_persistence_across_instances(self):
        """Memory persists across separate LongTermMemory instantiations."""
        self._mem.save("persistent_key", "persisted_value")
        # Create a second instance pointing to the same DB
        mem2 = LongTermMemory.__new__(LongTermMemory)
        mem2._lock = __import__("threading").Lock()
        mem2.DB_PATH = self._mem.DB_PATH
        mem2._init_db()
        val = mem2.recall("persistent_key")
        self.assertEqual(val, "persisted_value")


class TestFiveAgentWorkflow(unittest.TestCase):
    """Milestone 3: 5-agent coordination workflow."""

    def test_workflow_returns_all_fields(self):
        """Workflow returns all 5 agent outputs including analysis."""
        res = run_workflow("My laptop cannot connect to the company VPN.")
        self.assertIn("answer",   res)
        self.assertIn("plan",     res)
        self.assertIn("research", res)
        self.assertIn("analysis", res)   # NEW — Analysis Agent output
        self.assertIn("decision", res)
        self.assertIn("session_id", res) # NEW — Session identifier

    def test_workflow_analysis_not_empty(self):
        """Analysis Agent produces non-empty output."""
        res = run_workflow("Outlook keeps crashing when opening attachments.")
        self.assertTrue(len(res.get("analysis", "")) > 0)

    def test_workflow_session_id_unique(self):
        """Each workflow run gets a unique session_id."""
        res1 = run_workflow("VPN issue")
        res2 = run_workflow("Printer issue")
        self.assertNotEqual(res1.get("session_id"), res2.get("session_id"))

    def test_workflow_publishes_bus_events(self):
        """Workflow publishes events to the agent bus."""
        from agent_bus import bus
        initial_stats = bus.get_stats()
        initial_count = initial_stats.get("total_events", 0)
        run_workflow("Cannot access shared network drive.")
        updated_stats = bus.get_stats()
        self.assertGreater(updated_stats.get("total_events", 0), initial_count)


if __name__ == '__main__':
    unittest.main()
