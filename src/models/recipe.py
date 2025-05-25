"""Recipe data model"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any

@dataclass
class Recipe:
    """Data class representing a recipe"""
    id: str
    name: str
    content: str
    created_at: str
    updated_at: str
    is_ai_generated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recipe to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recipe':
        """Create recipe from dictionary"""
        return cls(**data)
    
    @classmethod
    def create_new(cls, user_id: int, name: str, content: str, is_ai_generated: bool = False) -> 'Recipe':
        """Factory method to create a new recipe"""
        now = datetime.now().isoformat()
        return cls(
            id=f"recipe_{user_id}_{datetime.now().timestamp()}",
            name=name,
            content=content,
            created_at=now,
            updated_at=now,
            is_ai_generated=is_ai_generated
        )
    
    def update_content(self, new_content: str) -> None:
        """Update recipe content"""
        self.content = new_content
        self.updated_at = datetime.now().isoformat()