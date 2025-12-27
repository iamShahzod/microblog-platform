from elasticsearch import Elasticsearch
from app.config import ES_HOST

es_client = Elasticsearch([ES_HOST])

def index_post(post_id: str, post_data: dict):
    """Индексирует пост в Elasticsearch"""
    es_client.index(
        index="posts",
        id=post_id,
        document={
            "text": post_data["text"],
            "tags": post_data.get("tags", []),
            "user_id": post_data["user_id"],
            "created_at": post_data.get("created_at", "").isoformat() if hasattr(post_data.get("created_at"), "isoformat") else str(post_data.get("created_at", ""))
        }
    )

def search_posts(query: str, size: int = 10):
    """Ищет посты по тексту"""
    response = es_client.search(
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
    return [hit["_source"] for hit in response["hits"]["hits"]]

def aggregate_tags_by_date(start_date: str, end_date: str):
    """Агрегирует теги по дате"""
    response = es_client.search(
        index="posts",
        body={
            "aggs": {
                "tags": {
                    "terms": {
                        "field": "tags.keyword",
                        "size": 10
                    }
                }
            },
            "query": {
                "range": {
                    "created_at": {
                        "gte": start_date,
                        "lte": end_date
                    }
                }
            }
        }
    )
    return [bucket for bucket in response["aggregations"]["tags"]["buckets"]]