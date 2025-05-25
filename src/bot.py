"""Main bot class"""
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from .config import Config, ConversationStates
from .handlers.base import start_command, help_command, cancel_command
from .handlers.recipe_handlers import RecipeHandlers
from .storage.json_storage import JSONFileStorage
from .llm.openai_llm import OpenAILLM

logger = logging.getLogger(__name__)

class RecipeBot:
    """Main bot class that sets up handlers and runs the bot"""
    
    def __init__(self, config: Config):
        self.config = config
        self.storage = JSONFileStorage(config.storage_path)
        self.llm = OpenAILLM(config.openai_api_key, config.openai_model)
        self.recipe_handlers = RecipeHandlers(self.storage, self.llm)
        self.application = None
    
    def setup_application(self) -> Application:
        """Set up the bot application with all handlers"""
        self.application = Application.builder().token(self.config.telegram_bot_token).build()
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("list", self.recipe_handlers.list_recipes))
        
        # Conversation handler for generating recipes
        generate_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("generate", self.recipe_handlers.generate_start)],
            states={
                ConversationStates.WAITING_FOR_INGREDIENTS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.recipe_handlers.generate_recipe)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_command)],
        )
        
        # Conversation handler for adding recipes
        add_conv_handler = ConversationHandler(
            entry_points=[CommandHandler("add", self.recipe_handlers.add_recipe_start)],
            states={
                ConversationStates.WAITING_FOR_RECIPE_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.recipe_handlers.add_recipe_name)
                ],
                ConversationStates.WAITING_FOR_RECIPE_CONTENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.recipe_handlers.add_recipe_content)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_command)],
        )
        
        self.application.add_handler(generate_conv_handler)
        self.application.add_handler(add_conv_handler)
        self.application.add_handler(CallbackQueryHandler(self.recipe_handlers.handle_callback))
        
        return self.application
    
    async def start_polling(self):
        """Start the bot in polling mode (for local development)"""
        if not self.application:
            self.setup_application()
        
        logger.info("Starting bot in polling mode...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
    
    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
    
    async def setup_webhook(self, webhook_url: str):
        """Set up webhook for production deployment"""
        if not self.application:
            self.setup_application()
        
        await self.application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")