"""JSON file-based storage implementation"""
import os
import json
import logging
from typing import List, Optional
from .interface import StorageInterface
from ..models.recipe import Recipe

logger = logging.getLogger(__name__)

class JSONFileStorage(StorageInterface):
    """JSON file-based storage implementation"""
    
    def __init__(self, storage_path: str = "recipe_data"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def _get_user_file(self, user_id: int) -> str:
        """Get the file path for a user's recipes"""
        return os.path.join(self.storage_path, f"user_{user_id}.json")
    
    async def save_recipe(self, user_id: int, recipe: Recipe) -> None:
        """Save a recipe for a user"""
        file_path = self._get_user_file(user_id)
        recipes = await self.get_recipes(user_id)
        recipes.append(recipe)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in recipes], f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved recipe {recipe.id} for user {user_id}")
    
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
    
    async def update_recipe(self, user_id: int, recipe_id: str, recipe: Recipe) -> None:
        """Update an existing recipe"""
        recipes = await self.get_recipes(user_id)
        updated = False
        
        for i, r in enumerate(recipes):
            if r.id == recipe_id:
                recipes[i] = recipe
                updated = True
                break
        
        if not updated:
            logger.warning(f"Recipe {recipe_id} not found for user {user_id}")
            return
        
        file_path = self._get_user_file(user_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in recipes], f, ensure_ascii=False, indent=2)
        
        logger.info(f"Updated recipe {recipe_id} for user {user_id}")
    
    async def delete_recipe(self, user_id: int, recipe_id: str) -> None:
        """Delete a recipe"""
        recipes = await self.get_recipes(user_id)
        recipes = [r for r in recipes if r.id != recipe_id]
        
        file_path = self._get_user_file(user_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in recipes], f, ensure_ascii=False, indent=2)
        
        logger.info(f"Deleted recipe {recipe_id} for user {user_id}")