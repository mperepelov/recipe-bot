# Recipe Telegram Bot 🍳

A modular, production-ready Telegram bot that helps you manage recipes and generate new ones using AI (OpenAI GPT-4 Mini).

## Features

- 🤖 Generate recipes from ingredients using AI
- 📝 Save your own recipes
- 📚 View, edit, and delete saved recipes
- 📏 All measurements in metric units
- 🏗️ Clean modular architecture
- 💾 Persistent storage
- 🚀 Production-ready with multiple deployment options

## Project Structure

```
recipe-telegram-bot/
├── src/
│   ├── bot.py              # Main bot class
│   ├── config.py           # Configuration management
│   ├── handlers/           # Command and callback handlers
│   ├── models/             # Data models
│   ├── storage/            # Storage implementations
│   └── llm/                # LLM implementations
├── lambda_function.py      # AWS Lambda handler
├── webhook_server.py       # Webhook server for cloud platforms
├── main.py                 # Local development entry point
└── deployment configs...   # Various deployment configurations
```

## Prerequisites

1. **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/botfather)
2. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/)
3. **Python 3.11+**

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd recipe-telegram-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your tokens
```

## Local Development

Run the bot locally:
```bash
python main.py
```

## Deployment

The bot can be deployed on multiple platforms. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions:

- **AWS Lambda** (Free tier, serverless) ⭐ Recommended
- **Railway** (Simple, $5 free credit)
- **Fly.io** (Generous free tier)
- **Render** (Free with limitations)
- **Google Cloud Run** (Pay-per-use)

## Bot Commands

- `/start` - Welcome message
- `/help` - Show help
- `/generate` - Generate recipe from ingredients
- `/add` - Add your own recipe
- `/list` - View all saved recipes

## Architecture

The bot follows a modular architecture with clear separation of concerns:

### Core Components

- **Bot Class** (`src/bot.py`): Main orchestrator
- **Handlers** (`src/handlers/`): Process user commands and callbacks
- **Storage** (`src/storage/`): Abstract storage interface with JSON implementation
- **LLM** (`src/llm/`): Abstract LLM interface with OpenAI implementation
- **Models** (`src/models/`): Data models (Recipe)
- **Config** (`src/config.py`): Configuration management

### Storage

- Default: JSON file storage
- Can be extended to use databases (PostgreSQL, MongoDB, etc.)
- Serverless deployments should use cloud storage (DynamoDB, Firestore)

### Adding New Features

1. **New LLM Provider:**
   ```python
   class YourLLM(LLMInterface):
       async def generate_recipe(self, ingredients: List[str]) -> str:
           # Implementation
   ```

2. **New Storage Backend:**
   ```python
   class DatabaseStorage(StorageInterface):
       # Implement all abstract methods
   ```

## Environment Variables

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (required)
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `WEBHOOK_URL` - Webhook URL for production (optional)
- `STORAGE_PATH` - Path for storing recipes (default: recipe_data)
- `OPENAI_MODEL` - OpenAI model to use (default: gpt-4o-mini)
- `LOG_LEVEL` - Logging level (default: INFO)
- `ENVIRONMENT` - Environment (development/production)

## Development

### Code Structure

- Each component has its own module
- Interfaces define contracts
- Easy to extend and test
- Type hints throughout

### Testing

```bash
# Run tests (add your test files)
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License

## Support

For issues, questions, or contributions, please open an issue on GitHub.