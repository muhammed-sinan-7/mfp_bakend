from rest_framework import serializers
from ..models import NewsArticle


class NewsArticleSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name")

    class Meta:
        model = NewsArticle
        fields = [
            "id",
            "title",
            "summary",
            "url",
            "image",
            "source",
            "published_at",
        ]
