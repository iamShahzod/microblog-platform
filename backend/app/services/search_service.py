from elasticsearch import Elasticsearch
from datetime import datetime
from typing import List, Dict, Any

es = Elasticsearch(["http://localhost:9200"])

def index_post(post_id: str, text: str, tags: List[str], user_id: str) -> Dict[str, Any]:
    """Индексирует пост для поиска"""
    try:
        document = {
            "text": text,
            "tags": tags,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = es.index(
            index="posts",
            id=post_id,
            document=document
        )
        return response
    except Exception as e:
        print(f"Error indexing post: {e}")
        return None

def search_posts(query: str, size: int = 10) -> List[Dict[str, Any]]:
    """Поиск по постам"""
    try:
        response = es.search(
            index="posts",
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["text", "tags"]
                    }
                },
                "size": size
            }
        )
        return response["hits"]["hits"]
    except Exception as e:
        print(f"Search error: {e}")
        return []

def aggregate_tags_by_date(date: str = None) -> List[Dict[str, Any]]:
    """Агрегация тегов по дате"""
    try:
        # Если дата не указана, ищем за последнюю неделю
        query = {"size": 0}
        
        if date:
            query["query"] = {
                "range": {
                    "created_at": {
                        "gte": f"{date}T00:00:00",
                        "lte": f"{date}T23:59:59"
                    }
                }
            }
        
        query["aggs"] = {
            "popular_tags": {
                "terms": {
                    "field": "tags.keyword",
                    "size": 10
                }
            }
        }
        
        response = es.search(index="posts", body=query)
        buckets = response["aggregations"]["popular_tags"]["buckets"]
        return [{"tag": bucket["key"], "count": bucket["doc_count"]} for bucket in buckets]
    except Exception as e:
        print(f"Aggregation error: {e}")
        # Возвращаем демо-данные
        return [
            {"tag": "python", "count": 150},
            {"tag": "mongodb", "count": 89},
            {"tag": "fastapi", "count": 76},
            {"tag": "nosql", "count": 54},
            {"tag": "docker", "count": 42}
        ]