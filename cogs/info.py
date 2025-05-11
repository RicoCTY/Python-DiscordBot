import discord
from discord import app_commands
from discord.ext import commands
import datetime

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="serverinfo", description="Get information about the server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"{guild.name} Info",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        embed.add_field(name="Owner", value=guild.owner.mention)
        embed.add_field(name="Created", value=guild.created_at.strftime("%b %d, %Y"))
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Channels", value=f"{len(guild.text_channels)} Text | {len(guild.voice_channels)} Voice")
        embed.add_field(name="Boosts", value=guild.premium_subscription_count)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Get information about a user")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        
        embed = discord.Embed(
            title=f"{target.name}'s Info",
            color=target.color
        )
        embed.set_thumbnail(url=target.avatar.url if target.avatar else None)
        
        embed.add_field(name="ID", value=target.id)
        embed.add_field(name="Nickname", value=target.nick or "None")
        embed.add_field(name="Account Created", value=target.created_at.strftime("%b %d, %Y"))
        embed.add_field(name="Joined Server", value=target.joined_at.strftime("%b %d, %Y"))
        
        roles = [role.mention for role in target.roles if role.name != "@everyone"]
        embed.add_field(
            name="Roles",
            value=", ".join(roles) if roles else "No roles",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get a user's avatar")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        embed = discord.Embed(title=f"{target.name}'s Avatar", color=target.color)
        embed.set_image(url=target.avatar.url if target.avatar else None)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))