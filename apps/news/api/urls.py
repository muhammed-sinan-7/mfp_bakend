from django.urls import path
from .views import IndustryNewsAPIView


urlpatterns = [
    path(
        "industry/",
        IndustryNewsAPIView.as_view(),
        name="industry-news",
    ),
]