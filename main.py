"""Main entry point for local development"""
import asyncio
import logging
from src.bot import RecipeBot
from src.config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Run the bot"""
    try:
        # Load configuration
        config = Config.from_env()
        
        # Create and start bot
        bot = RecipeBot(config)
        bot.setup_application()
        
        logger.info("Starting Recipe Bot...")
        
        # Start polling
        await bot.start_polling()
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if 'bot' in locals():
            await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())