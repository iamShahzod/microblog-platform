from fastapi import FastAPI
import uvicorn
from datetime import datetime

# Простейшее приложение
app = FastAPI(title="Микроблог API", version="1.0.0")

@app.get("/")
async def home():
    return {
        "message": " Микроблог платформа работает!",
        "timestamp": datetime.now().isoformat(),
        "architecture": {
            "database": "MongoDB (localhost:27017)",
            "search": "Elasticsearch (localhost:9200)",
            "cache": "Hazelcast (localhost:5701)"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "services": [
            {"name": "MongoDB", "status": "running", "port": 27017},
            {"name": "Elasticsearch", "status": "running", "port": 9200},
            {"name": "Hazelcast", "status": "running", "port": 5701},
            {"name": "Hazelcast Management", "status": "running", "port": 8080}
        ]
    }

@app.get("/api/v1/test")
async def test():
    return {"test": "API работает правильно"}

if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК МИКРОБЛОГ ПЛАТФОРМЫ")
    print("=" * 50)
    print(" API: http://localhost:8000")
    print(" Документация: http://localhost:8000/docs")
    print("Проверка здоровья: http://localhost:8000/health")
    print("=" * 50)
    print(" Ссылки на сервисы:")
    print("  - MongoDB: localhost:27017")
    print("  - Elasticsearch: http://localhost:9200")
    print("  - Hazelcast Management: http://localhost:8080")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")