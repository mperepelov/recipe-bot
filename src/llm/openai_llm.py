"""OpenAI LLM implementation"""
import logging
import requests
from typing import List
from .interface import LLMInterface

logger = logging.getLogger(__name__)

class OpenAILLM(LLMInterface):
    """OpenAI GPT implementation using requests"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    async def generate_recipe(self, ingredients: List[str]) -> str:
        """Generate a recipe from ingredients"""
        prompt = self._create_prompt(ingredients)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a helpful cooking assistant that only provides recipes and cooking-related advice. Always use metric measurements."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("Invalid OpenAI API key")
                return "Error: Invalid OpenAI API key. Please check your API key."
            elif e.response.status_code == 429:
                logger.error("OpenAI rate limit exceeded")
                return "Error: Rate limit exceeded. Please try again in a few moments."
            else:
                logger.error(f"HTTP error: {e}")
                return f"Sorry, I couldn't generate a recipe. Error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Error generating recipe: {e}")
            return "Sorry, I couldn't generate a recipe at this time. Please try again later."
    
    def _create_prompt(self, ingredients: List[str]) -> str:
        """Create the prompt for recipe generation"""
        return f"""You are a professional chef. Create a detailed recipe using ONLY these ingredients: {', '.join(ingredients)}.

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