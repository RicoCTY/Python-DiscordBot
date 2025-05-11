import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp
import os

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            # Take first item from a playlist
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    @app_commands.command(name="play", description="Play a song from YouTube")
    @app_commands.describe(query="The song or URL to play")
    async def play(self, interaction: discord.Interaction, query: str):
        """Plays a song from YouTube"""
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message(
                "You need to be in a voice channel to use this command!",
                ephemeral=True
            )
        
        await interaction.response.defer()
        
        voice_client = interaction.guild.voice_client
        if not voice_client:
            voice_client = await interaction.user.voice.channel.connect()
        
        try:
            # Get song info
            player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
            
            # Add to queue
            queue = self.get_queue(interaction.guild.id)
            queue.append(player)
            
            if not voice_client.is_playing():
                self.play_next(interaction.guild.id, voice_client)
                await interaction.followup.send(f"Now playing: **{player.title}**")
            else:
                await interaction.followup.send(f"Added to queue: **{player.title}**")
                
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    def play_next(self, guild_id, voice_client):
        queue = self.get_queue(guild_id)
        if queue:
            player = queue.pop(0)
            voice_client.play(
                player,
                after=lambda e: self.play_next(guild_id, voice_client) if not e else None
            )

    @app_commands.command(name="stop", description="Stop the music and clear the queue")
    async def stop(self, interaction: discord.Interaction):
        """Stops and disconnects the bot from voice"""
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            return await interaction.response.send_message(
                "I'm not connected to any voice channel!",
                ephemeral=True
            )
        
        if interaction.guild.id in self.queues:
            self.queues[interaction.guild.id] = []
        
        await voice_client.disconnect()
        await interaction.response.send_message("Stopped the music and left the voice channel")

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        """Skip the current song"""
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            return await interaction.response.send_message(
                "No music is currently playing!",
                ephemeral=True
            )
        
        voice_client.stop()
        await interaction.response.send_message("Skipped the current song")

    @app_commands.command(name="queue", description="Show the current queue")
    async def show_queue(self, interaction: discord.Interaction):
        """Show the current music queue"""
        queue = self.get_queue(interaction.guild.id)
        if not queue:
            return await interaction.response.send_message(
                "The queue is empty!",
                ephemeral=True
            )
        
        embed = discord.Embed(
            title="Music Queue",
            description="\n".join(
                f"{idx + 1}. {song.title}" 
                for idx, song in enumerate(queue[:10])  # Show first 10
            ),
            color=discord.Color.blurple()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        """Pause the current song"""
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            return await interaction.response.send_message(
                "No music is currently playing!",
                ephemeral=True
            )
        
        voice_client.pause()
        await interaction.response.send_message("Paused the music")

    @app_commands.command(name="resume", description="Resume the current song")
    async def resume(self, interaction: discord.Interaction):
        """Resume the current song"""
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_paused():
            return await interaction.response.send_message(
                "The music is not paused!",
                ephemeral=True
            )
        
        voice_client.resume()
        await interaction.response.send_message("Resumed the music")

    @app_commands.command(name="volume", description="Change the volume (0-100)")
    @app_commands.describe(volume="Volume level (0-100)")
    async def volume(self, interaction: discord.Interaction, volume: int):
        """Change the player volume"""
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            return await interaction.response.send_message(
                "No music is currently playing!",
                ephemeral=True
            )
        
        if volume < 0 or volume > 100:
            return await interaction.response.send_message(
                "Volume must be between 0 and 100",
                ephemeral=True
            )
        
        voice_client.source.volume = volume / 100
        await interaction.response.send_message(f"Changed volume to {volume}%")

async def setup(bot):
    await bot.add_cog(Music(bot))