# tools.py
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
import asyncio
import random
from discord.ext import tasks

class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthdays_file = "data/birthdays.json"
        self.ensure_files_exist()

    def ensure_files_exist(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.birthdays_file):
            with open(self.birthdays_file, "w") as f:
                json.dump({}, f)

    @app_commands.command(name="poll", description="Create a poll with reaction voting (up to 10 options)")
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        option5: str = None,
        option6: str = None,
        option7: str = None,
        option8: str = None,
        option9: str = None,
        option10: str = None,
    ):
        """Create a poll with automatic reaction voting (supports up to 10 options)"""
        # Collect all non-None options
        options = [opt for opt in [option1, option2, option3, option4, option5, 
                                option6, option7, option8, option9, option10] if opt is not None]
        
        # Verify is between 2-10 options
        if len(options) < 2:
            return await interaction.response.send_message("You need at least 2 options for a poll!", ephemeral=True)
        if len(options) > 10:
            return await interaction.response.send_message("You can't have more than 10 options!", ephemeral=True)

        # Numbered keycap emojis (1️⃣ through 🔟)
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", 
                "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][:len(options)]
        
        # Build the poll description
        description = "\n".join(
            f"{emojis[i]} {option}" 
            for i, option in enumerate(options)
        )
        
        embed = discord.Embed(
            title=question,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Poll created by {interaction.user.display_name}")

        # Send the poll
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        # Add reactions
        for emoji in emojis:
            await message.add_reaction(emoji)

    # Giveaway Command
    @app_commands.command(name="giveaway", description="Create a giveaway with reactions")
    @app_commands.default_permissions(manage_guild=True)
    async def giveaway(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration_minutes: int,
        winners: int = 1,
        channel: discord.TextChannel = None
    ):
        """Create a giveaway with proper reaction handling"""
        if duration_minutes <= 0:
            await interaction.response.send_message(
                "Duration must be a positive number!",
                ephemeral=True
            )
            return
        
        if channel is None:
            channel = interaction.channel
        
        try:
            end_time = discord.utils.utcnow() + timedelta(minutes=duration_minutes)
            
            embed = discord.Embed(
                title=f"🎉 {prize} 🎉",
                description=(
                    f"React with 🎉 to enter!\n"
                    f"Winners: {winners}\n"
                    f"Ends: <t:{int(end_time.timestamp())}:R>"
                ),
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Hosted by {interaction.user.name}")
            
            # Send the initial message
            await interaction.response.send_message(
                f"Giveaway created in {channel.mention}!",
                ephemeral=True
            )
            
            # Send the actual giveaway message
            giveaway_msg = await channel.send("🎉 **GIVEAWAY** 🎉", embed=embed)
            
            # Add the reaction after sending
            await giveaway_msg.add_reaction("🎉")
            
            # Wait for the duration
            await asyncio.sleep(duration_minutes * 60)
            
            # Re-fetch the message to get current reactions
            try:
                giveaway_msg = await channel.fetch_message(giveaway_msg.id)
            except discord.NotFound:
                await channel.send("Giveaway message was deleted!")
                return
            
            # Get valid entries
            reaction = next(
                (r for r in giveaway_msg.reactions 
                 if str(r.emoji) == "🎉"),
                None
            )
            
            if not reaction or reaction.count <= 1:  # Only bot reacted
                await channel.send("No one entered the giveaway!")
                return
            
            users = [user async for user in reaction.users() if not user.bot]
            if not users:
                await channel.send("No valid entries!")
                return
            
            # Select winners
            winner_count = min(winners, len(users))
            winners_list = random.sample(users, winner_count)
            winner_mentions = ", ".join(winner.mention for winner in winners_list)
            
            # Announce winners
            result_embed = discord.Embed(
                title=f"🎉 {prize} 🎉",
                description=f"Winner(s): {winner_mentions}",
                color=discord.Color.green()
            )
            await channel.send(
                f"🎉 **GIVEAWAY ENDED** 🎉",
                embed=result_embed
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"Error in giveaway: {str(e)}",
                ephemeral=True
            )

    # Birthday commands
    @app_commands.command(name="set_birthday", description="Set your birthday")
    async def set_birthday(self, interaction: discord.Interaction, month: int, day: int):
        if month < 1 or month > 12 or day < 1 or day > 31:
            await interaction.response.send_message("Invalid date. Please use numbers (month: 1-12, day: 1-31).", ephemeral=True)
            return
        
        with open(self.birthdays_file, "r") as f:
            birthdays = json.load(f)
        
        user_id = str(interaction.user.id)
        birthdays[user_id] = f"{month}-{day}"
        
        with open(self.birthdays_file, "w") as f:
            json.dump(birthdays, f)
        
        await interaction.response.send_message(f"Your birthday has been set to {month}/{day}.", ephemeral=True)

    @app_commands.command(name="view_birthdays", description="View all birthdays")
    async def view_birthdays(self, interaction: discord.Interaction):
        with open(self.birthdays_file, "r") as f:
            birthdays = json.load(f)
        
        if not birthdays:
            await interaction.response.send_message("No birthdays have been set yet.", ephemeral=True)
            return
        
        sorted_birthdays = sorted(birthdays.items(), key=lambda x: tuple(map(int, x[1].split("-"))))
        
        embed = discord.Embed(
            title="Birthdays",
            description="Here are all the registered birthdays:",
            color=discord.Color.pink()
        )
        
        for user_id, date in sorted_birthdays:
            month, day = date.split("-")
            member = interaction.guild.get_member(int(user_id))
            if member:
                embed.add_field(name=f"{month}/{day}", value=member.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)

    # Birthday check task
    @tasks.loop(hours=24)
    async def check_birthdays(self):
        today = datetime.now().strftime("%m-%d")
        with open(self.birthdays_file, "r") as f:
            birthdays = json.load(f)
        
        for user_id, date in birthdays.items():
            if date == today:
                for guild in self.bot.guilds:
                    member = guild.get_member(int(user_id))
                    if member:
                        channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
                        if channel:
                            await channel.send(f"🎉 Happy Birthday {member.mention}! 🎉")

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_birthdays.start()

async def setup(bot):
    await bot.add_cog(Tools(bot))