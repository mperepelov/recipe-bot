"""Persistent JSON storage for Railway volumes"""
import os
import json
import logging
from typing import List, Optional
from .interface import StorageInterface
from ..models.recipe import Recipe

logger = logging.getLogger(__name__)

class PersistentJSONStorage(StorageInterface):
    """JSON storage using Railway's persistent volumes"""
    
    def __init__(self, storage_path: str = None):
        # Use Railway's persistent volume path or fallback
        self.storage_path = storage_path or os.getenv("STORAGE_PATH", "/data/recipes")
        
        # Ensure the directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Test write permissions
        test_file = os.path.join(self.storage_path, ".write_test")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"Storage initialized at: {self.storage_path}")
        except Exception as e:
            logger.error(f"Cannot write to storage path {self.storage_path}: {e}")
            # Fallback to temp directory
            self.storage_path = "/tmp/recipes"
            os.makedirs(self.storage_path, exist_ok=True)
            logger.warning(f"Using fallback storage at: {self.storage_path}")
    
    def _get_user_file(self, user_id: int) -> str:
        """Get the file path for a user's recipes"""
        return os.path.join(self.storage_path, f"user_{user_id}.json")
    
    async def initialize(self):
        """Initialize storage (for compatibility with PostgreSQL storage)"""
        pass
    
    async def close(self):
        """Close storage (for compatibility with PostgreSQL storage)"""
        pass
    
    async def save_recipe(self, user_id: int, recipe: Recipe) -> None:
        """Save a recipe for a user"""
        file_path = self._get_user_file(user_id)
        recipes = await self.get_recipes(user_id)
        
        # Update existing or add new
        recipe_exists = False
        for i, r in enumerate(recipes):
            if r.id == recipe.id:
                recipes[i] = recipe
                recipe_exists = True
                break
        
        if not recipe_exists:
            recipes.append(recipe)
        
        # Write to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in recipes], f, ensure_ascii=False, indent=2)
            logger.info(f"Saved recipe {recipe.id} for user {user_id} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving recipe: {e}")
            raise
    
    async def get_recipes(self, user_id: int) -> List[Recipe]:
        """Get all recipes for a user"""
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
        """Get a specific recipe"""
        recipes = await self.get_recipes(user_id)
        for recipe in recipes:
            if recipe.id == recipe_id:
                return recipe
        return None
    
    async def update_recipe(self, user_id: int, recipe: Recipe) -> None:
        """Update an existing recipe"""
        await self.save_recipe(user_id, recipe)
        logger.info(f"Updated recipe {recipe.id} for user {user_id}")
    
    async def delete_recipe(self, user_id: int, recipe_id: str) -> None:
        """Delete a recipe"""
        recipes = await self.get_recipes(user_id)
        recipes = [r for r in recipes if r.id != recipe_id]
        
        file_path = self._get_user_file(user_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in recipes], f, ensure_ascii=False, indent=2)
            logger.info(f"Deleted recipe {recipe_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting recipe: {e}")
            raise