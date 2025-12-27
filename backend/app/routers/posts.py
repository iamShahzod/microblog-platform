from fastapi import APIRouter, HTTPException
from app.models.post import Post
from app.services import mongo_service, search_service, cache_service

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/")
async def create_post(user_id: str, text: str, tags: list = []):
    # Сохраняем в MongoDB
    post_id = mongo_service.create_post(user_id, text, tags)
    
    # Индексируем в Elasticsearch
    search_service.index_post(post_id, text, tags, user_id)
    
    # Получаем подписчиков (пока заглушка)
    # followers = mongo_service.get_followers(user_id)
    
    # Добавляем в кэш подписчикам
    # for follower in followers:
    #     cache_service.add_to_feed(follower, {
    #         "post_id": post_id,
    #         "text": text,
    #         "author_id": user_id
    #     })
    
    return {"post_id": post_id, "message": "Post created"}

@router.get("/{post_id}")
async def get_post(post_id: str):
    post = mongo_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post