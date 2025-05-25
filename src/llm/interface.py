"""LLM interface definition"""
from abc import ABC, abstractmethod
from typing import List

class LLMInterface(ABC):
    """Abstract interface for LLM implementations"""
    
    @abstractmethod
    async def generate_recipe(self, ingredients: List[str]) -> str:
        """Generate a recipe from ingredients"""
        pass