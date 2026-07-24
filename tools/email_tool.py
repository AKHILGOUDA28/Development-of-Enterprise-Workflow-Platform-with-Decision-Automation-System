import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel
from tools.base_tool import BaseTool
import config

class EmailToolSchema(BaseModel):
    to: str
    subject: str
    body: str

class EmailTool(BaseTool):
    name = "email"
    description = "Sends an email notification."
    args_schema = EmailToolSchema

    def _execute(self, to: str, subject: str, body: str) -> str:
        # For testing fallback
        if "timeout" in to.lower():
            raise TimeoutError("SMTP connection timed out.")
        
        # If no credentials, simulate success
        if not config.EMAIL_USER or not config.EMAIL_PASSWORD:
            return f"Mock Email sent successfully to {to} with subject '{subject}'."

        try:
            msg = MIMEMultipart()
            msg['From'] = config.EMAIL_USER
            msg['To'] = to
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.EMAIL_USER, config.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return f"Email successfully sent to {to}."
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")
