from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.organizations.mixins import OrganizationContextMixin
from ..selectors import get_industry_news
from .serializers import NewsArticleSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from apps.ai.services.llm_service import AIService
from ..models import NewsArticle
from django.shortcuts import get_object_or_404
# Create your views here.
@method_decorator(cache_page(60*5), name='dispatch')
class IndustryNewsAPIView(OrganizationContextMixin, APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        org = request.organization

        if not org or not org.industry:
            return Response([])

        page = int(request.query_params.get("page", 1))

        articles = get_industry_news(
            industry_id=org.industry_id,
            page=page,
            limit=10
        )

        serializer = NewsArticleSerializer(articles, many=True)

        return Response(serializer.data)
    
# class NewsSummaryAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, pk):

#         article = get_object_or_404(NewsArticle, id=pk)

#         ai = AIService()

#         prompt = f"""
# Summarize this news article in a concise, clear, professional way.

# Title: {article.title}

# Content:
# {article.summary}

# Rules:
# - 10–30 lines
# - No fluff
# - Easy to read
# - Keep key insights
# """

#         result = ai.chat([{"role": "user", "content": prompt}])

#         return Response({
#             "summary": result.get("response", ""),
#             "url": article.url
#         })