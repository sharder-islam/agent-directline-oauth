"""Copilot Studio Direct Line OAuth Library.

A secure Python solution for accessing Copilot Studio agents via Direct Line API
with Microsoft Entra ID OAuth authentication.
"""

from copilot_directline.auth import EntraIDAuth
from copilot_directline.directline import DirectLineClient
from copilot_directline.models import Activity, Conversation, Message

__version__ = "0.1.0"
__all__ = [
    "EntraIDAuth",
    "DirectLineClient",
    "Activity",
    "Conversation",
    "Message",
]
