from elasticsearch import Elasticsearch

es = Elasticsearch(["http://localhost:9200"])

def index_post(post_id: str, text: str, tags: list, user_id: str):
    """Добавляет пост в поисковый индекс"""
    es.index(
        index="posts",
        id=post_id,
        document={
            "text": text,
            "tags": tags,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

def search_posts(query: str):
    """Ищет посты по тексту"""
    response = es.search(
        index="posts",
        body={
            "query": {
                "match": {
                    "text": query
                }
            }
        }
    )
    return response["hits"]["hits"]