import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from typing import List, Dict
import os

from session import session
from orchestrator import orchestrator
from backboard_client import backboard
from prompts import (
    get_setup_prompt,
    get_turn_prompt,
    get_advice_prompt,
    get_user_messages_context
)

logger = logging.getLogger(__name__)

# Constants
DEBATE_TURNS = 6
ANALYSIS_TIMEOUT = 300.0  # 5 minutes total
TURN_TIMEOUT = 30.0  # 30 seconds per turn


class OptimistBot(commands.Bot):
    """Optimist Discord bot with slash commands."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(command_prefix='!opt_', intents=intents)
    
    async def setup_hook(self):
        """Sync commands on startup."""
        await self.tree.sync()
        logger.info("Optimist bot commands synced")
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Optimist bot ready: {self.user.name}")
    
    async def on_message(self, message: discord.Message):
        """Buffer messages from general channel."""
        if message.author.bot:
            return
        
        # Check if this is a tracked general channel
        if message.guild:
            guild_id = str(message.guild.id)
            channel_setup = session.get_channel_setup(guild_id)
            
            if channel_setup and str(message.channel.id) == channel_setup.general_channel_id:
                # Buffer this message
                orchestrator.add_message(guild_id, str(message.channel.id), message.content)
        
        await self.process_commands(message)


def create_optimist_bot() -> OptimistBot:
    """Create and configure the Optimist bot."""
    bot = OptimistBot()
    
    @bot.tree.command(name="setup", description="Setup debate analysis for two players")
    @app_commands.describe(
        player1="First player to analyze",
        player2="Second player to analyze",
        general="General chat channel",
        player1_room="Player 1's private room",
        player2_room="Player 2's private room",
        optimist_assistant="Optimist assistant ID",
        pessimist_assistant="Pessimist assistant ID"
    )
    async def setup(
        interaction: discord.Interaction,
        player1: discord.Member,
        player2: discord.Member,
        general: discord.TextChannel,
        player1_room: discord.TextChannel,
        player2_room: discord.TextChannel,
        optimist_assistant: str,
        pessimist_assistant: str
    ):
        """Setup channel configuration and create threads for both players."""
        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild.id)
        
        try:
            # Store channel setup
            session.set_channel_setup(
                guild_id=guild_id,
                player1_id=str(player1.id),
                player2_id=str(player2.id),
                general_channel_id=str(general.id),
                player1_room_id=str(player1_room.id),
                player2_room_id=str(player2_room.id)
            )
            
            # Create sessions for player1
            session.set_user_session(
                user_id=str(player1.id),
                optimist_assistant_id=optimist_assistant,
                pessimist_assistant_id=pessimist_assistant
            )
            
            # Create sessions for player2
            session.set_user_session(
                user_id=str(player2.id),
                optimist_assistant_id=optimist_assistant,
                pessimist_assistant_id=pessimist_assistant
            )
            
            await interaction.followup.send(
                f"✅ Setup complete!\n\n"
                f"**Players:** {player1.mention}, {player2.mention}\n"
                f"**General:** {general.mention}\n"
                f"**Rooms:** {player1_room.mention}, {player2_room.mention}\n\n"
                f"Use `/analyze` to start debates!",
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Setup error: {e}")
            await interaction.followup.send(
                f"❌ Setup failed: {str(e)}",
                ephemeral=True
            )
    
    @bot.tree.command(name="analyze", description="Run debate analysis on both players")
    async def analyze(interaction: discord.Interaction):
        """Analyze both players with true alternation debate."""
        await interaction.response.defer()
        
        guild_id = str(interaction.guild.id)
        
        # Check cooldown
        if not orchestrator.can_analyze():
            remaining = orchestrator.time_until_ready()
            await interaction.followup.send(
                f"⏳ Analysis on cooldown. Try again in {int(remaining)} seconds."
            )
            return
        
        # Acquire lock
        if orchestrator.analyze_lock.locked():
            await interaction.followup.send(
                "⏳ An analysis is already running. Please wait."
            )
            return
        
        async with orchestrator.analyze_lock:
            orchestrator.update_analyze_timestamp()
            
            try:
                # Get channel setup
                channel_setup = session.get_channel_setup(guild_id)
                if not channel_setup:
                    await interaction.followup.send(
                        "❌ No setup found. Use `/setup` first!"
                    )
                    return
                
                # Get player sessions
                p1_session = session.get_user_session(channel_setup.player1_id)
                p2_session = session.get_user_session(channel_setup.player2_id)
                
                if not p1_session or not p2_session:
                    await interaction.followup.send(
                        "❌ Player sessions not found. Re-run `/setup`!"
                    )
                    return
                
                # Get channels
                general_channel = bot.get_channel(int(channel_setup.general_channel_id))
                p1_room = bot.get_channel(int(channel_setup.player1_room_id))
                p2_room = bot.get_channel(int(channel_setup.player2_room_id))
                
                if not all([general_channel, p1_room, p2_room]):
                    await interaction.followup.send(
                        "❌ Cannot access configured channels!"
                    )
                    return
                
                # Get buffered messages
                messages = orchestrator.get_messages(guild_id, channel_setup.general_channel_id)
                
                if not messages:
                    await interaction.followup.send(
                        "❌ No messages in general channel to analyze."
                    )
                    return
                
                await interaction.followup.send(
                    f"🔍 Analyzing {len(messages)} messages from general chat..."
                )
                
                # Get player info
                player1 = await bot.fetch_user(int(channel_setup.player1_id))
                player2 = await bot.fetch_user(int(channel_setup.player2_id))
                
                # Run analysis for both players
                try:
                    # Analyze player 1
                    await orchestrator.post_as_optimist(
                        p1_room,
                        f"🎭 Starting debate analysis for {player1.display_name}..."
                    )
                    
                    p1_result = await asyncio.wait_for(
                        run_true_alternation(
                            user_id=channel_setup.player1_id,
                            username=player1.display_name,
                            user_messages=messages,
                            user_session=p1_session,
                            output_channel=p1_room
                        ),
                        timeout=ANALYSIS_TIMEOUT
                    )
                    
                    # Analyze player 2
                    await orchestrator.post_as_optimist(
                        p2_room,
                        f"🎭 Starting debate analysis for {player2.display_name}..."
                    )
                    
                    p2_result = await asyncio.wait_for(
                        run_true_alternation(
                            user_id=channel_setup.player2_id,
                            username=player2.display_name,
                            user_messages=messages,
                            user_session=p2_session,
                            output_channel=p2_room
                        ),
                        timeout=ANALYSIS_TIMEOUT
                    )
                    
                    await interaction.followup.send(
                        "✅ Analysis complete! Check the player rooms for results."
                    )
                    
                except asyncio.TimeoutError:
                    await interaction.followup.send(
                        f"❌ Analysis timed out after {ANALYSIS_TIMEOUT}s. Please try again."
                    )
                    logger.error("Analysis timeout")
                
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                await interaction.followup.send(
                    f"❌ Analysis failed: {str(e)}"
                )
    
    return bot


async def run_true_alternation(
    user_id: str,
    username: str,
    user_messages: List[str],
    user_session: 'session.UserSession',
    output_channel: discord.TextChannel
) -> Dict[str, str]:
    """
    Run true alternation debate between optimist and pessimist.
    Posts messages in real-time to the output channel.
    Returns dict with 'debate', 'optimist_advice', 'pessimist_advice'.
    """
    # Setup context
    context = get_user_messages_context(user_messages, username)
    
    # Initialize both threads with setup prompts
    setup_optimist = get_setup_prompt("optimist", username)
    setup_pessimist = get_setup_prompt("pessimist", username)

    user_session.optimist_thread_id = await backboard.create_thread(
        user_session.optimist_assistant_id
    )
    user_session.pessimist_thread_id = await backboard.create_thread(
        user_session.pessimist_assistant_id
    )

    # Seed context without invoking the LLM
    await backboard.send_message(
        thread_id=user_session.optimist_thread_id,
        content=f"{setup_optimist}\n\n{context}",
        send_to_llm=False,
        memory="off"
    )
    await backboard.send_message(
        thread_id=user_session.pessimist_thread_id,
        content=f"{setup_pessimist}\n\n{context}",
        send_to_llm=False,
        memory="off"
    )
    
    # Run debate turns
    debate_lines = []
    
    for turn in range(DEBATE_TURNS):
        # Determine who speaks this turn
        is_optimist_turn = (turn % 2 == 0)
        perspective = "optimist" if is_optimist_turn else "pessimist"
        current_thread = user_session.optimist_thread_id if is_optimist_turn else user_session.pessimist_thread_id
        other_thread = user_session.pessimist_thread_id if is_optimist_turn else user_session.optimist_thread_id
        prefix = "Optimist:" if is_optimist_turn else "Pessimist:"
        
        # Build debate history
        debate_history = "\n".join(debate_lines) if debate_lines else "No debate yet."
        
        # Create turn prompt
        turn_prompt = get_turn_prompt(perspective, turn, debate_history)
        
        # Send message and get response
        try:
            response = await backboard.send_message(
                thread_id=current_thread,
                content=turn_prompt,
                timeout=TURN_TIMEOUT,
                memory="Auto"
            )
            
            # Extract the line (should start with "Optimist:" or "Pessimist:")
            lines = response.strip().split('\n')
            
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
            
            # Add this line to the OTHER bot's thread for context (no LLM call)
            await backboard.send_message(
                thread_id=other_thread,
                content=f"The other debater said: {debate_line}",
                send_to_llm=False,
                memory="off"
            )
            
            # Post to Discord using appropriate bot
            if is_optimist_turn:
                await orchestrator.post_as_optimist(output_channel, f"```{debate_line}```")
            else:
                await orchestrator.post_as_pessimist(output_channel, f"```{debate_line}```")
            
        except TimeoutError as e:
            logger.error(f"Turn {turn} timeout: {e}")
            debate_line = f"{prefix} [Timeout]"
            debate_lines.append(debate_line)
            await orchestrator.post_as_optimist(output_channel, f"⚠️ Turn {turn} timed out")
        except Exception as e:
            logger.error(f"Turn {turn} error: {e}")
            debate_line = f"{prefix} [Error]"
            debate_lines.append(debate_line)
            await orchestrator.post_as_optimist(output_channel, f"⚠️ Turn {turn} error: {str(e)}")
    
    # Generate advice from both bots
    full_debate = "\n".join(debate_lines)
    
    # Optimist advice
    await orchestrator.post_as_optimist(output_channel, "\n**💡 Generating Optimist advice...**")
    optimist_advice_prompt = get_advice_prompt("optimist", full_debate)
    
    try:
        optimist_advice = await backboard.send_message(
            thread_id=user_session.optimist_thread_id,
            content=optimist_advice_prompt,
            timeout=TURN_TIMEOUT,
            memory="Auto"
        )
    except Exception as e:
        logger.error(f"Optimist advice error: {e}")
        optimist_advice = "Optimist Advice:\n1) Unable to generate\n2) Please try again\n3) Error occurred"
    
    # Post optimist advice
    for chunk in orchestrator.split_message(f"**{optimist_advice.strip()}**"):
        await orchestrator.post_as_optimist(output_channel, chunk)
    
    # Pessimist advice
    await orchestrator.post_as_pessimist(output_channel, "\n**💡 Generating Pessimist advice...**")
    pessimist_advice_prompt = get_advice_prompt("pessimist", full_debate)
    
    try:
        pessimist_advice = await backboard.send_message(
            thread_id=user_session.pessimist_thread_id,
            content=pessimist_advice_prompt,
            timeout=TURN_TIMEOUT,
            memory="Auto"
        )
    except Exception as e:
        logger.error(f"Pessimist advice error: {e}")
        pessimist_advice = "Pessimist Advice:\n1) Unable to generate\n2) Please try again\n3) Error occurred"
    
    # Post pessimist advice
    for chunk in orchestrator.split_message(f"**{pessimist_advice.strip()}**"):
        await orchestrator.post_as_pessimist(output_channel, chunk)
    
    return {
        "debate": full_debate,
        "optimist_advice": optimist_advice.strip(),
        "pessimist_advice": pessimist_advice.strip()
    }
