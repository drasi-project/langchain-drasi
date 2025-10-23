"""Drasi sensor notification handler for Terminator agents."""

import time
from queue import Queue
from typing import Any

from langchain_drasi.callbacks import BaseDrasiNotificationHandler


class SensorHandler(BaseDrasiNotificationHandler):
    """Handles Drasi query notifications and maintains a queue for the agent."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.notification_queue = Queue()

    def on_result_added(self, query_name: str, added_data: dict[str, Any]) -> None:
        notification = {
            "type": "added",
            "query": query_name,
            "data": added_data,
            "timestamp": time.time()
        }
        self.notification_queue.put(notification)
        print(f"[{self.agent_id}] 🔔 Notification (added) from '{query_name}': {added_data}")

    def on_result_updated(self, query_name: str, updated_data: dict[str, Any]) -> None:
        notification = {
            "type": "updated",
            "query": query_name,
            "data": updated_data,
            "timestamp": time.time()
        }
        self.notification_queue.put(notification)
        print(f"[{self.agent_id}] 🔔 Notification (updated) from '{query_name}': {updated_data}")

    def on_result_deleted(self, query_name: str, deleted_data: dict[str, Any]) -> None:
        notification = {
            "type": "deleted",
            "query": query_name,
            "data": deleted_data,
            "timestamp": time.time()
        }
        self.notification_queue.put(notification)
        print(f"[{self.agent_id}] 🔔 Notification (deleted) from '{query_name}': {deleted_data}")

    def has_new_notifications(self) -> bool:
        return not self.notification_queue.empty()

    def get_new_notifications(self) -> list:
        notifications = []
        while not self.notification_queue.empty():
            notifications.append(self.notification_queue.get())
        return notifications

    def custom_log(self, message: str) -> None:
        print(f"[{self.agent_id}] [Custom Sensor Log] {message}")
        notification = {
            "data": message,
            "timestamp": time.time()
        }
        self.notification_queue.put(notification)
