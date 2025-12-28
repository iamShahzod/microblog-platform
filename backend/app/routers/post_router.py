from fastapi import APIRouter, HTTPException
from app.models.post import PostCreate, PostResponse
from app.services.mongo_service import (
    create_post,
    get_post_by_id,
    like_post,
    get_posts_by_user
)
from app.services.search_service import index_post
from app.services.cache_service import add_post_to_feed
from bson import ObjectId

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/", response_model=dict)
async def api_create_post(post: PostCreate):
    """Создание нового поста"""
    # Сохраняем в MongoDB
    post_id = create_post(post.dict())
    
    # Индексируем в Elasticsearch
    try:
        index_post(post_id, post.text, post.tags, post.user_id)
    except Exception as e:
        print(f"Warning: Elasticsearch indexing failed: {e}")
    
    # TODO: Получить подписчиков и обновить их кэш
    # Пока просто сохраняем в кэше автора
    post_data = {
        "_id": ObjectId(post_id),
        "text": post.text,
        "user_id": post.user_id,
        "created_at": datetime.utcnow()
    }
    add_post_to_feed(post.user_id, post_data)
    
    return {"message": "Пост создан", "id": post_id}

@router.get("/{post_id}", response_model=PostResponse)
async def api_get_post(post_id: str):
    """Получение поста по ID"""
    post = get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    post["_id"] = str(post["_id"])
    post["likes_count"] = len(post.get("likes", []))
    return post

@router.post("/{post_id}/like")
async def api_like_post(post_id: str, user_id: str):
    """Поставить лайк посту"""
    success = like_post(post_id, user_id)
    if success:
        return {"message": "Лайк добавлен", "post_id": post_id}
    else:
        raise HTTPException(status_code=500, detail="Ошибка при добавлении лайка")

@router.get("/user/{user_id}")
async def api_get_user_posts(user_id: str, limit: int = 50):
    """Получить посты пользователя"""
    posts = get_posts_by_user(user_id, limit)
    
    for post in posts:
        post["_id"] = str(post["_id"])
        post["likes_count"] = len(post.get("likes", []))
    
    return {
        "user_id": user_id,
        "count": len(posts),
        "posts": posts
    }