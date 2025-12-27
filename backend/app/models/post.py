from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Post(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    text: str
    tags: List[str] = []
    likes: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True