from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
from app.services.search_service import search_posts, aggregate_tags_by_date

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/")
async def api_search(
    query: str = Query(..., min_length=1, description="Поисковый запрос"),
    limit: int = Query(10, ge=1, le=100, description="Лимит результатов")
):
    """Поиск по постам"""
    try:
        results = search_posts(query, limit)
        
        formatted_results = []
        for hit in results:
            source = hit.get("_source", {})
            formatted_results.append({
                "id": hit.get("_id"),
                "text": source.get("text", "")[:200] + "..." if len(source.get("text", "")) > 200 else source.get("text", ""),
                "tags": source.get("tags", []),
                "user_id": source.get("user_id", ""),
                "score": hit.get("_score", 0)
            })
        
        return {
            "query": query,
            "total": len(results),
            "results": formatted_results
        }
    except Exception as e:
        return {
            "query": query,
            "total": 0,
            "results": [],
            "note": "Поиск временно недоступен"
        }

@router.get("/trends")
async def api_get_trends(
    date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD")
):
    """Популярные теги"""
    try:
        trends = aggregate_tags_by_date(date)
        
        return {
            "date": date or "последняя неделя",
            "trends": trends,
            "total": len(trends)
        }
    except Exception as e:
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "trends": [
                {"tag": "python", "count": 150},
                {"tag": "mongodb", "count": 89},
                {"tag": "fastapi", "count": 76}
            ],
            "note": "Демо-данные"
        }