# automod.py
import discord
from discord import app_commands
from discord.ext import commands, tasks
import re
import json
import os
from datetime import datetime, timedelta

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/automod.json"
        self.ensure_files_exist()
        self.spam_cooldown = commands.CooldownMapping.from_cooldown(5, 10, commands.BucketType.user)
        self.last_message = {}

    def ensure_files_exist(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.config_file):
            default_config = {
                "banned_words": [],
                "max_mentions": 5,
                "anti_spam": True,
                "anti_invite": True,
                "log_channel": None
            }
            with open(self.config_file, "w") as f:
                json.dump(default_config, f)

    def get_config(self, guild_id):
        with open(self.config_file, "r") as f:
            config = json.load(f)
        return config.get(str(guild_id), {})

    def save_config(self, guild_id, config):
        with open(self.config_file, "r+") as f:
            all_config = json.load(f)
            all_config[str(guild_id)] = config
            f.seek(0)
            json.dump(all_config, f)
            f.truncate()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        config = self.get_config(message.guild.id)
        if not config:
            return

        # Anti-spam
        if config.get("anti_spam", True):
            bucket = self.spam_cooldown.get_bucket(message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                await message.delete()
                try:
                    await message.author.send("Please don't spam messages!")
                except discord.Forbidden:
                    pass
                return

        # Banned words
        banned_words = config.get("banned_words", [])
        if banned_words:
            content_lower = message.content.lower()
            for word in banned_words:
                if word.lower() in content_lower:
                    await message.delete()
                    try:
                        await message.author.send(
                            f"Your message was deleted because it contained a banned word: `{word}`"
                        )
                    except discord.Forbidden:
                        pass
                    await self.log_action(
                        message.guild,
                        f"Deleted message from {message.author.mention} for banned word: `{word}`"
                    )
                    return

        # Excessive mentions
        max_mentions = config.get("max_mentions", 5)
        if len(message.mentions) > max_mentions:
            await message.delete()
            try:
                await message.author.send(
                    f"Your message was deleted because it contained more than {max_mentions} mentions"
                )
            except discord.Forbidden:
                pass
            await self.log_action(
                message.guild,
                f"Deleted message from {message.author.mention} for excessive mentions"
            )
            return

        # Discord invites
        if config.get("anti_invite", True):
            invite_regex = re.compile(
                r"(discord\.gg|discord\.com/invite|discordapp\.com/invite)/[a-zA-Z0-9]+"
            )
            if invite_regex.search(message.content):
                await message.delete()
                try:
                    await message.author.send(
                        "Your message was deleted because it contained a Discord invite link"
                    )
                except discord.Forbidden:
                    pass
                await self.log_action(
                    message.guild,
                    f"Deleted message from {message.author.mention} for Discord invite"
                )
                return

    async def log_action(self, guild, message):
        config = self.get_config(guild.id)
        if not config or not config.get("log_channel"):
            return

        channel = guild.get_channel(config["log_channel"])
        if channel:
            embed = discord.Embed(
                title="AutoMod Action",
                description=message,
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            await channel.send(embed=embed)

    @app_commands.command(name="automod_setup", description="Configure AutoMod settings")
    @app_commands.default_permissions(manage_guild=True)
    async def automod_setup(
        self,
        interaction: discord.Interaction,
        log_channel: discord.TextChannel = None,
        max_mentions: int = None,
        anti_spam: bool = None,
        anti_invite: bool = None
    ):
        config = self.get_config(interaction.guild.id) or {}
        
        if log_channel:
            config["log_channel"] = log_channel.id
        if max_mentions:
            config["max_mentions"] = max_mentions
        if anti_spam is not None:
            config["anti_spam"] = anti_spam
        if anti_invite is not None:
            config["anti_invite"] = anti_invite
        
        self.save_config(interaction.guild.id, config)
        
        embed = discord.Embed(
            title="AutoMod Configuration Updated",
            color=discord.Color.green()
        )
        if log_channel:
            embed.add_field(name="Log Channel", value=log_channel.mention)
        if max_mentions:
            embed.add_field(name="Max Mentions", value=max_mentions)
        if anti_spam is not None:
            embed.add_field(name="Anti-Spam", value="Enabled" if anti_spam else "Disabled")
        if anti_invite is not None:
            embed.add_field(name="Anti-Invite", value="Enabled" if anti_invite else "Disabled")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="add_banned_word", description="Add a word to the banned words list")
    @app_commands.default_permissions(manage_guild=True)
    async def add_banned_word(self, interaction: discord.Interaction, word: str):
        config = self.get_config(interaction.guild.id) or {}
        banned_words = config.get("banned_words", [])
        
        if word in banned_words:
            await interaction.response.send_message(
                "This word is already banned",
                ephemeral=True
            )
            return
        
        banned_words.append(word)
        config["banned_words"] = banned_words
        self.save_config(interaction.guild.id, config)
        
        await interaction.response.send_message(
            f"Added `{word}` to the banned words list",
            ephemeral=True
        )

    @app_commands.command(name="remove_banned_word", description="Remove a word from the banned words list")
    @app_commands.default_permissions(manage_guild=True)
    async def remove_banned_word(self, interaction: discord.Interaction, word: str):
        config = self.get_config(interaction.guild.id) or {}
        banned_words = config.get("banned_words", [])
        
        if word not in banned_words:
            await interaction.response.send_message(
                "This word isn't in the banned words list",
                ephemeral=True
            )
            return
        
        banned_words.remove(word)
        config["banned_words"] = banned_words
        self.save_config(interaction.guild.id, config)
        
        await interaction.response.send_message(
            f"Removed `{word}` from the banned words list",
            ephemeral=True
        )

    @app_commands.command(name="list_banned_words", description="List all banned words")
    @app_commands.default_permissions(manage_guild=True)
    async def list_banned_words(self, interaction: discord.Interaction):
        config = self.get_config(interaction.guild.id) or {}
        banned_words = config.get("banned_words", [])
        
        if not banned_words:
            await interaction.response.send_message(
                "No words are currently banned",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="Banned Words",
            description="\n".join(f"• `{word}`" for word in banned_words),
            color=discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))