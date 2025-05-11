import discord
from discord.ext import commands
from discord import app_commands

class Essential(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Basic commands
    @app_commands.command(name="hello", description="Say hello!")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Long time no see, {interaction.user.mention}!")

    # Ping command
    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        ping_embed = discord.Embed(title="Pong!", description="", color=discord.Color.green())
        ping_embed.set_thumbnail(url=interaction.guild.icon)  
        ping_embed.add_field(name=f"{self.bot.user.name}'s Latency: ", value=f"`{round(self.bot.latency * 1000)}`ms", inline=False)
        ping_embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=ping_embed)

    # Shutdown command
    @app_commands.command(name="shutdown", description="Shutdown the bot")
    @commands.is_owner()  # Only allow the bot owner
    async def shutdown(self, interaction: discord.Interaction):
        await interaction.response.send_message("Shutting down...", ephemeral=True)
        await self.bot.close()
    @shutdown.error
    async def shutdown_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.NotOwner):
            await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Essential(bot))