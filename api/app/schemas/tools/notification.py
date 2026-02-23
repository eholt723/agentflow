# schemas/tools/notification.py
from pydantic import BaseModel


class NotificationInput(BaseModel):
    message: str


class NotificationResult(BaseModel):
    sent: bool
