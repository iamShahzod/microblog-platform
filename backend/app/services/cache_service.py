import hazelcast
from typing import List, Dict, Any
from datetime import datetime

client = hazelcast.HazelcastClient(
    cluster_members=["localhost:5701"],
    cluster_name="dev"
)

user_feeds_map = client.get_map("user_feeds").blocking()
post_likes_map = client.get_map("post_likes").blocking()

def add_post_to_feed(user_id: str, post: Dict[str, Any]) -> bool:
    """Добавляет пост в ленту пользователя"""
    current_feed = user_feeds_map.get(user_id)
    if not current_feed:
        current_feed = []
    
    # Добавляем метаданные для кэша
    post_with_meta = {
        "id": str(post.get("_id", "")),
        "text": post.get("text", "")[:200],
        "user_id": post.get("user_id", ""),
        "created_at": post.get("created_at", datetime.utcnow()).isoformat(),
        "cached_at": datetime.utcnow().isoformat()
    }
    
    current_feed.insert(0, post_with_meta)
    
    # Ограничиваем 100 постами
    if len(current_feed) > 100:
        current_feed = current_feed[:100]
    
    user_feeds_map.put(user_id, current_feed)
    return True

def get_user_feed(user_id: str) -> List[Dict[str, Any]]:
    """Получает ленту пользователя из кэша"""
    return user_feeds_map.get(user_id) or []

def update_likes_in_cache(post_id: str, likes_count: int) -> bool:
    """Обновляет счетчик лайков в кэше"""
    post_likes_map.put(post_id, likes_count)
    post_likes_map.set_ttl(post_id, 3600)  # TTL 1 час
    return True

def get_likes_from_cache(post_id: str) -> int:
    """Получает счетчик лайков из кэша"""
    return post_likes_map.get(post_id) or 0