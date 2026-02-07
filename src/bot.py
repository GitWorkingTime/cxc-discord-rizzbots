import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv

from backboard_client import BackboardClient
from session import session
from prompts import (
    get_setup_prompt,
    get_turn_prompt,
    get_advice_prompt,
    get_user_messages_context
)

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
backboard = BackboardClient()

# Constants
DEBATE_TURNS = 20
ANALYSIS_TIMEOUT = 300.0  # 5 minutes total
TURN_TIMEOUT = 30.0  # 30 seconds per turn
COOLDOWN_SECONDS = 60.0
MAX_MESSAGE_LENGTH = 1900  # Discord limit is 2000, leave buffer


async def fetch_user_messages(
    guild: discord.Guild, 
    user: discord.Member, 
    limit: int = 50
) -> List[str]:
    """Fetch recent messages from a user across all channels."""
    messages = []
    
    for channel in guild.text_channels:
        try:
            async for message in channel.history(limit=limit):
                if message.author.id == user.id:
                    messages.append(message.content)
        except discord.Forbidden:
            continue
        except Exception as e:
            logger.error(f"Error fetching messages from {channel.name}: {e}")
            continue
    
    return messages


async def true_alternation(
    user_id: str,
    username: str,
    user_messages: List[str],
    optimist_thread: str,
    pessimist_thread: str
) -> Dict[str, str]:
    """
    Run true alternation debate between optimist and pessimist.
    Returns dict with 'debate', 'optimist_advice', 'pessimist_advice'.
    """
    # Setup context
    context = get_user_messages_context(user_messages, username)
    
    # Initialize both threads with setup prompts and context
    setup_optimist = get_setup_prompt("optimist", username)
    setup_pessimist = get_setup_prompt("pessimist", username)
    
    await backboard.add_message(optimist_thread, setup_optimist + "\n\n" + context)
    await backboard.add_message(pessimist_thread, setup_pessimist + "\n\n" + context)
    
    # Run debate turns
    debate_lines = []
    
    for turn in range(DEBATE_TURNS):
        # Determine who speaks this turn
        is_optimist_turn = (turn % 2 == 0)
        perspective = "optimist" if is_optimist_turn else "pessimist"
        thread_id = optimist_thread if is_optimist_turn else pessimist_thread
        assistant_id = backboard.optimist_assistant_id if is_optimist_turn else backboard.pessimist_assistant_id
        other_thread = pessimist_thread if is_optimist_turn else optimist_thread
        
        # Build debate history
        debate_history = "\n".join(debate_lines) if debate_lines else "No debate yet."
        
        # Create turn prompt
        turn_prompt = get_turn_prompt(perspective, turn, debate_history)
        
        # Add to current speaker's thread
        await backboard.add_message(thread_id, turn_prompt)
        
        # Run assistant
        try:
            response = await backboard.run_assistant(
                thread_id, 
                assistant_id, 
                timeout=TURN_TIMEOUT
            )
            
            # Extract the line (should start with "Optimist:" or "Pessimist:")
            lines = response.strip().split('\n')
            prefix = "Optimist:" if is_optimist_turn else "Pessimist:"
            
            # Find line starting with correct prefix
            debate_line = None
            for line in lines:
                if line.strip().startswith(prefix):
                    debate_line = line.strip()
                    break
            
            if not debate_line:
                # Fallback: use first non-empty line and add prefix
                for line in lines:
                    if line.strip():
                        debate_line = f"{prefix} {line.strip()}"
                        break
            
            if not debate_line:
                debate_line = f"{prefix} [No response]"
            
            # Enforce word limit (18 words)
            words = debate_line.split()
            if len(words) > 20:  # prefix + 18 words max
                debate_line = " ".join(words[:20]) + "..."
            
            debate_lines.append(debate_line)
            
            # Add this line to the OTHER bot's thread for context
            await backboard.add_message(other_thread, debate_line)
            
        except TimeoutError as e:
            logger.error(f"Turn {turn} timeout: {e}")
            debate_line = f"{prefix} [Timeout]"
            debate_lines.append(debate_line)
        except Exception as e:
            logger.error(f"Turn {turn} error: {e}")
            debate_line = f"{prefix} [Error]"
            debate_lines.append(debate_line)
    
    # Generate advice from both bots
    full_debate = "\n".join(debate_lines)
    
    # Optimist advice
    optimist_advice_prompt = get_advice_prompt("optimist", full_debate)
    await backboard.add_message(optimist_thread, optimist_advice_prompt)
    
    try:
        optimist_advice = await backboard.run_assistant(
            optimist_thread,
            backboard.optimist_assistant_id,
            timeout=TURN_TIMEOUT
        )
    except Exception as e:
        logger.error(f"Optimist advice error: {e}")
        optimist_advice = "Optimist Advice:\n1) Unable to generate\n2) Please try again\n3) Error occurred"
    
    # Pessimist advice
    pessimist_advice_prompt = get_advice_prompt("pessimist", full_debate)
    await backboard.add_message(pessimist_thread, pessimist_advice_prompt)
    
    try:
        pessimist_advice = await backboard.run_assistant(
            pessimist_thread,
            backboard.pessimist_assistant_id,
            timeout=TURN_TIMEOUT
        )
    except Exception as e:
        logger.error(f"Pessimist advice error: {e}")
        pessimist_advice = "Pessimist Advice:\n1) Unable to generate\n2) Please try again\n3) Error occurred"
    
    return {
        "debate": full_debate,
        "optimist_advice": optimist_advice.strip(),
        "pessimist_advice": pessimist_advice.strip()
    }


