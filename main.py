import discord
import os, asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv
from itertools import cycle

# load environment variables from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix = "/", intents = discord.Intents.all())

bot_statuses = cycle(["with fire", "Work in Process..."])

@tasks.loop(seconds = 30)
async def change_bot_status():
    await bot.change_presence(activity = discord.Game(next(bot_statuses)))

@bot.event
async def on_ready():
    print("bot is online")
    change_bot_status.start()
    try:
        slash = await bot.tree.sync()
        print(f"Synced {len(slash)} commands")
    except Exception as e:
        print("An error with syncing application commands has occurred: ", e)

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded {filename}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")

async def main():
    async with bot:
        await load()
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())