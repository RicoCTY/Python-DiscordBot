import discord
import asyncio
import os
from discord.ext import commands, tasks
from itertools import cycle

from config.config import config
from utils.logger import logger

# Initialize bot with configuration
intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    owner_ids=config.OWNER_IDS
)

# Status rotation
bot_statuses = cycle([
    "with fire",
    "Work in Process...",
    f"Prefix: {config.PREFIX}",
])

@tasks.loop(seconds=30)
async def change_bot_status():
    """Change the bot's status every 30 seconds."""
    try:
        await bot.change_presence(activity=discord.Game(next(bot_statuses)))
    except Exception as e:
        logger.error(f"Error changing bot status: {e}")

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f"Bot is online as {bot.user.name} (ID: {bot.user.id})")
    change_bot_status.start()
    
    try:
        slash = await bot.tree.sync()
        logger.info(f"Synced {len(slash)} slash commands")
    except Exception as e:
        logger.error(f"Error syncing application commands: {e}")

async def load_extensions():
    """Load all cog extensions."""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info(f"Loaded extension: {filename}")
            except Exception as e:
                logger.error(f"Failed to load extension {filename}: {e}")

async def main():
    """Main function to start the bot."""
    try:
        # Validate configuration
        config.validate()
        
        # Load extensions
        await load_extensions()
        
        # Start the bot
        async with bot:
            await bot.start(config.TOKEN)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())