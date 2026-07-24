from pydantic import BaseModel
from tools.base_tool import BaseTool

class NotificationToolSchema(BaseModel):
    message: str

class NotificationTool(BaseTool):
    name = "notification"
    description = "Sends an in-app system notification."
    args_schema = NotificationToolSchema

    def _execute(self, message: str) -> str:
        return f"System Notification Logged: {message}"
