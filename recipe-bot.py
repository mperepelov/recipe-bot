import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Try to load from .env file if it exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available in Replit by default
    pass

import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_INGREDIENTS, WAITING_FOR_RECIPE_NAME, WAITING_FOR_RECIPE_CONTENT, EDITING_RECIPE = range(4)

# Keep Replit alive
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running! 🤖"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

@dataclass
class Recipe:
    """Data class representing a recipe"""
    id: str
    name: str
    content: str
    created_at: str
    updated_at: str
    is_ai_generated: bool = False
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Recipe':
        return cls(**data)

class StorageInterface(ABC):
    """Abstract interface for storage implementations"""
    
    @abstractmethod
    async def save_recipe(self, user_id: int, recipe: Recipe) -> None:
        pass
    
    @abstractmethod
    async def get_recipes(self, user_id: int) -> List[Recipe]:
        pass
    
    @abstractmethod
    async def get_recipe(self, user_id: int, recipe_id: str) -> Optional[Recipe]:
        pass
    
    @abstractmethod
    async def update_recipe(self, user_id: int, recipe: Recipe) -> None:
        pass
    
    @abstractmethod
    async def delete_recipe(self, user_id: int, recipe_id: str) -> None:
        pass

class JSONFileStorage(StorageInterface):
    """JSON file-based storage implementation"""
    
    def __init__(self, storage_path: str = "recipe_data"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def _get_user_file(self, user_id: int) -> str:
        return os.path.join(self.storage_path, f"user_{user_id}.json")
    
    async def save_recipe(self, user_id: int, recipe: Recipe) -> None:
        file_path = self._get_user_file(user_id)
        recipes = await self.get_recipes(user_id)
        recipes.append(recipe)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in recipes], f, ensure_ascii=False, indent=2)
    
    async def get_recipes(self, user_id: int) -> List[Recipe]:
        file_path = self._get_user_file(user_id)
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Recipe.from_dict(r) for r in data]
        except Exception as e:
            logger.error(f"Error reading recipes for user {user_id}: {e}")
            return []
    
    async def get_recipe(self, user_id: int, recipe_id: str) -> Optional[Recipe]:
        recipes = await self.get_recipes(user_id)
        for recipe in recipes:
            if recipe.id == recipe_id:
                return recipe
        return None
    
    async def update_recipe(self, user_id: int, recipe: Recipe) -> None:
        recipes = await self.get_recipes(user_id)
        for i, r in enumerate(recipes):
            if r.id == recipe.id:
                recipes[i] = recipe
                break
        
        file_path = self._get_user_file(user_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in recipes], f, ensure_ascii=False, indent=2)
    
    async def delete_recipe(self, user_id: int, recipe_id: str) -> None:
        recipes = await self.get_recipes(user_id)
        recipes = [r for r in recipes if r.id != recipe_id]
        
        file_path = self._get_user_file(user_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in recipes], f, ensure_ascii=False, indent=2)

class LLMInterface(ABC):
    """Abstract interface for LLM implementations"""
    
    @abstractmethod
    async def generate_recipe(self, ingredients: List[str]) -> str:
        pass

class OpenAILLM(LLMInterface):
    """OpenAI GPT implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        try:
            # Try the newer OpenAI client initialization
            self.client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            # Fallback for compatibility issues
            openai.api_key = api_key
            self.client = None
        self.model = model
    
    async def generate_recipe(self, ingredients: List[str]) -> str:
        prompt = f"""You are a professional chef. Create a detailed recipe using ONLY these ingredients: {', '.join(ingredients)}.

IMPORTANT RULES:
1. Use ONLY metric measurements (grams, milliliters, liters, etc.)
2. Include prep time and cooking time
3. Provide step-by-step instructions
4. Suggest serving size
5. Keep the recipe practical and achievable for home cooking
6. If the ingredients don't make sense together, suggest the closest viable recipe

