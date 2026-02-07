import asyncio
import logging
import os
from dotenv import load_dotenv

from bot_optimist import create_optimist_bot
from bot_pessimist import create_pessimist_bot
from orchestrator import orchestrator

# Load environment variables
load_dotenv()

# Setup logging with more detail
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detail
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord.log', encoding='utf-8', mode='w'),
        logging.StreamHandler()
    ]
)

# Set specific log levels for different modules
logging.getLogger('discord').setLevel(logging.INFO)  # Less verbose Discord library logs
logging.getLogger('discord.http').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

# Your app logs at DEBUG level
logging.getLogger('orchestrator').setLevel(logging.DEBUG)
logging.getLogger('bot_optimist').setLevel(logging.DEBUG)
logging.getLogger('bot_pessimist').setLevel(logging.DEBUG)
logging.getLogger('backboard_client').setLevel(logging.INFO)

logger = logging.getLogger(__name__)


async def main():
    """Run both Discord bots in one process."""
    
    # Get tokens
    optimist_token = os.getenv('OPTIMIST_TOKEN')
    pessimist_token = os.getenv('PESSIMIST_TOKEN')
    
    if not optimist_token:
        raise ValueError("OPTIMIST_TOKEN not set in .env")
    if not pessimist_token:
        raise ValueError("PESSIMIST_TOKEN not set in .env")
    
    # Create bot instances
    logger.info("Creating bot instances...")
    optimist_bot = create_optimist_bot()
    pessimist_bot = create_pessimist_bot()
    
    # Register bots with orchestrator
    logger.info("Registering bots with orchestrator...")
    orchestrator.set_bots(optimist_bot, pessimist_bot)
    
    logger.info("Starting both bots...")
    
    try:
        # Run both bots concurrently
        async with asyncio.TaskGroup() as tg:
            tg.create_task(optimist_bot.start(optimist_token))
            tg.create_task(pessimist_bot.start(pessimist_token))
    finally:
        # Clean up Backboard client
        logger.info("Cleaning up Backboard client...")
        from backboard_client import backboard
        await backboard.close()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down bots...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise