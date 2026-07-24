import time
import os

class Tracing:
    def __init__(self):
        self.logs = []

    def start_trace(self, query: str):
        self.logs = []
        self.log_event("Workflow Init", f"User Query: {query}")

    def log_event(self, step: str, details: str):
        event = {
            "step": step,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.logs.append(event)
        # Also print out to console
        print(f"[{event['timestamp']}] [{step}] {details}")

    def get_logs(self):
        return self.logs

# Singleton instance
tracer = Tracing()
