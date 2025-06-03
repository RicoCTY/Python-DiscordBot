# Python Discord Bot

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://discordpy.readthedocs.io/"><img src="https://img.shields.io/badge/discord.py-2.3.2%2B-blue?logo=discord&logoColor=white" alt="Discord.py"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?logo=opensourceinitiative&logoColor=white" alt="License"></a>
  <a href="https://github.com/RicoCTY/Python-DiscordBot
/stargazers"><img src="https://img.shields.io/github/stars/RicoCTY/Python-DiscordBot?logo=github&color=yellow" alt="Stars"></a>
  <a href="https://github.com/RicoCTY/Python-DiscordBot
/network/members"><img src="https://img.shields.io/github/forks/RicoCTY/Python-DiscordBot?logo=github&color=blue" alt="Forks"></a>
</p>

<p align="center">
  <img width="180" alt="Bot logo" src="https://github.com/user-attachments/assets/895cd213-4f3d-4142-93f9-7fca08782a50"/>
</p>



## 🎯 Overview

A feature-rich Discord bot that combines AI chat capabilities with music playback features. Perfect for enhancing your Discord server with intelligent conversations, entertainment, and utility functions.

### 🌟 Key Features

- 🤖 **AI Chat**: Engage in natural conversations with context awareness
- 🎵 **Music Player**: High-quality music playback with queue management
- 🎮 **Fun Games**: Interactive games like 8ball, rock-paper-scissors, and more
- 🛡️ **Auto-Moderation**: Keep your server safe with customizable moderation tools
- 🎉 **Giveaways**: Create and manage giveaways with ease
- 📅 **Birthday System**: Never miss a member's birthday celebration
- 🎤 **Text-to-Speech**: Convert text messages to voice

## 🚀 Installation Guide

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token
- HuggingFace Access Token
- FFmpeg (for music features)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/RicoCTY/Python-DiscordBot.git
cd Python-DiscordBot
```

### Step 2: Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the root directory with the following variables:
```env
# Discord Bot Configuration
DISCORD_TOKEN=your_bot_token_here

# AI Model Configuration
HUGGINGFACE_TOKEN=your_huggingFace_token
```

### Step 5: Run the Bot
#### Windows:
```bash
python main.py
```

#### macOS/Linux:
```bash
python3 main.py
```

## 🛠️ Development

### Project Structure
```
discord_bot/
├── cogs/           # Command modules
│   ├── fun.py      # Fun commands
│   ├── music.py    # Music features
│   ├── tools.py    # Utility commands
│   └── ...
├── config/         # Configuration files
├── utils/          # Helper functions
├── data/           # Data storage
└── main.py         # Bot entry point
```

## 📋 Command List

### 🎮 Fun Commands
| Command | Description | Usage |
|---------|-------------|--------|
| `/8ball` | Ask the magic 8-ball a question | `/8ball Will I win the lottery?` |
| `/coinflip` | Flip a coin | `/coinflip` |
| `/roll` | Roll a dice | `/roll 20` |
| `/rps` | Play rock-paper-scissors | `/rps rock` |

### 🛠️ Utility Commands
| Command | Description | Usage |
|---------|-------------|--------|
| `/hello` | Get a friendly greeting | `/hello` |
| `/ping` | Check the bot's latency | `/ping` |
| `/poll` | Create a poll with up to 10 options | `/poll "Best season?" "Summer" "Winter" "Spring" "Fall"` |
| `/giveaway` | Create a giveaway | `/giveaway "PS5" 60 1` |
| `/set_birthday` | Set your birthday | `/set_birthday 12 25` |
| `/view_birthdays` | View all registered birthdays | `/view_birthdays` |
| `/tts` | Convert text to speech | `/tts Hello everyone!` |
| `/remind` | Set a reminder | `/remind "Submit report" 2h` |
| `/reminders` | View your active reminders | `/reminders` |

### 🎵 Music Commands
| Command | Description | Usage |
|---------|-------------|--------|
| `/play` | Play a song | `/play https://youtube.com/...` |
| `/skip` | Skip the current song | `/skip` |
| `/stop` | Stop playback and clear queue | `/stop` |
| `/pause` | Pause the current song | `/pause` |
| `/volume` | Adjust playback volume | `/volume 50` |
| `/queue` | View the current music queue | `/queue` |

### 👤 Information Commands
| Command | Description | Usage |
|---------|-------------|--------|
| `/userinfo` | Get detailed user information | `/userinfo @user` |
| `/avatar` | Get a user's avatar | `/avatar @user` |

### ⚙️ Admin Commands
| Command | Description | Usage |
|---------|-------------|--------|
| `/shutdown` | Shutdown the bot (owner only) | `/shutdown` |
| `/setup_welcome` | Set the welcome channel | `/setup_welcome #welcome-channel` |
| `/setup_goodbye` | Set the goodbye channel | `/setup_goodbye #goodbye-channel` |
| `/role_menu` | Create a reaction role menu | `/role_menu "Game Roles" "Select your games"` |
| `/automod_setup` | Configure AutoMod settings | `/automod_setup` |
| `/add_banned_word` | Add a banned word | `/add_banned_word example` |
| `/remove_banned_word` | Remove a banned word | `/remove_banned_word example` |
| `/list_banned_words` | View all banned words | `/list_banned_words` |
| `/download_backup` | Download server backup | `/download_backup` |
| `/create_backup` | Create server backup | `/create_backup` |
| `/edit_menu_description` | Edit role menu description | `/edit_menu_description "New description"` |
| `/edit_menu_title` | Edit role menu title | `/edit_menu_title "New title"` |
| `/view_backup` | View available backups | `/view_backup` |
| `/aiChat` | Chat with AI | `/aiChat What's the meaning of life?` |


## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/NewFeature`)
3. Commit your changes (`git commit -m 'Add some New Feature'`)
4. Push to the branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💬 Support

If you encounter any issues or have questions, please:
1. Check the [Issues](https://github.com/RicoCTY/Python-DiscordBot/issues) page
2. Create a new issue if your problem isn't already listed

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - The Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- All contributors and users of this bot 
