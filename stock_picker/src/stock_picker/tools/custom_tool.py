import os
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

class PushNotificationInput(BaseModel):
    """Message to be sent to the user."""
    message: str = Field(..., description="Message to be sent to the user.")

class PushNotificationTool(BaseTool):
    name: str = "Send a push notification "
    description: str = (
        "Send a push notification to the user with the given message."
    )
    args_schema: Type[BaseModel] = PushNotificationInput

    def _run(self, message: str) -> str:
        pushover_user = os.getenv("PUSHOVER_USER")
        pushover_token = os.getenv("PUSHOVER_TOKEN")

        pushover_url = "https://api.pushover.net/1/messages.json"
        payload = {
            "user": pushover_user,
            "token": pushover_token,
            "message": message
        }
        print(payload)
        requests.post(pushover_url, data=payload)

        return '{"notification ": "ok"}'
