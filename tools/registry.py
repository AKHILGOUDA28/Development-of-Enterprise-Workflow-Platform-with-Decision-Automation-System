from tools.knowledge_tool import KnowledgeTool
from tools.database_tool import DatabaseTool
from tools.ticket_tool import TicketTool
from tools.email_tool import EmailTool
from tools.notification_tool import NotificationTool

class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self.register(KnowledgeTool())
        self.register(DatabaseTool())
        self.register(TicketTool())
        self.register(EmailTool())
        self.register(NotificationTool())

    def register(self, tool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str):
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found.")
        return self._tools[name]

    def get_all_tools(self):
        return list(self._tools.values())

tool_registry = ToolRegistry()