Format the recipe clearly with sections for:
- Recipe Name
- Prep Time & Cook Time
- Servings
- Ingredients (with metric measurements)
- Instructions (numbered steps)
- Optional: Tips or variations"""

        try:
            if self.client:
                # Use the new client interface
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful cooking assistant that only provides recipes and cooking-related advice. Always use metric measurements."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            else:
                # Fallback to older API style
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful cooking assistant that only provides recipes and cooking-related advice. Always use metric measurements."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating recipe: {e}")
            return "Sorry, I couldn't generate a recipe at this time. Please try again later."

class RecipeBot:
    """Main bot class managing all operations"""
    
    def __init__(self, storage: StorageInterface, llm: LLMInterface):
        self.storage = storage
        self.llm = llm
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    async def generate_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the recipe generation process"""
        await update.message.reply_text(
            "🥘 Let's create a recipe!\n\n"
            "Please list the ingredients you have, separated by commas.\n"
            "Example: chicken breast, tomatoes, garlic, olive oil, pasta"
        )
        return WAITING_FOR_INGREDIENTS
    
    async def generate_recipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Generate recipe from ingredients"""
        ingredients = [i.strip() for i in update.message.text.split(',')]
        
        await update.message.reply_text("👨‍🍳 Creating your recipe... This may take a moment.")
        
        # Generate recipe using LLM
        recipe_content = await self.llm.generate_recipe(ingredients)
        
        # Extract recipe name from content (first line usually)
        lines = recipe_content.strip().split('\n')
        recipe_name = lines[0].strip() if lines else "Generated Recipe"
        
        # Create recipe object
        recipe = Recipe(
            id=f"recipe_{update.effective_user.id}_{datetime.now().timestamp()}",
            name=recipe_name,
            content=recipe_content,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_ai_generated=True
        )
        
        # Save recipe
        await self.storage.save_recipe(update.effective_user.id, recipe)
        
        # Send recipe to user
        await update.message.reply_text(f"✅ Recipe generated and saved!\n\n{recipe_content}")
        
        return ConversationHandler.END
    
    async def add_recipe_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start adding a custom recipe"""
        await update.message.reply_text(
            "📝 Let's save your recipe!\n\n"
            "First, what's the name of your recipe?"
        )
        return WAITING_FOR_RECIPE_NAME
    
    async def add_recipe_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Save recipe name and ask for content"""
        context.user_data['recipe_name'] = update.message.text
        
        await update.message.reply_text(
            "Great! Now please share your recipe.\n\n"
            "Include ingredients (with metric measurements) and instructions.\n"
            "You can format it however you like!"
        )
        return WAITING_FOR_RECIPE_CONTENT
    
    async def add_recipe_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Save the complete recipe"""
        recipe = Recipe(
            id=f"recipe_{update.effective_user.id}_{datetime.now().timestamp()}",
            name=context.user_data['recipe_name'],
            content=update.message.text,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_ai_generated=False
        )
        
        await self.storage.save_recipe(update.effective_user.id, recipe)
        
        await update.message.reply_text(
            f"✅ Recipe '{recipe.name}' has been saved successfully!"
        )
        
        # Clear user data
        context.user_data.clear()
        
        return ConversationHandler.END
    
    async def list_recipes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List all user's recipes"""
        recipes = await self.storage.get_recipes(update.effective_user.id)
        
        if not recipes:
            await update.message.reply_text(
                "📭 You don't have any saved recipes yet.\n"
                "Use /generate or /add to create your first recipe!"
            )
            return
        
        # Create inline keyboard
        keyboard = []
        for recipe in recipes:
            emoji = "🤖" if recipe.is_ai_generated else "👤"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {recipe.name}", 
                    callback_data=f"view_{recipe.id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📚 Your Recipes ({len(recipes)} total):\n\n"
            "🤖 = AI Generated | 👤 = Your Recipe",
            reply_markup=reply_markup
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data.startswith("view_"):
            recipe_id = data.replace("view_", "")
            recipe = await self.storage.get_recipe(user_id, recipe_id)
            
            if recipe:
                keyboard = [
                    [
                        InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{recipe_id}"),
                        InlineKeyboardButton("🗑 Delete", callback_data=f"delete_{recipe_id}")
                    ],
                    [InlineKeyboardButton("« Back to List", callback_data="list")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"📖 {recipe.name}\n\n{recipe.content}\n\n"
                    f"Created: {recipe.created_at[:10]}",
                    reply_markup=reply_markup
                )
        
        elif data.startswith("edit_"):
            recipe_id = data.replace("edit_", "")
            context.user_data['editing_recipe_id'] = recipe_id
            
            await query.edit_message_text(
                "✏️ Please send the updated recipe content.\n"
                "Send /cancel to cancel editing."
            )
            # This would need to be handled in a conversation handler
        
        elif data.startswith("delete_"):
            recipe_id = data.replace("delete_", "")
            await self.storage.delete_recipe(user_id, recipe_id)
            
            await query.edit_message_text("🗑 Recipe deleted successfully!")
            
            # Show updated list
            await self.list_recipes(query, context)
        
        elif data == "list":
            # Refresh the list
            recipes = await self.storage.get_recipes(user_id)
            
            if not recipes:
                await query.edit_message_text(
                    "📭 You don't have any saved recipes yet.\n"
                    "Use /generate or /add to create your first recipe!"
                )
                return
            
            keyboard = []
            for recipe in recipes:
                emoji = "🤖" if recipe.is_ai_generated else "👤"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{emoji} {recipe.name}", 
                        callback_data=f"view_{recipe.id}"
                    )
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📚 Your Recipes ({len(recipes)} total):\n\n"
                "🤖 = AI Generated | 👤 = Your Recipe",
                reply_markup=reply_markup
            )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel any ongoing conversation"""
        await update.message.reply_text("Operation cancelled.")
        context.user_data.clear()
        return ConversationHandler.END

def main():
    """Start the bot"""
    # Get environment variables (Replit Secrets or .env)
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        logger.info("Please add TELEGRAM_BOT_TOKEN to Replit Secrets")
        return
    
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not found in environment variables!")
        logger.info("Please add OPENAI_API_KEY to Replit Secrets")
        return
    
    logger.info("Starting Recipe Bot...")
    
    # Keep Replit alive
    keep_alive()
    
    # Initialize components
    storage = JSONFileStorage()
    llm = OpenAILLM(OPENAI_API_KEY)
    bot = RecipeBot(storage, llm)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("list", bot.list_recipes))
    
    # Conversation handler for generating recipes
    generate_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("generate", bot.generate_start)],
        states={
            WAITING_FOR_INGREDIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.generate_recipe)
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )
    
    # Conversation handler for adding recipes
    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", bot.add_recipe_start)],
        states={
            WAITING_FOR_RECIPE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.add_recipe_name)
            ],
            WAITING_FOR_RECIPE_CONTENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.add_recipe_content)
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
    )
    
    application.add_handler(generate_conv_handler)
    application.add_handler(add_conv_handler)
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    logger.info("Bot is running! 🤖")
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()