from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import pymongo
from elasticsearch import Elasticsearch
import hazelcast

# Модели данных
class User(BaseModel):
    username: str
    email: str
    bio: Optional[str] = ""

class PostCreate(BaseModel):
    user_id: str
    text: str
    tags: List[str] = []

class PostResponse(BaseModel):
    id: str
    user_id: str
    text: str
    tags: List[str]
    likes: int
    created_at: datetime

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10

class FollowRequest(BaseModel):
    follower_id: str
    following_id: str

# Инициализация приложения
app = FastAPI(
    title="Микроблог API",
    description="Распределенная платформа микроблогов",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Подключение к сервисам
try:
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
    db = mongo_client["microblog"]
    users_collection = db["users"]
    posts_collection = db["posts"]
    MONGO_STATUS = "✅"
except Exception as e:
    MONGO_STATUS = f"❌ {str(e)}"

try:
    es_client = Elasticsearch(["http://localhost:9200"], request_timeout=5)
    ES_STATUS = "✅" if es_client.ping() else "❌"
except Exception as e:
    ES_STATUS = f"❌ {str(e)}"

try:
    hz_client = hazelcast.HazelcastClient(
        cluster_members=["localhost:5701"],
        cluster_connect_timeout=3.0
    )
    feed_cache = hz_client.get_map("user_feeds").blocking()
    HZ_STATUS = "✅"
except Exception as e:
    HZ_STATUS = f"❌ {str(e)}"

# ========== ПОЛЬЗОВАТЕЛИ ==========
@app.post("/api/users/", 
          summary="Создать пользователя", 
          tags=["Пользователи"],
          response_description="ID созданного пользователя")
async def create_user(user: User):
    """Создает нового пользователя в системе"""
    # Проверяем, существует ли пользователь
    existing = users_collection.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    user_dict = user.dict()
    user_dict["created_at"] = datetime.utcnow()
    user_dict["followers"] = []
    user_dict["following"] = []
    
    result = users_collection.insert_one(user_dict)
    return {"id": str(result.inserted_id), **user_dict}

@app.get("/api/users/{username}", 
         summary="Получить пользователя", 
         tags=["Пользователи"])
async def get_user(username: str):
    """Получает информацию о пользователе по имени"""
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user["_id"] = str(user["_id"])
    return user

@app.put("/api/users/{username}/follow",
         summary="Подписаться на пользователя",
         tags=["Пользователи"])
async def follow_user(username: str, follow_req: FollowRequest):
    """Подписаться на другого пользователя"""
    # Здесь должна быть логика подписки
    return {"message": f"Пользователь {follow_req.follower_id} подписан на {follow_req.following_id}"}

# ========== ПОСТЫ ==========
@app.post("/api/posts/",
          summary="Создать пост",
          tags=["Посты"],
          response_model=PostResponse)
async def create_post(post: PostCreate):
    """Создает новый пост в микроблоге"""
    post_dict = post.dict()
    post_dict["created_at"] = datetime.utcnow()
    post_dict["likes"] = []
    
    # Сохраняем в MongoDB
    result = posts_collection.insert_one(post_dict)
    post_id = str(result.inserted_id)
    
    # Индексируем в Elasticsearch (если он работает)
    if ES_STATUS == "✅":
        try:
            es_client.index(
                index="posts",
                id=post_id,
                document={
                    "text": post_dict["text"],
                    "tags": post_dict.get("tags", []),
                    "user_id": post_dict["user_id"],
                    "created_at": post_dict["created_at"].isoformat()
                }
            )
        except:
            pass
    
    # Обновляем кэш подписчиков (упрощенно)
    if HZ_STATUS == "✅":
        # Получаем подписчиков (в реальности из БД)
        followers = ["user1", "user2"]  # Заглушка
        for follower in followers:
            feed = feed_cache.get(follower) or []
            feed.append({
                "post_id": post_id,
                "text": post.text[:100],
                "author_id": post.user_id,
                "timestamp": post_dict["created_at"].isoformat()
            })
            feed_cache.put(follower, feed[-100:])  # Храним 100 последних
    
    return {
        "id": post_id,
        **post_dict,
        "likes": 0
    }

@app.get("/api/posts/{post_id}",
         summary="Получить пост по ID",
         tags=["Посты"])
async def get_post(post_id: str):
    """Получает пост по его идентификатору"""
    from bson import ObjectId
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Пост не найден")
        post["_id"] = str(post["_id"])
        return post
    except:
        raise HTTPException(status_code=400, detail="Неверный ID поста")

@app.post("/api/posts/{post_id}/like",
          summary="Поставить лайк посту",
          tags=["Посты"])
async def like_post(post_id: str, user_id: str):
    """Добавляет лайк к посту от пользователя"""
    from bson import ObjectId
    posts_collection.update_one(
        {"_id": ObjectId(post_id)},
        {"$addToSet": {"likes": user_id}}
    )
    return {"message": "Лайк добавлен", "post_id": post_id}

# ========== ПОИСК ==========
@app.post("/api/search",
          summary="Поиск по постам",
          tags=["Поиск"])
async def search_posts(search: SearchQuery):
    """Выполняет полнотекстовый поиск по постам"""
    if ES_STATUS != "✅":
        return {"message": "Elasticsearch недоступен", "results": []}
    
    try:
        response = es_client.search(
            index="posts",
            body={
                "query": {
                    "multi_match": {
                        "query": search.query,
                        "fields": ["text", "tags"]
                    }
                },
                "size": search.limit
            }
        )
        
        results = []
        for hit in response["hits"]["hits"]:
            results.append({
                "id": hit["_id"],
                "score": hit["_score"],
                **hit["_source"]
            })
        
        return {
            "query": search.query,
            "total": response["hits"]["total"]["value"],
            "results": results
        }
    except Exception as e:
        return {"error": str(e), "results": []}

@app.get("/api/trends",
         summary="Тренды по тегам",
         tags=["Поиск"])
async def get_trends(date: str = None):
    """Получает популярные теги за указанную дату"""
    if ES_STATUS != "✅":
        return {"message": "Elasticsearch недоступен", "trends": []}
    
    try:
        # Агрегация по тегам
        response = es_client.search(
            index="posts",
            body={
                "size": 0,
                "aggs": {
                    "popular_tags": {
                        "terms": {
                            "field": "tags.keyword",
                            "size": 10
                        }
                    }
                }
            }
        )
        
        trends = []
        for bucket in response["aggregations"]["popular_tags"]["buckets"]:
            trends.append({
                "tag": bucket["key"],
                "count": bucket["doc_count"]
            })
        
        return {"trends": trends}
    except Exception as e:
        return {"error": str(e), "trends": []}

# ========== ЛЕНТА ==========
@app.get("/api/feed/{user_id}",
         summary="Получить ленту пользователя",
         tags=["Лента"])
async def get_feed(user_id: str, use_cache: bool = True):
    """Получает ленту новостей пользователя"""
    if use_cache and HZ_STATUS == "✅":
        # Пытаемся получить из кэша
        cached_feed = feed_cache.get(user_id)
        if cached_feed:
            return {
                "source": "cache",
                "count": len(cached_feed),
                "feed": cached_feed
            }
    
    # Если нет в кэше или кэш отключен, получаем из БД
    # Здесь упрощенная логика - в реальности нужно получать посты от тех, на кого подписан
    from bson import ObjectId
    posts = list(posts_collection.find().sort("created_at", -1).limit(50))
    
    for post in posts:
        post["_id"] = str(post["_id"])
    
    return {
        "source": "database",
        "count": len(posts),
        "feed": posts
    }

# ========== СИСТЕМНЫЕ ==========
@app.get("/",
         summary="Главная страница",
         tags=["Система"])
async def root():
    return {
        "message": "Добро пожаловать в Микроблог API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "architecture": {
            "database": "MongoDB",
            "search": "Elasticsearch",
            "cache": "Hazelcast"
        }
    }

