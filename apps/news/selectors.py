from .models import NewsArticle


def get_industry_news(industry_id, limit=10):
    
    return (
        NewsArticle.objects
        .select_related("source")
        .filter(industry_id=industry_id)
        .order_by("-published_at")[:limit]
    )