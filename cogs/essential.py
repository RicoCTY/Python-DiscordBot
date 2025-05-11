import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class Essential(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/config.json"
        self.ensure_config_exists()

    def ensure_config_exists(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.config_file):
            with open(self.config_file, "w") as f:
                json.dump({"welcome_channel": None, "goodbye_channel": None}, f)

    # Basic commands
    @app_commands.command(name="hello", description="Say hello!")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Long time no see, {interaction.user.mention}!")

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        ping_embed = discord.Embed(title="Pong!", description="", color=discord.Color.green())
        ping_embed.set_thumbnail(url=interaction.guild.icon)  
        ping_embed.add_field(name=f"{self.bot.user.name}'s Latency: ", value=f"`{round(self.bot.latency * 1000)}`ms", inline=False)
        ping_embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=ping_embed)

    @app_commands.command(name="shutdown", description="Shutdown the bot")
    @commands.is_owner()
    async def shutdown(self, interaction: discord.Interaction):
        await interaction.response.send_message("Shutting down...", ephemeral=True)
        await self.bot.close()

    # Welcome setup commands
    @app_commands.command(name="setup_welcome", description="Set the welcome channel")
    @app_commands.default_permissions(manage_guild=True)
    async def setup_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        with open(self.config_file, "r") as f:
            config = json.load(f)
        config["welcome_channel"] = channel.id
        with open(self.config_file, "w") as f:
            json.dump(config, f)
        await interaction.response.send_message(f"Welcome channel set to {channel.mention}", ephemeral=True)

    # Goodbye setup commands
    @app_commands.command(name="setup_goodbye", description="Set the goodbye channel")
    @app_commands.default_permissions(manage_guild=True)
    async def setup_goodbye(self, interaction: discord.Interaction, channel: discord.TextChannel):
        with open(self.config_file, "r") as f:
            config = json.load(f)
        config["goodbye_channel"] = channel.id
        with open(self.config_file, "w") as f:
            json.dump(config, f)
        await interaction.response.send_message(f"Goodbye channel set to {channel.mention}", ephemeral=True)

    # Events
    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open(self.config_file, "r") as f:
            config = json.load(f)
        
        if config["welcome_channel"]:
            channel = self.bot.get_channel(config["welcome_channel"])
            if channel:
                await channel.send(f"Welcome {member.mention} to {member.guild.name}!")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        with open(self.config_file, "r") as f:
            config = json.load(f)
        
        if config["goodbye_channel"]:
            channel = self.bot.get_channel(config["goodbye_channel"])
            if channel:
                await channel.send(f"{member.name} has left the server. Goodbye!")

    @shutdown.error
    async def shutdown_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.NotOwner):
            await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Essential(bot))