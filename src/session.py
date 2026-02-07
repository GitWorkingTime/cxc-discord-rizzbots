import asyncio
from typing import Dict, Optional
from dataclasses import dataclass, field
import time


@dataclass
class AnalysisSession:
    """Stores session data for debate analysis."""
    
    user_threads: Dict[str, Dict[str, str]] = field(default_factory=dict)
    last_analyze_timestamp: float = 0.0
    analyze_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    def can_analyze(self, cooldown_seconds: float = 60.0) -> bool:
        """Check if enough time has passed since last analysis."""
        current_time = time.time()
        return (current_time - self.last_analyze_timestamp) >= cooldown_seconds
    
    def time_until_ready(self, cooldown_seconds: float = 60.0) -> float:
        """Return seconds until next analysis is allowed."""
        current_time = time.time()
        elapsed = current_time - self.last_analyze_timestamp
        remaining = cooldown_seconds - elapsed
        return max(0.0, remaining)
    
    def update_analyze_timestamp(self) -> None:
        """Update the last analysis timestamp to now."""
        self.last_analyze_timestamp = time.time()
    
    def get_threads(self, user_id: str) -> Optional[Dict[str, str]]:
        """Get thread IDs for a user."""
        return self.user_threads.get(user_id)
    
    def set_threads(self, user_id: str, optimist_thread: str, pessimist_thread: str) -> None:
        """Set thread IDs for a user."""
        self.user_threads[user_id] = {
            "optimist": optimist_thread,
            "pessimist": pessimist_thread
        }


# Global session instance
session = AnalysisSession()
