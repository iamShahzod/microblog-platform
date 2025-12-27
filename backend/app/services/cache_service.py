import hazelcast
import json

client = hazelcast.HazelcastClient(cluster_members=["localhost:5701"])
feed_map = client.get_map("user_feeds").blocking()

def add_to_feed(user_id: str, post: dict):
    """Добавляет пост в ленту пользователя"""
    # Получаем текущую ленту
    current_feed = feed_map.get(user_id)
    if not current_feed:
        current_feed = []
    
    # Добавляем новый пост в начало
    current_feed.insert(0, post)
    
    # Ограничиваем 100 постами
    if len(current_feed) > 100:
        current_feed = current_feed[:100]
    
    # Сохраняем обратно
    feed_map.put(user_id, current_feed)

def get_feed(user_id: str):
    """Получает ленту пользователя"""
    return feed_map.get(user_id) or []