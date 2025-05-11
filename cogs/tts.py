import os
import edge_tts
import discord
from discord import app_commands
from discord.ext import commands
import asyncio

class TTSCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.inactivity_timers = {}

    VOICE_OPTIONS = {
        "Soft Female - Jenny": "en-US-JennyNeural",
    }

    async def generate_tts(self, text: str, voice: str) -> str:
        """Generate TTS audio from text"""
        temp_file = "temp_tts.mp3"
        try:
            communicate = edge_tts.Communicate(text=text, voice=voice)
            await communicate.save(temp_file)
            
            if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                raise Exception("Generated audio file is empty")
                
            return temp_file
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e

    async def disconnect_after_inactivity(self, guild_id: int):
        """Disconnect after 15 minutes of inactivity"""
        await asyncio.sleep(900)
        
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_connected():
            voice_client = self.voice_clients[guild_id]
            await voice_client.disconnect()
            del self.voice_clients[guild_id]
            if guild_id in self.inactivity_timers:
                del self.inactivity_timers[guild_id]

    @app_commands.command(name="tts", description="Convert text to speech")
    @app_commands.describe(
        text="Text to convert",
        voice="Voice style"
    )
    @app_commands.choices(voice=[
        app_commands.Choice(name=name, value=value)
        for name, value in VOICE_OPTIONS.items()
    ])
    async def tts(self, interaction: discord.Interaction, text: str, 
                 voice: app_commands.Choice[str]):
        temp_file = None
        try:
            if not interaction.user.voice or not interaction.user.voice.channel:
                await interaction.response.send_message(
                    "Please join a voice channel first!",
                    ephemeral=True
                )
                return

            await interaction.response.defer(thinking=True)

            voice_value = voice.value
            temp_file = await self.generate_tts(text, voice_value)
            
            guild_id = interaction.guild.id
            voice_channel = interaction.user.voice.channel
            
            if guild_id in self.voice_clients:
                voice_client = self.voice_clients[guild_id]
                if voice_client.channel != voice_channel:
                    await voice_client.move_to(voice_channel)
            else:
                voice_client = await voice_channel.connect()
                self.voice_clients[guild_id] = voice_client

            if guild_id in self.inactivity_timers:
                self.inactivity_timers[guild_id].cancel()
            
            self.inactivity_timers[guild_id] = asyncio.create_task(
                self.disconnect_after_inactivity(guild_id)
            )

            def after_playing(error):
                if error:
                    print(f"Playback error: {error}")
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)

            audio_source = discord.FFmpegPCMAudio(temp_file)
            voice_client.play(audio_source, after=after_playing)

            await interaction.delete_original_response()
            
        except Exception as e:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            if "No audio was received" not in str(e):
                await interaction.followup.send(
                    f"⚠️ Failed to generate TTS, please try again",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(TTSCommands(bot))