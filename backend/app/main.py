from fastapi import FastAPI
from datetime import datetime
import pymongo
from elasticsearch import Elasticsearch
import hazelcast

from app.routers import user_router, post_router, search_router

app = FastAPI(
    title="Микроблог API",
    description="Распределенная платформа микроблогов на NoSQL",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Подключение к сервисам
MONGO_STATUS = "❌"
ES_STATUS = "❌"
HZ_STATUS = "❌"

try:
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=3000)
    mongo_client.server_info()
    MONGO_STATUS = "✅"
except Exception as e:
    MONGO_STATUS = f"❌ {str(e)[:50]}"

try:
    es_client = Elasticsearch(["http://localhost:9200"], request_timeout=5)
    if es_client.ping():
        ES_STATUS = "✅"
    else:
        ES_STATUS = "❌"
except Exception as e:
    ES_STATUS = f"❌ {str(e)[:50]}"

try:
    hz_client = hazelcast.HazelcastClient(
        cluster_members=["localhost:5701"],
        cluster_connect_timeout=3.0
    )
    if hz_client.lifecycle_service.is_running():
        HZ_STATUS = "✅"
    else:
        HZ_STATUS = "❌"
    hz_client.shutdown()
except Exception as e:
    HZ_STATUS = f"❌ {str(e)[:50]}"

# Подключение роутеров
app.include_router(user_router.router, prefix="/api/v1")
app.include_router(post_router.router, prefix="/api/v1")
app.include_router(search_router.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "🚀 Микроблог Платформа v2.0",
        "description": "Распределенная платформа на MongoDB, Elasticsearch, Hazelcast",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "users": "/api/v1/users",
            "posts": "/api/v1/posts",
            "search": "/api/v1/search",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    """Проверка состояния системы"""
    overall = "✅" if all(s == "✅" for s in [MONGO_STATUS, ES_STATUS, HZ_STATUS]) else "⚠️"
    
    return {
        "status": overall,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "mongodb": MONGO_STATUS,
            "elasticsearch": ES_STATUS,
            "hazelcast": HZ_STATUS
        },
        "endpoints": {
            "api": "http://localhost:8000",
            "docs": "http://localhost:8000/docs",
            "elasticsearch": "http://localhost:9200",
            "hazelcast": "http://localhost:8080"
        }
    }

@app.get("/stats")
async def stats():
    """Статистика системы"""
    try:
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        db = mongo["microblog"]
        
        user_count = db.users.count_documents({})
        post_count = db.posts.count_documents({})
        
        return {
            "users": user_count,
            "posts": post_count,
            "timestamp": datetime.now().isoformat()
        }
    except:
        return {
            "users": 0,
            "posts": 0,
            "note": "Не удалось получить статистику"
        }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 ЗАПУСК МИКРОБЛОГ ПЛАТФОРМЫ v2.0")
    print("=" * 60)
    print(f"📊 Состояние сервисов:")
    print(f"  - MongoDB: {MONGO_STATUS}")
    print(f"  - Elasticsearch: {ES_STATUS}")
    print(f"  - Hazelcast: {HZ_STATUS}")
    print("=" * 60)
    print("🔗 Доступные ссылки:")
    print("  - API: http://localhost:8000")
    print("  - Документация: http://localhost:8000/docs")
    print("  - Elasticsearch: http://localhost:9200")
    print("  - Hazelcast: http://localhost:8080 (admin/admin)")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)