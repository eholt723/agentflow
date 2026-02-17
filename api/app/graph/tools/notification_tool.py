# api/app/graph/tools/notification_tool.py
from api.app.graph.tools.notification_tool import send_notification

def send_notification(message: str) -> bool:
    print(f"[Notification] {message}")
    return True
