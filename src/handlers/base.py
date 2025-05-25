"""Base handler functionality"""
from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = """👨‍🍳 Welcome to Recipe Bot!

I can help you manage your recipes and generate new ones using AI.

Available commands:
/generate - Generate a recipe from ingredients
/add - Add your own recipe
/list - View all your saved recipes
/help - Show this help message

Let's start cooking! 🍳"""
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """📚 Recipe Bot Commands:

/generate - I'll ask you for ingredients and create a recipe
/add - Save your own recipe
/list - View all your saved recipes
/help - Show this help message

When viewing recipes, you can:
- 👁 View full recipe
- ✏️ Edit recipe
- 🗑 Delete recipe

All measurements are in metric units! 📏"""
    
    await update.message.reply_text(help_text)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel any ongoing conversation"""
    await update.message.reply_text("Operation cancelled.")
    context.user_data.clear()
    from telegram.ext import ConversationHandler
    return ConversationHandler.END