"""
memory.py
---------
Simple memory system for agents.

ShortTermMemory  - remembers the current conversation (cleared each session)
LongTermMemory   - remembers important facts across sessions (key-value store)
"""


class ShortTermMemory:
    """Stores conversation history for the current session."""

    def __init__(self):
        self.history = []

    def add(self, role, message):
        self.history.append({"role": role, "message": message})

    def get(self):
        return self.history

    def clear(self):
        self.history = []


class LongTermMemory:
    """Stores important facts that should be remembered across sessions."""

    def __init__(self):
        self.facts = {}

    def save(self, key, value):
        self.facts[key] = value

    def recall(self, key):
        return self.facts.get(key, None)

    def show_all(self):
        return self.facts


# Create one instance of each memory type to share across the app
short_memory = ShortTermMemory()
long_memory  = LongTermMemory()
