from pymongo import MongoClient
from elasticsearch import Elasticsearch
import hazelcast

# Клиенты для подключения
mongo_client = None
es_client = None
hz_client = None
users_collection = None
posts_collection = None
feed_cache = None

def init_db():
    global mongo_client, es_client, hz_client
    global users_collection, posts_collection, feed_cache
    
    # MongoDB
    mongo_client = MongoClient("mongodb://localhost:27017")
    db = mongo_client["microblog"]
    users_collection = db["users"]
    posts_collection = db["posts"]
    
    # Elasticsearch
    es_client = Elasticsearch(["http://localhost:9200"])
    
    # Hazelcast
    hz_client = hazelcast.HazelcastClient(
        cluster_members=["localhost:5701"],
        cluster_name="dev"
    )
    feed_cache = hz_client.get_map("user_feeds").blocking()
    
    print(f" MongoDB: {mongo_client.server_info()['version']}")
    print(f"Elasticsearch: {es_client.info()['version']['number']}")
    print(f"Hazelcast: {hz_client.lifecycle_service.is_running()}")
    
    return {
        "mongodb": mongo_client,
        "elasticsearch": es_client,
        "hazelcast": hz_client
    }

def get_mongo():
    return mongo_client

def get_elastic():
    return es_client

def get_hazelcast():
    return hz_client