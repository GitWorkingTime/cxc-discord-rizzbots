from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class UserSession:
    """Stores Backboard thread IDs and assistant IDs for a user."""
    optimist_thread: str
    pessimist_thread: str
    optimist_assistant_id: str
    pessimist_assistant_id: str


@dataclass
class ChannelSetup:
    """Stores Discord channel configuration."""
    player1_id: str
    player2_id: str
    general_channel_id: str
    player1_room_id: str
    player2_room_id: str


@dataclass
class Session:
    """Global session data for debate analysis."""
    
    # User sessions: user_id -> UserSession
    users: Dict[str, UserSession] = field(default_factory=dict)
    
    # Channel setup per guild: guild_id -> ChannelSetup
    channels: Dict[str, ChannelSetup] = field(default_factory=dict)
    
    def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """Get session for a user."""
        return self.users.get(user_id)
    
    def set_user_session(
        self,
        user_id: str,
        optimist_thread: str,
        pessimist_thread: str,
        optimist_assistant_id: str,
        pessimist_assistant_id: str
    ) -> None:
        """Set session for a user."""
        self.users[user_id] = UserSession(
            optimist_thread=optimist_thread,
            pessimist_thread=pessimist_thread,
            optimist_assistant_id=optimist_assistant_id,
            pessimist_assistant_id=pessimist_assistant_id
        )
    
    def get_channel_setup(self, guild_id: str) -> Optional[ChannelSetup]:
        """Get channel setup for a guild."""
        return self.channels.get(guild_id)
    
    def set_channel_setup(
        self,
        guild_id: str,
        player1_id: str,
        player2_id: str,
        general_channel_id: str,
        player1_room_id: str,
        player2_room_id: str
    ) -> None:
        """Set channel setup for a guild."""
        self.channels[guild_id] = ChannelSetup(
            player1_id=player1_id,
            player2_id=player2_id,
            general_channel_id=general_channel_id,
            player1_room_id=player1_room_id,
            player2_room_id=player2_room_id
        )


# Global session instance
session = Session()
