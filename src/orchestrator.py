import asyncio
import time
import logging
from typing import List, Dict, Optional, TYPE_CHECKING
from collections import deque

if TYPE_CHECKING:
    import discord

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Coordinates both Discord bots and manages shared state.
    """
    
    def __init__(self):
        # Bot references (set by main.py after bot initialization)
        self.optimist_bot: Optional['discord.Client'] = None
        self.pessimist_bot: Optional['discord.Client'] = None
        
        # Message buffers: guild_id -> channel_id -> deque of message dicts
        self.message_buffers: Dict[str, Dict[str, deque]] = {}
        self.buffer_size = 25
        
        # Analysis state
        self.analyze_lock = asyncio.Lock()
        self.last_analyze_timestamp = 0.0
        self.cooldown_seconds = 60.0
        
    def set_bots(self, optimist_bot: 'discord.Client', pessimist_bot: 'discord.Client') -> None:
        """Set bot references."""
        self.optimist_bot = optimist_bot
        self.pessimist_bot = pessimist_bot
    
    def add_message(self, guild_id: str, channel_id: str, message_data: Dict[str, str]) -> None:
        """
        Add a message to the buffer for a channel.
        
        Args:
            guild_id: Discord guild ID
            channel_id: Discord channel ID
            message_data: Dict containing 'content', 'author_name', 'author_id', 'timestamp'
        """
        if guild_id not in self.message_buffers:
            self.message_buffers[guild_id] = {}
        
        if channel_id not in self.message_buffers[guild_id]:
            self.message_buffers[guild_id][channel_id] = deque(maxlen=self.buffer_size)
        
        self.message_buffers[guild_id][channel_id].append(message_data)
    
    def get_messages(self, guild_id: str, channel_id: str) -> List[Dict[str, str]]:
        """
        Get buffered messages for a channel.
        
        Returns:
            List of message dicts with 'content', 'author_name', 'author_id', 'timestamp'
        """
        if guild_id in self.message_buffers:
            if channel_id in self.message_buffers[guild_id]:
                return list(self.message_buffers[guild_id][channel_id])
        return []
    
    def format_messages_for_ai(self, messages: List[Dict[str, str]], target_user_id: Optional[str] = None) -> str:
        """
        Format buffered messages for AI consumption with clear user separation.
        
        Args:
            messages: List of message dicts
            target_user_id: Optional user ID to highlight/filter
            
        Returns:
            Formatted string with clear user attribution
        """
        if not messages:
            return ""
        
        formatted = []
        for msg in messages:
            author_name = msg.get('author_name', 'Unknown')
            author_id = msg.get('author_id', '000000')
            content = msg.get('content', '')
            
            # Format: [User: name (ID: id)]: message
            formatted.append(f"[User: {author_name} (ID: {author_id})]: {content}")
        
        return "\n".join(formatted)
    
    def get_messages_by_user(self, guild_id: str, channel_id: str, user_id: str) -> List[Dict[str, str]]:
        """
        Get messages from a specific user only.
        
        Args:
            guild_id: Discord guild ID
            channel_id: Discord channel ID
            user_id: Target user's Discord ID
            
        Returns:
            List of message dicts from that user only
        """
        all_messages = self.get_messages(guild_id, channel_id)
        return [msg for msg in all_messages if msg.get('author_id') == user_id]
    
    def get_user_message_count(self, guild_id: str, channel_id: str, user_id: str) -> int:
        """Count how many messages a specific user has in the buffer."""
        return len(self.get_messages_by_user(guild_id, channel_id, user_id))
    
    def can_analyze(self) -> bool:
        """Check if enough time has passed since last analysis."""
        current_time = time.time()
        return (current_time - self.last_analyze_timestamp) >= self.cooldown_seconds
    
    def time_until_ready(self) -> float:
        """Return seconds until next analysis is allowed."""
        current_time = time.time()
        elapsed = current_time - self.last_analyze_timestamp
        remaining = self.cooldown_seconds - elapsed
        return max(0.0, remaining)
    
    def update_analyze_timestamp(self) -> None:
        """Update the last analysis timestamp to now."""
        self.last_analyze_timestamp = time.time()
    
    async def post_as_optimist(self, channel: 'discord.TextChannel', content: str) -> None:
        """Post a message using the Optimist bot."""
        if not self.optimist_bot:
            logger.error("Optimist bot not set")
            return
        
        # Get the channel from optimist bot's perspective
        optimist_channel = self.optimist_bot.get_channel(channel.id)
        if optimist_channel and hasattr(optimist_channel, 'send'):
            await optimist_channel.send(content)
        else:
            logger.error(f"Optimist bot cannot access channel {channel.id}")
    
    async def post_as_pessimist(self, channel: 'discord.TextChannel', content: str) -> None:
        """Post a message using the Pessimist bot."""
        if not self.pessimist_bot:
            logger.error("Pessimist bot not set")
            return
        
        # Get the channel from pessimist bot's perspective
        pessimist_channel = self.pessimist_bot.get_channel(channel.id)
        if pessimist_channel and hasattr(pessimist_channel, 'send'):
            await pessimist_channel.send(content)
        else:
            logger.error(f"Pessimist bot cannot access channel {channel.id}")
    
    def split_message(self, content: str, max_length: int = 1900) -> List[str]:
        """Split a message into chunks under Discord's limit."""
        if len(content) <= max_length:
            return [content]
        
        chunks = []
        current_chunk = ""
        
        for line in content.split('\n'):
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


# Global orchestrator instance
orchestrator = Orchestrator()