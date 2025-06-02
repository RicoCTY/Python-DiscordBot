# aiChat.py
import os
import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import requests
import json

load_dotenv()

class AiChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('HUGGINGFACE_TOKEN')}",
            "Content-Type": "application/json"
        }
        self.model_ready = False

    async def cog_load(self):
        print(f"{self.__class__.__name__} loaded!")
        # Check if model is ready
        await self.check_model_status()

    async def cog_unload(self):
        print(f"{self.__class__.__name__} unloaded!")

    async def check_model_status(self):
        """Check if the model is ready to accept requests"""
        try:
            response = requests.get(
                self.api_url,
                headers={"Authorization": f"Bearer {os.getenv('HUGGINGFACE_TOKEN')}"},
                timeout=10
            )
            self.model_ready = response.status_code == 200
        except requests.exceptions.RequestException:
            self.model_ready = False

    async def query_with_retry(self, payload, max_retries=3, initial_delay=5):
        """Query with retry for model loading cases"""
        for attempt in range(max_retries):
            try:
                data = json.dumps(payload)
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 503:
                    retry_after = int(response.headers.get('Retry-After', initial_delay * (attempt + 1)))
                    print(f"Model loading, retrying in {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    return {"error": response.text, "status_code": response.status_code}
                    
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return {"error": str(e)}
                await asyncio.sleep(initial_delay * (attempt + 1))
                
        return {"error": "Max retries reached"}

    @app_commands.command(
        name="aichat",
        description="Chat with Zephyr-7B AI (free model)"
    )
    @app_commands.describe(
        message="Your message to the AI",
        max_length="Maximum length of the response (default: 200)",
        temperature="Sampling temperature (default: 0.7)",
        top_p="Top-p sampling (default: 0.9)"
    )
    async def chat_command(
        self,
        interaction: discord.Interaction,
        message: str,
        max_length: int = 200, 
        temperature: float = 0.7,
        top_p: float = 0.9
    ):
        await interaction.response.defer(thinking=True)
        
        if not self.model_ready:
            await interaction.followup.send("⚠️ The AI model is still loading. Please try again in a minute.")
            return
            
        try:
            # Format prompt for Zephyr model
            prompt = f"<|user|>\n{message}</s>\n<|assistant|>"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_length,
                    "temperature": temperature,
                    "top_p": top_p,
                    "do_sample": True
                }
            }
            
            response = await self.query_with_retry(payload)
            
            if isinstance(response, dict) and 'error' in response:
                error_msg = response['error']
                if 'status_code' in response:
                    if response['status_code'] == 404:
                        error_msg = "The AI model endpoint was not found. Please contact the bot owner."
                    elif response['status_code'] == 401:
                        error_msg = "Invalid API key. Please contact the bot owner."
                
                await interaction.followup.send(f"⚠️ {error_msg}")
                return
                
            if not isinstance(response, list) or len(response) == 0:
                await interaction.followup.send("⚠️ Unexpected response format from API")
                return
                
            if 'generated_text' not in response[0]:
                await interaction.followup.send("⚠️ No generated text in API response")
                return
                
            ai_response = response[0]['generated_text'].strip()
            
            # Remove the prompt from the response if it's included
            if prompt in ai_response:
                ai_response = ai_response.replace(prompt, "").strip()
            
            # Handle Discord's character limit
            if len(ai_response) > 2000:
                chunks = [ai_response[i:i+2000] for i in range(0, len(ai_response), 2000)]
                await interaction.followup.send(chunks[0])
                for chunk in chunks[1:]:
                    await interaction.channel.send(chunk)
            else:
                await interaction.followup.send(ai_response)
                
        except Exception as e:
            await interaction.followup.send(f"⚠️ An unexpected error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(AiChat(bot))