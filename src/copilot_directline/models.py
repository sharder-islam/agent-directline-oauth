"""Data models for Direct Line API interactions."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Conversation:
    """Represents a Direct Line conversation."""

    conversation_id: str
    token: str
    expires_in: int
    stream_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create a Conversation from API response dictionary."""
        return cls(
            conversation_id=data.get("conversationId", ""),
            token=data.get("token", ""),
            expires_in=data.get("expires_in", 0),
            stream_url=data.get("streamUrl"),
        )


@dataclass
class Activity:
    """Represents a Direct Line activity (message or event)."""

    id: str
    type: str
    from_user: Dict[str, str]
    text: Optional[str] = None
    channel_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Activity":
        """Create an Activity from API response dictionary."""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            from_user=data.get("from", {}),
            text=data.get("text"),
            channel_data=data.get("channelData"),
            timestamp=data.get("timestamp"),
            attachments=data.get("attachments"),
        )


@dataclass
class Message:
    """Represents a message to send to the bot."""

    text: str
    type: str = "message"
    from_user: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for API request."""
        message_dict: Dict[str, Any] = {
            "type": self.type,
            "text": self.text,
        }
        if self.from_user:
            message_dict["from"] = self.from_user
        return message_dict


@dataclass
class ActivitiesResponse:
    """Response containing activities from Direct Line API."""

    activities: List[Activity]
    watermark: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActivitiesResponse":
        """Create an ActivitiesResponse from API response dictionary."""
        activities = [
            Activity.from_dict(activity) for activity in data.get("activities", [])
        ]
        return cls(
            activities=activities,
            watermark=data.get("watermark"),
        )
