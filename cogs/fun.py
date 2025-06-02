# fun.py
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    async def eightball(self, interaction: discord.Interaction, question: str):
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.", "Don't count on it.",
            "My reply is no.", "My sources say no.", "Outlook not so good.", "Very doubtful."
        ]
        response = random.choice(responses)
        
        embed = discord.Embed(
            title="Magic 8-Ball",
            description=f"**Question:** {question}\n**Answer:** {response}",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on **{result}**!")

    @app_commands.command(name="roll", description="Roll a dice")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        if sides < 2 or sides > 100:
            return await interaction.response.send_message("Number of sides must be between 2 and 100", ephemeral=True)
        
        result = random.randint(1, sides)
        await interaction.response.send_message(f"🎲 You rolled a **{result}** (1-{sides})")

    @app_commands.command(name="rps", description="Play rock-paper-scissors")
    async def rps(self, interaction: discord.Interaction, choice: str):
        choices = ["rock", "paper", "scissors"]
        if choice.lower() not in choices:
            return await interaction.response.send_message("Please choose rock, paper, or scissors", ephemeral=True)
        
        bot_choice = random.choice(choices)
        user_choice = choice.lower()
        
        if user_choice == bot_choice:
            result = "It's a tie!"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
        else:
            result = "I win!"
        
        await interaction.response.send_message(
            f"**You chose:** {user_choice}\n"
            f"**I chose:** {bot_choice}\n"
            f"**Result:** {result}"
        )

async def setup(bot):
    await bot.add_cog(Fun(bot))