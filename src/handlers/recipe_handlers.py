"""Recipe-related handlers"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from ..models.recipe import Recipe
from ..storage.interface import StorageInterface
from ..llm.interface import LLMInterface
from ..config import ConversationStates

logger = logging.getLogger(__name__)

class RecipeHandlers:
    """Handles recipe-related commands and callbacks"""
    
    def __init__(self, storage: StorageInterface, llm: LLMInterface):
        self.storage = storage
        self.llm = llm
    
    async def generate_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the recipe generation process"""
        await update.message.reply_text(
            "🥘 Let's create a recipe!\n\n"
            "Please list the ingredients you have, separated by commas.\n"
            "Example: chicken breast, tomatoes, garlic, olive oil, pasta"
        )
        return ConversationStates.WAITING_FOR_INGREDIENTS
    
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
        recipe = Recipe.create_new(
            user_id=update.effective_user.id,
            name=recipe_name,
            content=recipe_content,
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
        return ConversationStates.WAITING_FOR_RECIPE_NAME
    
    async def add_recipe_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Save recipe name and ask for content"""
        context.user_data['recipe_name'] = update.message.text
        
        await update.message.reply_text(
            "Great! Now please share your recipe.\n\n"
            "Include ingredients (with metric measurements) and instructions.\n"
            "You can format it however you like!"
        )
        return ConversationStates.WAITING_FOR_RECIPE_CONTENT
    
    async def add_recipe_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Save the complete recipe"""
        recipe = Recipe.create_new(
            user_id=update.effective_user.id,
            name=context.user_data['recipe_name'],
            content=update.message.text,
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
            await self._handle_view_recipe(query, user_id, data)
        elif data.startswith("edit_"):
            await self._handle_edit_recipe(query, context, data)
        elif data.startswith("ai_verify_"):
            await self.verify_recipe(update, context)
        elif data.startswith("manual_edit_"):
            recipe_id = data.replace("manual_edit_", "")
            context.user_data['editing_recipe_id'] = recipe_id
            await query.edit_message_text(
                "✏️ Please send the updated recipe content.\n"
                "Send /cancel to cancel editing."
            )
            return ConversationStates.WAITING_FOR_RECIPE_UPDATE
        elif data.startswith("delete_"):
            await self._handle_delete_recipe(query, user_id, data)
        elif data == "list":
            await self._handle_list_recipes(query, user_id)
    
    async def _handle_view_recipe(self, query, user_id: int, data: str) -> None:
        """Handle viewing a recipe"""
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
    
    async def _handle_edit_recipe(self, query, context: ContextTypes.DEFAULT_TYPE, data: str) -> int:
        """Handle editing a recipe"""
        recipe_id = data.replace("edit_", "")
        context.user_data['editing_recipe_id'] = recipe_id
        
        # Get existing recipe to store in context
        recipe = await self.storage.get_recipe(query.from_user.id, recipe_id)
        if recipe:
            context.user_data['original_recipe'] = recipe.content
        
        keyboard = [
            [
                InlineKeyboardButton("✏️ Manual Edit", callback_data=f"manual_edit_{recipe_id}"),
                InlineKeyboardButton("🤖 AI Verify", callback_data=f"ai_verify_{recipe_id}")
            ],
            [InlineKeyboardButton("« Back", callback_data=f"view_{recipe_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "How would you like to edit this recipe?\n\n"
            "✏️ Manual Edit - Write your own changes\n"
            "🤖 AI Verify - Let AI check and improve the recipe",
            reply_markup=reply_markup
        )
        return ConversationStates.CHOOSING_EDIT_TYPE
    
    async def _handle_delete_recipe(self, query, user_id: int, data: str) -> None:
        """Handle deleting a recipe"""
        recipe_id = data.replace("delete_", "")
        await self.storage.delete_recipe(user_id, recipe_id)
        
        await query.edit_message_text("🗑 Recipe deleted successfully!")
        
        # Show updated list
        await self._handle_list_recipes(query, user_id)
    
    async def _handle_list_recipes(self, query, user_id: int) -> None:
        """Handle showing the recipe list"""
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
    
    async def verify_recipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Verify and improve recipe using LLM"""
        if 'editing_recipe_id' not in context.user_data:
            await update.callback_query.edit_message_text("❌ No recipe selected for verification.")
            return ConversationHandler.END
            
        recipe_id = context.user_data['editing_recipe_id']
        user_id = update.callback_query.from_user.id
        
        # Get existing recipe
        recipe = await self.storage.get_recipe(user_id, recipe_id)
        if not recipe:
            await update.callback_query.edit_message_text("❌ Recipe not found.")
            return ConversationHandler.END
        
        await update.callback_query.edit_message_text("🤖 Verifying and improving recipe... This may take a moment.")
        
        try:
            # Update recipe using LLM
            improved_content = await self.llm.update_recipe(recipe.content)
            
            # Update recipe content (this will also update the timestamp)
            recipe.update_content(improved_content)
            recipe.is_ai_generated = True
            
            # Save updated recipe
            await self.storage.update_recipe(user_id, recipe_id, recipe)
            
            # Create keyboard for after verification
            keyboard = [
                [InlineKeyboardButton("« Back to Recipe", callback_data=f"view_{recipe_id}")],
                [InlineKeyboardButton("« Back to List", callback_data="list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                f"✅ Recipe '{recipe.name}' has been verified and improved!\n\n"
                f"{improved_content}",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error during recipe verification: {e}")
            await update.callback_query.edit_message_text(
                "❌ Sorry, there was an error verifying the recipe. Please try again later."
            )
    
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END