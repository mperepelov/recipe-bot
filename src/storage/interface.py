"""Storage interface definition"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.recipe import Recipe

class StorageInterface(ABC):
    """Abstract interface for storage implementations"""
    
    @abstractmethod
    async def save_recipe(self, user_id: int, recipe: Recipe) -> None:
        """Save a recipe for a user"""
        pass
    
    @abstractmethod
    async def get_recipes(self, user_id: int) -> List[Recipe]:
        """Get all recipes for a user"""
        pass
    
    @abstractmethod
    async def get_recipe(self, user_id: int, recipe_id: str) -> Optional[Recipe]:
        """Get a specific recipe"""
        pass
    
    @abstractmethod
    async def update_recipe(self, user_id: int, recipe: Recipe) -> None:
        """Update an existing recipe"""
        pass
    
    @abstractmethod
    async def delete_recipe(self, user_id: int, recipe_id: str) -> None:
        """Delete a recipe"""
        pass