def split_message(content: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
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


@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"Bot ready: {bot.user.name}")
    logger.info("Slash commands synced")


@bot.tree.command(name="setup", description="Setup debate threads for your account")
async def setup(interaction: discord.Interaction):
    """Create optimist and pessimist threads for the user."""
    await interaction.response.defer(ephemeral=True)
    
    user_id = str(interaction.user.id)
    
    try:
        # Check if threads already exist
        existing = session.get_threads(user_id)
        if existing:
            await interaction.followup.send(
                "✅ You already have threads set up!\n"
                f"Optimist: `{existing['optimist']}`\n"
                f"Pessimist: `{existing['pessimist']}`",
                ephemeral=True
            )
            return
        
        # Create new threads
        optimist_thread = await backboard.create_thread()
        pessimist_thread = await backboard.create_thread()
        
        # Store in session
        session.set_threads(user_id, optimist_thread, pessimist_thread)
        
        await interaction.followup.send(
            "✅ Debate threads created!\n"
            f"Optimist: `{optimist_thread}`\n"
            f"Pessimist: `{pessimist_thread}`\n\n"
            "Use `/analyze` to start the debate!",
            ephemeral=True
        )
        
    except Exception as e:
        logger.error(f"Setup error for {interaction.user.name}: {e}")
        await interaction.followup.send(
            f"❌ Setup failed: {str(e)}",
            ephemeral=True
        )


@bot.tree.command(name="analyze", description="Run debate analysis on your messages")
async def analyze(interaction: discord.Interaction):
    """Analyze user's messages with true alternation debate."""
    await interaction.response.defer()
    
    user_id = str(interaction.user.id)
    username = interaction.user.display_name
    
    # Check cooldown
    if not session.can_analyze(COOLDOWN_SECONDS):
        remaining = session.time_until_ready(COOLDOWN_SECONDS)
        await interaction.followup.send(
            f"⏳ Analysis on cooldown. Try again in {int(remaining)} seconds."
        )
        return
    
    # Acquire lock
    if session.analyze_lock.locked():
        await interaction.followup.send(
            "⏳ An analysis is already running. Please wait."
        )
        return
    
    async with session.analyze_lock:
        session.update_analyze_timestamp()
        
        try:
            # Check for threads
            threads = session.get_threads(user_id)
            if not threads:
                await interaction.followup.send(
                    "❌ No threads found. Use `/setup` first!"
                )
                return
            
            optimist_thread = threads['optimist']
            pessimist_thread = threads['pessimist']
            
            # Fetch user messages
            await interaction.followup.send(
                f"🔍 Analyzing messages for {username}..."
            )
            
            user_messages = await fetch_user_messages(
                interaction.guild,
                interaction.user,
                limit=100
            )
            
            if not user_messages:
                await interaction.followup.send(
                    "❌ No messages found to analyze."
                )
                return
            
            await interaction.followup.send(
                f"📊 Found {len(user_messages)} messages. Starting debate..."
            )
            
            # Run true alternation with timeout
            try:
                result = await asyncio.wait_for(
                    true_alternation(
                        user_id,
                        username,
                        user_messages,
                        optimist_thread,
                        pessimist_thread
                    ),
                    timeout=ANALYSIS_TIMEOUT
                )
                
                # Send debate
                debate_msg = f"**🎭 Debate for {username}**\n```\n{result['debate']}\n```"
                for chunk in split_message(debate_msg):
                    await interaction.followup.send(chunk)
                
                # Send advice
                advice_msg = (
                    f"**💡 Final Advice**\n\n"
                    f"**{result['optimist_advice']}**\n\n"
                    f"**{result['pessimist_advice']}**"
                )
                for chunk in split_message(advice_msg):
                    await interaction.followup.send(chunk)
                
            except asyncio.TimeoutError:
                await interaction.followup.send(
                    f"❌ Analysis timed out after {ANALYSIS_TIMEOUT}s. Please try again."
                )
                logger.error(f"Analysis timeout for {username}")
            
        except Exception as e:
            logger.error(f"Analysis error for {username}: {e}")
            await interaction.followup.send(
                f"❌ Analysis failed: {str(e)}"
            )


def run_bot():
    """Run the Discord bot."""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("DISCORD_TOKEN not set")
    
    handler = logging.FileHandler(
        filename='discord.log', 
        encoding='utf-8', 
        mode='w'
    )
    
    bot.run(token, log_handler=handler, log_level=logging.INFO)


if __name__ == "__main__":
    run_bot()
