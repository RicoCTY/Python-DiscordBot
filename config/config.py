# config.py
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration class for the Discord bot
class Config:
    # Bot Configuration
    TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    PREFIX: str = os.getenv("COMMAND_PREFIX", "/")
    OWNER_IDS: list = [int(id) for id in os.getenv("OWNER_IDS", "").split(",") if id]
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bot.db")
    
    # Music Configuration
    MAX_PLAYLIST_SIZE: int = int(os.getenv("MAX_PLAYLIST_SIZE", "50"))
    MAX_SONG_LENGTH: int = int(os.getenv("MAX_SONG_LENGTH", "3600"))  # 1 hour in seconds
    
    # Moderation Configuration
    DEFAULT_MUTE_DURATION: int = int(os.getenv("DEFAULT_MUTE_DURATION", "300"))  # 5 minutes
    MAX_WARNINGS: int = int(os.getenv("MAX_WARNINGS", "3"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "bot.log")
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        # Get all configuration values as a dictionary
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith("_") and isinstance(value, (str, int, list, dict, bool))
        }
    
    @classmethod
    def validate(cls) -> bool:
        #Validate the configuration
        if not cls.TOKEN:
            raise ValueError("Discord token is required")
        return True

# Create a singleton instance
config = Config() 