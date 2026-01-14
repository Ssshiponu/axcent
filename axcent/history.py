import json
import os
from typing import List, Dict, Any, Optional
from collections import UserList

class ConversationHistory(UserList):
    def __init__(self, initial: List[Dict[str, Any]] = [], persist: bool = False, filepath: str = "conv.json", max_messages: Optional[int] = None, keep_system_prompt: bool = True):
        super().__init__(initial)
        self.persist = persist
        self.filepath = filepath
        self.max_messages = max_messages
        self.keep_system_prompt = keep_system_prompt
        # Load existing history if file exists
        self._load()
        self._enforce_limit()

    def _save(self):
        """Internal logic to sync with JSON file safely."""
        if not self.persist or not self.filepath:
            return
        
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    def _load(self):
        if not self.persist or not self.filepath:
            return
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading history: {e}")
            self.data = []

    def _enforce_limit(self):
        """Enforce the maximum number of messages, preserving system prompt if configured."""
        if self.max_messages is None or len(self.data) <= self.max_messages:
            return

        # Keep system prompt if it exists and keep_system_prompt is True
        system_prompt = None
        if self.keep_system_prompt and self.data and self.data[0].get("role") == "system":
            system_prompt = self.data[0]
            start_index = 1
        else:
            start_index = 0

        # Calculate how many messages to keep (excluding the system prompt)
        remaining_slots = self.max_messages - (1 if system_prompt else 0)
        
        # Take the most recent messages
        self.data = self.data[-remaining_slots:] if remaining_slots > 0 else []
        
        # Re-insert system prompt at the beginning
        if system_prompt:
            self.data.insert(0, system_prompt)

    # Override mutation methods to trigger limit enforcement and save
    def append(self, item):
        super().append(item)
        self._enforce_limit()
        self._save()

    def extend(self, other):
        super().extend(other)
        self._enforce_limit()
        self._save()

    def clear(self):
        super().clear()
        self._save()

    def get_last_message(self) -> Optional[Dict[str, Any]]:
        return self.data[-1] if self.data else None

    def to_text(self) -> str:
        """Returns the conversation as a readable string."""
        lines = []
        for msg in self.data:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role.capitalize()}: {content}")
        return "\n".join(lines)
