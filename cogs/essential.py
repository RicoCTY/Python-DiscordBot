import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from typing import List

class Essential(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/config.json"
        self.reaction_roles_file = "data/reaction_roles.json"
        self.ensure_files_exist()

    def ensure_files_exist(self):
        os.makedirs("data", exist_ok=True)
        
        # Ensure config file exists
        if not os.path.exists(self.config_file):
            with open(self.config_file, "w") as f:
                json.dump({"welcome_channel": None, "goodbye_channel": None}, f)
        
        # Ensure reaction roles file exists
        if not os.path.exists(self.reaction_roles_file):
            with open(self.reaction_roles_file, "w") as f:
                json.dump({}, f)

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

    # Shutdown command
    @app_commands.command(name="shutdown", description="Shutdown the bot")
    @commands.is_owner()
    async def shutdown(self, interaction: discord.Interaction):
        await interaction.response.send_message("Shutting down...", ephemeral=True)
        await self.bot.close()

    # Welcome/Goodbye setup commands
    @app_commands.command(name="setup_welcome", description="Set the welcome channel")
    @commands.is_owner()
    async def setup_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        with open(self.config_file, "r") as f:
            config = json.load(f)
        config["welcome_channel"] = channel.id
        with open(self.config_file, "w") as f:
            json.dump(config, f)
        await interaction.response.send_message(f"Welcome channel set to {channel.mention}", ephemeral=True)

    @app_commands.command(name="setup_goodbye", description="Set the goodbye channel")
    @commands.is_owner()
    async def setup_goodbye(self, interaction: discord.Interaction, channel: discord.TextChannel):
        with open(self.config_file, "r") as f:
            config = json.load(f)
        config["goodbye_channel"] = channel.id
        with open(self.config_file, "w") as f:
            json.dump(config, f)
        await interaction.response.send_message(f"Goodbye channel set to {channel.mention}", ephemeral=True)

    # Reaction role commands
    @app_commands.command(name="role_menu", description="Create a reaction role menu")
    @commands.is_owner()
    async def role_menu(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str = "React to get roles!",
        channel: discord.TextChannel = None
    ):
        """Create an interactive role selection menu"""
        if channel is None:
            channel = interaction.channel

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Click the reactions below to get roles")

        message = await channel.send(embed=embed)
        
        with open(self.reaction_roles_file, "r") as f:
            config = json.load(f)
        
        config[str(message.id)] = {"roles": {}}
        
        with open(self.reaction_roles_file, "w") as f:
            json.dump(config, f)

        await interaction.response.send_message(
            f"Role menu created in {channel.mention}! Use `/add_role` to add roles to it.",
            ephemeral=True
        )

    # Add role to existing menu
    @app_commands.command(name="add_role", description="Add a role to the role menu")
    @commands.is_owner()
    async def add_role(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role
    ):
        """Add a role to an existing menu"""
        try:
            message = await interaction.channel.fetch_message(int(message_id))
            
            # Update config
            with open(self.reaction_roles_file, "r") as f:
                config = json.load(f)
            
            if message_id not in config:
                await interaction.response.send_message(
                    "This message isn't a role menu. Create one with `/role_menu` first.",
                    ephemeral=True
                )
                return
            
            # Add role mapping
            config[message_id]["roles"][emoji] = role.id
            with open(self.reaction_roles_file, "w") as f:
                json.dump(config, f)
            await message.add_reaction(emoji)
            embed = message.embeds[0]
            original_description = embed.description.split("\n\n")[0]  # Get the part before roles were added
            
            # Build new role list
            role_list = "\n".join(
                f"{e} - <@&{r}>" 
                for e, r in config[message_id]["roles"].items()
            )
            
            # Update embed description with original text and new role list
            embed.description = f"{original_description}\n\n{role_list}"
            await message.edit(embed=embed)
            await interaction.response.send_message(
                f"Added {role.mention} to the menu!",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"Error: {str(e)}",
                ephemeral=True
            )

    # Remove role from existing menu
    @app_commands.command(name="remove_role", description="Remove a role from the role menu")
    @commands.is_owner()
    async def remove_role(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str
    ):
        """Remove a role from an existing menu"""
        try:
            message = await interaction.channel.fetch_message(int(message_id))
            with open(self.reaction_roles_file, "r") as f:
                config = json.load(f)
            
            if message_id not in config:
                await interaction.response.send_message(
                    "This message isn't a role menu.",
                    ephemeral=True
                )
                return
            
            if emoji not in config[message_id]["roles"]:
                await interaction.response.send_message(
                    "This emoji isn't assigned to any role in this menu.",
                    ephemeral=True
                )
                return
            
            # Get the role being removed for the response message
            role_id = config[message_id]["roles"][emoji]
            guild = interaction.guild
            role = guild.get_role(role_id)
            del config[message_id]["roles"][emoji]
            
            with open(self.reaction_roles_file, "w") as f:
                json.dump(config, f)
            await message.clear_reaction(emoji)
            
            # Update the embed
            embed = message.embeds[0]
            original_description = embed.description.split("\n\n")[0]  # Get original text
            
            if config[message_id]["roles"]:
                role_list = "\n".join(
                    f"{e} - <@&{r}>" 
                    for e, r in config[message_id]["roles"].items()
                )
                embed.description = f"{original_description}\n\n{role_list}"
            else:
                embed.description = original_description
            
            await message.edit(embed=embed)
            
            await interaction.response.send_message(
                f"Removed role {role.mention} (emoji: {emoji}) from the menu.",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"Error: {str(e)}",
                ephemeral=True
            )

    # Edit menu title
    @app_commands.command(name="edit_menu_title", description="Edit the title of an existing role menu")
    @commands.is_owner()
    async def edit_menu_title(
        self,
        interaction: discord.Interaction,
        message_id: str,
        new_title: str
    ):
        """Edit the title of an existing role menu"""
        try:
            channel = interaction.channel
            message = await channel.fetch_message(int(message_id))
            
            with open(self.reaction_roles_file, "r") as f:
                config = json.load(f)
            
            if message_id not in config:
                await interaction.response.send_message(
                    "This message isn't a role menu.",
                    ephemeral=True
                )
                return
            
            if not message.embeds:
                await interaction.response.send_message(
                    "This message doesn't have an embed.",
                    ephemeral=True
                )
                return
            
            embed = message.embeds[0]
            embed.title = new_title
            await message.edit(embed=embed)
            
            await interaction.response.send_message(
                "Successfully updated the menu title!",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"Error: {str(e)}",
                ephemeral=True
            )

    # Edit menu description
    @app_commands.command(name="edit_menu_description", description="Edit the description of an existing role menu")
    @commands.is_owner()
    async def edit_menu_description(
        self,
        interaction: discord.Interaction,
        message_id: str,
        new_description: str):
        """Edit the description of an existing role menu"""
        try:
            channel = interaction.channel
            message = await channel.fetch_message(int(message_id))
            
            with open(self.reaction_roles_file, "r") as f:
                config = json.load(f)
            
            if message_id not in config:
                await interaction.response.send_message(
                    "This message isn't a role menu.",
                    ephemeral=True
                )
                return
            
            if not message.embeds:
                await interaction.response.send_message(
                    "This message doesn't have an embed.",
                    ephemeral=True
                )
                return
            
            embed = message.embeds[0]
            # Preserve the role list if it exists
            current_desc = embed.description
            if "\n\n" in current_desc:
                original_part = current_desc.split("\n\n")[0]
                role_list = current_desc.split("\n\n")[1]
                embed.description = f"{new_description}\n\n{role_list}"
            else:
                embed.description = new_description
                
            await message.edit(embed=embed)
            
            await interaction.response.send_message(
                "Successfully updated the menu description!",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"Error: {str(e)}",
                ephemeral=True
            )

    # Event handlers
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
            
        with open(self.reaction_roles_file, "r") as f:
            config = json.load(f)
        
        message_id = str(payload.message_id)
        emoji = str(payload.emoji)
        
        if message_id in config and emoji in config[message_id]["roles"]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(config[message_id]["roles"][emoji])
            member = guild.get_member(payload.user_id)
            
            if role and member:
                try:
                    await member.add_roles(role)
                except discord.Forbidden:
                    pass
                except discord.NotFound:  # Role was deleted
                    # Remove the invalid role from config
                    with open(self.reaction_roles_file, "r") as f:
                        config = json.load(f)
                    if message_id in config and emoji in config[message_id]["roles"]:
                        del config[message_id]["roles"][emoji]
                        with open(self.reaction_roles_file, "w") as f:
                            json.dump(config, f)
                        # Remove the reaction
                        channel = self.bot.get_channel(payload.channel_id)
                        message = await channel.fetch_message(payload.message_id)
                        await message.clear_reaction(payload.emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        with open(self.reaction_roles_file, "r") as f:
            config = json.load(f)
        
        message_id = str(payload.message_id)
        emoji = str(payload.emoji)
        
        if message_id in config and emoji in config[message_id]["roles"]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(config[message_id]["roles"][emoji])
            member = guild.get_member(payload.user_id)
            
            if role and member:
                try:
                    await member.remove_roles(role)
                except (discord.Forbidden, discord.NotFound):
                    pass

    @shutdown.error
    async def shutdown_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.NotOwner):
            await interaction.response.send_message("You don't have permission to use this command", ephemeral=True)
        else:
            await interaction.response.send_message("An error occurred", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Essential(bot))