"""PostgreSQL storage implementation"""
import os
import json
import logging
from typing import List, Optional
import asyncpg
from datetime import datetime
from .interface import StorageInterface
from ..models.recipe import Recipe
import asyncio

logger = logging.getLogger(__name__)

class PostgreSQLStorage(StorageInterface):
    """PostgreSQL storage implementation"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL not provided")
        
        # Convert Railway's postgres:// to postgresql:// for asyncpg
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
        
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection and create tables, with retry logic if DB is sleeping"""
        max_retries = 5
        delay = 5  # seconds
        attempt = 0
        while attempt < max_retries:
            try:
                # Try a direct connection and simple query to wake up DB
                conn = await asyncpg.connect(self.database_url)
                await conn.execute("SELECT 1;")
                await conn.close()
                break  # Success, exit retry loop
            except Exception as e:
                attempt += 1
                logger.warning(f"Database connection attempt {attempt} failed: {e}")
                if attempt >= max_retries:
                    logger.error(f"Failed to connect to database after {max_retries} attempts.")
                    raise
                await asyncio.sleep(delay)
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            await self._create_tables()
            logger.info("PostgreSQL storage initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL storage: {e}")
            raise
    
    async def _create_tables(self):
        """Create necessary tables if they don't exist"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS recipes (
                    id VARCHAR(255) PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    is_ai_generated BOOLEAN DEFAULT FALSE,
                    data JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_user_id ON recipes(user_id);
            """)
    
    async def close(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
    
    async def save_recipe(self, user_id: int, recipe: Recipe) -> None:
        """Save a recipe for a user"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO recipes (id, user_id, name, content, created_at, updated_at, is_ai_generated, data)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    content = EXCLUDED.content,
                    updated_at = EXCLUDED.updated_at,
                    data = EXCLUDED.data
            """, 
            recipe.id, 
            user_id, 
            recipe.name, 
            recipe.content,
            datetime.fromisoformat(recipe.created_at),
            datetime.fromisoformat(recipe.updated_at),
            recipe.is_ai_generated,
            json.dumps(recipe.to_dict())
            )
        logger.info(f"Saved recipe {recipe.id} for user {user_id}")
    
    async def get_recipes(self, user_id: int) -> List[Recipe]:
        """Get all recipes for a user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT data FROM recipes 
                WHERE user_id = $1 
                ORDER BY created_at DESC
            """, user_id)
            
            recipes = []
            for row in rows:
                try:
                    recipe_data = json.loads(row['data'])
                    recipes.append(Recipe.from_dict(recipe_data))
                except Exception as e:
                    logger.error(f"Error parsing recipe data: {e}")
            
            return recipes
    
    async def get_recipe(self, user_id: int, recipe_id: str) -> Optional[Recipe]:
        """Get a specific recipe"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT data FROM recipes 
                WHERE user_id = $1 AND id = $2
            """, user_id, recipe_id)
            
            if row:
                try:
                    recipe_data = json.loads(row['data'])
                    return Recipe.from_dict(recipe_data)
                except Exception as e:
                    logger.error(f"Error parsing recipe data: {e}")
            
            return None
    
    async def update_recipe(self, user_id: int, recipe: Recipe) -> None:
        """Update an existing recipe"""
        recipe.updated_at = datetime.now().isoformat()
        await self.save_recipe(user_id, recipe)
        logger.info(f"Updated recipe {recipe.id} for user {user_id}")
    
    async def delete_recipe(self, user_id: int, recipe_id: str) -> None:
        """Delete a recipe"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM recipes 
                WHERE user_id = $1 AND id = $2
            """, user_id, recipe_id)
        logger.info(f"Deleted recipe {recipe_id} for user {user_id}")