import unittest
import time
import os
import sqlite3
from tools.knowledge_tool import KnowledgeTool
from tools.database_tool import DatabaseTool
from tools.ticket_tool import TicketTool
from tools.email_tool import EmailTool
from tools.notification_tool import NotificationTool
from workflow import run_workflow

class TestITSupportSystem(unittest.TestCase):

    def setUp(self):
        # Create database dir if it doesn't exist
        db_dir = os.path.join(os.path.dirname(__file__), "database")
        os.makedirs(db_dir, exist_ok=True)
        # Ensure knowledge_base exists for tests
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
        """Tools reject wrong schema types validation."""
        kb = KnowledgeTool()
        res = kb.run()  # Missing required parameter query
        self.assertFalse(res["success"])
        self.assertIn("Schema Validation Error", res["error"])

    def test_database_incident_query(self):
        """Incident database retrieves past tickets."""
        db = DatabaseTool()
        res = db.run(query="Printer")
        self.assertTrue(res["success"])
        # Should initialize and find mock printer data
        self.assertIn("Restart printer", res["result"])

    def test_ticket_creation(self):
        """Ticket system creates and stores a ticket."""
        ticket = TicketTool()
        res = ticket.run(user="Akhil", issue="Laptop screen broken", priority="High")
        self.assertTrue(res["success"])
        self.assertIn("INC", res["result"])
        self.assertIn("Ticket Created Successfully", res["result"])

    def test_email_retry_and_timeout(self):
        """Email simulates retry backoff and handles timeout connection error safely."""
        # Timeout scenario has 3 retries
        email = EmailTool(timeout=1.0, retries=3, backoff_factor=1.1)
        start_time = time.time()
        res = email.run(to="timeout@example.com", subject="Alert", body="Action required")
        elapsed = time.time() - start_time
        
        self.assertFalse(res["success"])
        self.assertIn("Failed after 3 attempts", res["error"])
        self.assertIn("SMTP connection timed out", res["error"])
        # Should have taken at least some backoff time
        self.assertTrue(elapsed >= 0.5)

    def test_notification_alert(self):
        """Notification triggers alert logging successfully."""
        notifier = NotificationTool()
        res = notifier.run(message="Ticket INC1001 created")
        self.assertTrue(res["success"])
        self.assertIn("System Notification Logged", res["result"])

    def test_workflow_end_to_end_success(self):
        """LangGraph coordination workflow runs end-to-end for IT issue."""
        res = run_workflow("My laptop cannot connect to the company VPN.")
        self.assertIn("answer", res)
        self.assertIn("plan", res)
        self.assertIn("research", res)
        self.assertIn("decision", res)

if __name__ == '__main__':
    unittest.main()