@app.get("/health",
         summary="Проверка здоровья системы",
         tags=["Система"])
async def health():
    return {
        "status": "healthy" if all(s == "✅" for s in [MONGO_STATUS, ES_STATUS, HZ_STATUS]) else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "mongodb": MONGO_STATUS,
            "elasticsearch": ES_STATUS,
            "hazelcast": HZ_STATUS
        }
    }

@app.get("/stats",
         summary="Статистика системы",
         tags=["Система"])
async def stats():
    """Возвращает статистику по системе"""
    user_count = users_collection.count_documents({}) if MONGO_STATUS == "✅" else 0
    post_count = posts_collection.count_documents({}) if MONGO_STATUS == "✅" else 0
    
    return {
        "users": user_count,
        "posts": post_count,
        "cache_entries": feed_cache.size() if HZ_STATUS == "✅" else 0,
        "search_indexed": es_client.count(index="posts")["count"] if ES_STATUS == "✅" else 0
    }

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ЗАПУСК МИКРОБЛОГ ПЛАТФОРМЫ")
    print("=" * 60)
    print("📌 API: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/docs")
    print("🔴 ReDoc: http://localhost:8000/redoc")
    print("=" * 60)
    print("🏗️  Архитектура:")
    print(f"  - MongoDB: {MONGO_STATUS}")
    print(f"  - Elasticsearch: {ES_STATUS}")
    print(f"  - Hazelcast: {HZ_STATUS}")
    print("=" * 60)
    print("🔧 Доступные API:")
    print("  POST /api/users/     - Создать пользователя")
    print("  GET  /api/users/{id} - Получить пользователя")
    print("  POST /api/posts/     - Создать пост")
    print("  POST /api/search     - Поиск по постам")
    print("  GET  /api/feed/{id}  - Лента пользователя")
    print("  GET  /api/trends     - Популярные теги")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")