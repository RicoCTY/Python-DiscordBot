import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional, Union
import threading

import aiohttp
import colorama
from discord import Guild, TextChannel
from discord.ext import commands
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

from config.config import config

# Initialize colorama for Windows support
colorama.init()

class DiscordContextFilter(logging.Filter):
    """Filter to add Discord context to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add Discord context to the log record."""
        record.discord_guild = getattr(record, 'discord_guild', 'N/A')
        record.discord_channel = getattr(record, 'discord_channel', 'N/A')
        record.correlation_id = getattr(record, 'correlation_id', str(uuid.uuid4()))
        return True

class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', str(uuid.uuid4())),
            'discord_guild': getattr(record, 'discord_guild', 'N/A'),
            'discord_channel': getattr(record, 'discord_channel', 'N/A'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

class ColoredFormatter(logging.Formatter):
    """Format log records with colors for console output."""
    
    COLORS = {
        'DEBUG': colorama.Fore.BLUE,
        'INFO': colorama.Fore.GREEN,
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED,
        'CRITICAL': colorama.Fore.RED + colorama.Style.BRIGHT
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        if not record.exc_info:
            level = record.levelname
            color = self.COLORS.get(level, colorama.Fore.WHITE)
            record.levelname = f"{color}{level}{colorama.Style.RESET_ALL}"
        return super().format(record)

class AsyncRotatingFileHandler(RotatingFileHandler):
    """Asynchronous rotating file handler."""
    
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit the record to the file."""
        try:
            with self._lock:
                super().emit(record)
        except Exception:
            self.handleError(record)

class DiscordWebhookHandler(logging.Handler):
    """Handler for sending critical logs to Discord webhook."""
    
    def __init__(self, webhook_url: str, level: int = logging.ERROR):
        super().__init__(level)
        self.webhook_url = webhook_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def setup(self) -> None:
        """Set up the aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit the record to Discord webhook."""
        if not self.session:
            return
        
        asyncio.create_task(self._send_to_webhook(record))
    
    async def _send_to_webhook(self, record: logging.LogRecord) -> None:
        """Send the log record to Discord webhook."""
        if not self.session:
            return
        
        try:
            embed = {
                'title': f'🚨 {record.levelname}',
                'description': record.getMessage(),
                'color': 0xFF0000 if record.levelno >= logging.ERROR else 0xFFA500,
                'fields': [
                    {
                        'name': 'Guild',
                        'value': getattr(record, 'discord_guild', 'N/A'),
                        'inline': True
                    },
                    {
                        'name': 'Channel',
                        'value': getattr(record, 'discord_channel', 'N/A'),
                        'inline': True
                    },
                    {
                        'name': 'Correlation ID',
                        'value': getattr(record, 'correlation_id', str(uuid.uuid4())),
                        'inline': True
                    }
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if record.exc_info:
                embed['fields'].append({
                    'name': 'Exception',
                    'value': f'```{self.formatException(record.exc_info)}```',
                    'inline': False
                })
            
            await self.session.post(
                self.webhook_url,
                json={'embeds': [embed]}
            )
        except Exception as e:
            print(f"Error sending to webhook: {e}")

def setup_logger(
    name: str = "discord_bot",
    log_file: Optional[str] = None,
    log_format: str = "text",
    use_colors: bool = True,
    webhook_url: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure the logger with enhanced features.
    
    Args:
        name: The name of the logger
        log_file: Optional path to the log file
        log_format: Log format (text/json)
        use_colors: Whether to use colors in console output
        webhook_url: Optional Discord webhook URL for critical logs
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get the log level from config
    log_level = getattr(logging, config.LOG_LEVEL.upper())
    
    # Create and configure the logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add Discord context filter
    logger.addFilter(DiscordContextFilter())
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    if use_colors:
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
    else:
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = AsyncRotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        if log_format == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        logger.addHandler(file_handler)
    
    # Webhook handler for critical logs
    if webhook_url:
        webhook_handler = DiscordWebhookHandler(webhook_url)
        webhook_handler.setLevel(logging.ERROR)
        logger.addHandler(webhook_handler)
    
    return logger

# Create a singleton logger instance
logger = setup_logger(
    log_file=config.LOG_FILE,
    log_format=os.getenv("LOG_FORMAT", "text"),
    use_colors=os.getenv("LOG_COLORS", "true").lower() == "true",
    webhook_url=os.getenv("LOG_WEBHOOK")
)

# Health check endpoint
async def health_check() -> Dict[str, Any]:
    """Return health check information."""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'log_level': config.LOG_LEVEL,
        'log_file': config.LOG_FILE,
        'log_format': os.getenv("LOG_FORMAT", "text")
    } 