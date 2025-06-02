# reminders.py
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders_file = "data/reminders.json"
        self.ensure_files_exist()
        self.check_reminders.start()

    def ensure_files_exist(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.reminders_file):
            with open(self.reminders_file, "w") as f:
                json.dump({}, f)

    def get_reminders(self):
        with open(self.reminders_file, "r") as f:
            return json.load(f)

    def save_reminders(self, data):
        with open(self.reminders_file, "w") as f:
            json.dump(data, f, indent=4)

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.utcnow().timestamp()
        data = self.get_reminders()
        
        reminders_to_remove = []
        
        for reminder_id, reminder_data in data.items():
            if float(reminder_data["time"]) <= now:
                user = self.bot.get_user(int(reminder_data["user_id"]))
                if user:
                    try:
                        await user.send(
                            f"⏰ Reminder: {reminder_data['message']}\n"
                        )
                    except discord.Forbidden:
                        pass  # User has DMs disabled
                
                reminders_to_remove.append(reminder_id)
        
        if reminders_to_remove:
            for reminder_id in reminders_to_remove:
                del data[reminder_id]
            self.save_reminders(data)

    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(
        time="Time until reminder (e.g., 30s, 1h30m, 30m, 2d)",
        message="Message for the reminder"
    )
    async def remind(
        self,
        interaction: discord.Interaction,
        time: str,
        message: str
    ):
        """Set a reminder with a time (e.g., 30s, 1h30m, 30m, 2d)"""
        try:
            seconds = self.parse_time(time)
            if seconds <= 0:
                return await interaction.response.send_message(
                    "Time must be in the future",
                    ephemeral=True
                )
            
            if len(message) > 500:
                return await interaction.response.send_message(
                    "Message must be 500 characters or less",
                    ephemeral=True
                )
            
            reminder_time = (datetime.utcnow() + timedelta(seconds=seconds)).timestamp()
            created_at = datetime.utcnow().timestamp()
            
            data = self.get_reminders()
            reminder_id = str(int(created_at * 1000))  # Unique ID based on timestamp
            
            data[reminder_id] = {
                "user_id": str(interaction.user.id),
                "message": message,
                "time": str(reminder_time),
                "created_at": str(created_at)
            }
            
            self.save_reminders(data)
            
            await interaction.response.send_message(
                f"Reminder set! I'll remind you in {self.format_seconds(seconds)} about: {message}",
                ephemeral=True
            )
            
        except ValueError as e:
            await interaction.response.send_message(
                f"Invalid time format: {str(e)}. Use combinations like 30s, 1h30m, 30m, 2d, etc.",
                ephemeral=True
            )

    def parse_time(self, time_str):
        """Parse time string like 1h30m into seconds"""
        time_units = {
            's': 1,
            'm': 60,
            'h': 60 * 60,
            'd': 24 * 60 * 60,
            'w': 7 * 24 * 60 * 60
        }
        
        seconds = 0
        current_num = ''
        
        for char in time_str.lower():
            if char.isdigit() or char == '.':
                current_num += char
            elif char in time_units:
                if current_num:
                    seconds += float(current_num) * time_units[char]
                    current_num = ''
                else:
                    raise ValueError("Number missing before time unit")
            else:
                raise ValueError(f"Invalid time unit: '{char}'")
        
        if current_num:  # If there's remaining numbers without unit, assume seconds
            seconds += float(current_num)
        
        if seconds <= 0:
            raise ValueError("Time must be positive")
        
        return seconds

    def format_seconds(self, seconds):
        """Format seconds into human-readable string"""
        intervals = [
            ('w', 604800),
            ('d', 86400),
            ('h', 3600),
            ('m', 60),
            ('s', 1)
        ]
        
        result = []
        for unit, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                result.append(f"{int(value)}{unit}")
        
        return ' '.join(result) if result else "0s"

    @app_commands.command(name="reminders", description="List your active reminders")
    async def list_reminders(self, interaction: discord.Interaction):
        """List all active reminders"""
        data = self.get_reminders()
        user_reminders = [
            r for r in data.values() 
            if r["user_id"] == str(interaction.user.id)
        ]
        
        if not user_reminders:
            return await interaction.response.send_message(
                "You don't have any active reminders.",
                ephemeral=True
            )
        
        embed = discord.Embed(
            title="Your Active Reminders",
            color=discord.Color.blue()
        )
        
        for reminder_id, reminder in data.items():
            if reminder["user_id"] == str(interaction.user.id):
                created_at = datetime.fromtimestamp(float(reminder["created_at"]))
                time_left = float(reminder["time"]) - datetime.utcnow().timestamp()
                embed.add_field(
                    name=f"Reminder ID: {reminder_id}",
                    value=(
                        f"Message: {reminder['message']}\n"
                        f"Created At: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Time Left: {self.format_seconds(time_left)}"
                    ),
                    inline=False
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Reminders(bot))