import discord
from discord.ext import commands
import logging

from orchestrator import orchestrator
from session import session

logger = logging.getLogger(__name__)


class PessimistBot(commands.Bot):
    """Pessimist Discord bot (no commands, only for posting)."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(command_prefix='!pess_', intents=intents)
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Pessimist bot ready: {self.user.name}")
    
    async def on_message(self, message: discord.Message):
        """Buffer messages from general channel."""
        if message.author.bot:
            return
        
        # Check if this is a tracked general channel
        if message.guild:
            guild_id = str(message.guild.id)
            channel_setup = session.get_channel_setup(guild_id)
            
            if channel_setup and str(message.channel.id) == channel_setup.general_channel_id:
                # Buffer this message WITH USER INFO
                message_data = {
                    'content': message.content,
                    'author_name': message.author.name,
                    'author_id': str(message.author.id),
                    'timestamp': message.created_at.isoformat()
                }
                
                # Log the message data
                logger.debug(
                    f"Pessimist bot buffered | Guild: {guild_id} | "
                    f"User: {message_data['author_name']} (ID: {message_data['author_id']}) | "
                    f"Content: {message_data['content'][:50]}{'...' if len(message_data['content']) > 50 else ''}"
                )
                
                orchestrator.add_message(guild_id, str(message.channel.id), message_data)
        
        await self.process_commands(message)


def create_pessimist_bot() -> PessimistBot:
    """Create and configure the Pessimist bot."""
    bot = PessimistBot()
    return bot