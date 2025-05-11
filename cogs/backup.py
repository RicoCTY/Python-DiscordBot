import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import zipfile
import io
from datetime import datetime

class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_dir = "data/backups"
        os.makedirs(self.backup_dir, exist_ok=True)

    async def create_backup(self, guild):
        backup_data = {
            "metadata": {
                "guild_id": guild.id,
                "guild_name": guild.name,
                "created_at": datetime.utcnow().isoformat(),
                "created_by": self.bot.user.name
            },
            "roles": [],
            "channels": [],
            "categories": [],
            "settings": {
                "name": guild.name,
                "icon": str(guild.icon.url) if guild.icon else None,
                "afk_channel": guild.afk_channel.name if guild.afk_channel else None,
                "afk_timeout": guild.afk_timeout,
                "verification_level": str(guild.verification_level),
                "default_notifications": str(guild.default_notifications),
                "explicit_content_filter": str(guild.explicit_content_filter),
                "system_channel": guild.system_channel.name if guild.system_channel else None,
                "system_channel_flags": guild.system_channel_flags.value if guild.system_channel else None
            }
        }

        # Backup roles
        for role in guild.roles:
            if role.is_default():
                continue
                
            backup_data["roles"].append({
                "name": role.name,
                "color": role.color.value,
                "hoist": role.hoist,
                "position": role.position,
                "permissions": role.permissions.value,
                "mentionable": role.mentionable
            })

        # Backup categories
        for category in guild.categories:
            backup_data["categories"].append({
                "name": category.name,
                "position": category.position,
                "nsfw": category.is_nsfw(),
                "permissions": [
                    {
                        "target": perm[0].name if isinstance(perm[0], discord.Role) else perm[0],
                        "values": list(perm[1])
                    }
                    for perm in category.overwrites.items()
                ]
            })

        # Backup channels
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                channel_data = {
                    "type": "text",
                    "name": channel.name,
                    "position": channel.position,
                    "category": channel.category.name if channel.category else None,
                    "topic": channel.topic,
                    "slowmode": channel.slowmode_delay,
                    "nsfw": channel.is_nsfw(),
                    "permissions": [
                        {
                            "target": perm[0].name if isinstance(perm[0], discord.Role) else perm[0],
                            "values": list(perm[1])
                        }
                        for perm in channel.overwrites.items()
                    ]
                }
                backup_data["channels"].append(channel_data)
            elif isinstance(channel, discord.VoiceChannel):
                channel_data = {
                    "type": "voice",
                    "name": channel.name,
                    "position": channel.position,
                    "category": channel.category.name if channel.category else None,
                    "bitrate": channel.bitrate,
                    "user_limit": channel.user_limit,
                    "permissions": [
                        {
                            "target": perm[0].name if isinstance(perm[0], discord.Role) else perm[0],
                            "values": list(perm[1])
                        }
                        for perm in channel.overwrites.items()
                    ]
                }
                backup_data["channels"].append(channel_data)

        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("backup.json", json.dumps(backup_data, indent=2))
            
            # Save icon if exists
            if guild.icon:
                icon_data = await guild.icon.read()
                zip_file.writestr("icon.png", icon_data)
        
        zip_buffer.seek(0)
        return zip_buffer

    @app_commands.command(name="create_backup", description="Create a backup of the server")
    @app_commands.default_permissions(administrator=True)
    async def create_backup_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            backup_file = await self.create_backup(interaction.guild)
            timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{interaction.guild.name.replace(' ', '_')}_backup_{timestamp}.zip"
            
            await interaction.followup.send(
                "Here's your server backup:",
                file=discord.File(backup_file, filename=filename),
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"Failed to create backup: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="view_backups", description="List all available backups")
    @app_commands.default_permissions(administrator=True)
    async def view_backups(self, interaction: discord.Interaction):
        if not os.path.exists(self.backup_dir):
            return await interaction.response.send_message(
                "No backups available",
                ephemeral=True
            )
            
        backups = [f for f in os.listdir(self.backup_dir) if f.endswith(".zip")]
        if not backups:
            return await interaction.response.send_message(
                "No backups available",
                ephemeral=True
            )
            
        embed = discord.Embed(
            title="Available Backups",
            description="\n".join(f"• {f}" for f in sorted(backups, reverse=True)[:10]),
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="download_backup", description="Download a specific backup")
    @app_commands.default_permissions(administrator=True)
    async def download_backup(self, interaction: discord.Interaction, filename: str):
        filepath = os.path.join(self.backup_dir, filename)
        if not os.path.exists(filepath):
            return await interaction.response.send_message(
                "Backup file not found",
                ephemeral=True
            )
            
        await interaction.response.send_message(
            "Here's your requested backup:",
            file=discord.File(filepath),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Backup(bot))