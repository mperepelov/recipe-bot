import os
import json
from telegram import Update
from telegram.ext import Application
from main import RecipeBot, JSONFileStorage, OpenAILLM

# Initialize components
storage = JSONFileStorage("/tmp/recipe_data")  # Use /tmp for serverless
llm = OpenAILLM(os.getenv("OPENAI_API_KEY"))
bot = RecipeBot(storage, llm)

# Create application
application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

# Add all handlers here (same as in main.py)
# ... (copy handler setup from main.py)

async def handle_webhook(request):
    """Handle incoming webhook requests"""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return {"statusCode": 200}
    return {"statusCode": 405}

# For Vercel
def handler(request, context):
    """Vercel serverless function handler"""
    import asyncio
    return asyncio.run(handle_webhook(request))