# libraries
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

# Load the .env file and get the bot discord token
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Initialize debug handler; write debug data in 'discord.log'
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Initialize intents
# More documentation can be found here: https://discordpy.readthedocs.io/en/stable/intents.html
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Commands are of this format: '!<command> <params>'
bot = commands.Bot(command_prefix='!', intents=intents)

# For the assign/remove roles, could be made dynamically
secret_role = "test"

# Event handling is done via the '@bot.event' decorator
# Note that discord.py utilizes async/await (i.e asynchronous code)
@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server {member.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "shit" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} - dont use that word!")

    # Must include bot.process_commands(message) to continue handling more messages
    await bot.process_commands(message)

# Command handling through the '@bot.command()' decorator
# ctx -> context (i.e tells who said what, where, etc)
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to {secret_role}")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def remove(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} has had the {secret_role} removed")
    else:
        await ctx.send("Role doesn't exist")

# To access args (i.e !dm <args>), you'll need to include ' *, msg' in the parameters
@bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f"You said {msg}")

@bot.command()
async def reply(ctx):
    await ctx.reply("This is a reply to your message!")

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="New Poll", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")

# '@commands' comes from the commands library
@bot.command()
@commands.has_role(secret_role)
async def secret(ctx):
    await ctx.send("Welcome to the club!")

# Error handling when the user doesn't have the role
@secret.error
async def secret_error(ctx, error):
    # We can be more specific with the type of error
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have permission to do that!")

# Make sure to include this to keep the bot running when executing this python file
bot.run(token, log_handler=handler, log_level=logging.DEBUG)