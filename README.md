# Recipe Telegram Bot 🍳

A Telegram bot that helps you manage recipes and generate new ones using AI (OpenAI GPT-4 Mini).

## Features

- 🤖 Generate recipes from ingredients using AI
- 📝 Save your own recipes
- 📚 View, edit, and delete saved recipes
- 📏 All measurements in metric units
- 🏗️ Clean OOP architecture
- 💾 Persistent storage (JSON-based)

## Prerequisites

1. **Telegram Bot Token**: Create a bot via [@BotFather](https://t.me/botfather)
2. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/)

## Project Structure

```
recipe-telegram-bot/
├── main.py              # Main bot application
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
├── vercel.json         # Vercel deployment config
├── api/
│   └── webhook.py      # Webhook handler for serverless
└── recipe_data/        # Local storage directory
```

## Installation & Setup

### Local Development

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

4. Run the bot:
```bash
python main.py
```

### Docker Deployment

```bash
docker-compose up -d
```

## Free Deployment Options

### 1. Replit

1. Create new Python repl
2. Upload all files
3. Add environment variables in Secrets
4. Run `main.py`
5. Use UptimeRobot to keep it alive

### 2. Vercel (Serverless)

1. Fork this repository
2. Connect to Vercel
3. Add environment variables
4. Deploy
5. Set webhook URL in Telegram:
```bash
curl -F "url=https://your-app.vercel.app/api/webhook" \
     https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
```

### 3. Railway

1. Connect GitHub repository
2. Add environment variables
3. Deploy (automatic)

### 4. Render

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python main.py`
5. Add environment variables

### 5. Fly.io

1. Install flyctl
2. Run `fly launch`
3. Set environment variables: `fly secrets set TELEGRAM_BOT_TOKEN=... OPENAI_API_KEY=...`
4. Deploy: `fly deploy`

## Bot Commands

- `/start` - Welcome message
- `/help` - Show help
- `/generate` - Generate recipe from ingredients
- `/add` - Add your own recipe
- `/list` - View all saved recipes

## Architecture

The bot follows OOP principles with clear separation of concerns:

- **Recipe**: Data class for recipe objects
- **StorageInterface**: Abstract interface for storage implementations
- **JSONFileStorage**: JSON-based storage implementation
- **LLMInterface**: Abstract interface for LLM providers
- **OpenAILLM**: OpenAI GPT implementation
- **RecipeBot**: Main bot logic

## Storage

Recipes are stored in JSON files:
- Local: `recipe_data/user_{user_id}.json`
- Serverless: Uses `/tmp` directory

## Customization

### Adding New LLM Providers

Create a new class implementing `LLMInterface`:

```python
class YourLLM(LLMInterface):
    async def generate_recipe(self, ingredients: List[str]) -> str:
        # Your implementation
        pass
```

### Adding Database Storage

Create a new class implementing `StorageInterface`:

```python
class DatabaseStorage(StorageInterface):
    async def save_recipe(self, user_id: int, recipe: Recipe) -> None:
        # Your implementation
        pass
    # ... other methods
```

## Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `OPENAI_API_KEY`: Your OpenAI API key

## License

MIT License