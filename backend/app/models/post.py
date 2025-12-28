from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class PostBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    tags: List[str] = Field(default_factory=list)

class PostCreate(PostBase):
    user_id: str

class PostResponse(PostBase):
    id: str = Field(..., alias="_id")
    user_id: str
    likes: List[str] = []
    likes_count: int = 0
    created_at: datetime
    
    class Config:
        allow_population_by_field_name = True