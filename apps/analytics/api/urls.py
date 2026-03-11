from django.urls import path
from .views import (
    AnalyticsListView,
    AnalyticsOverviewView,
    TopPostsAnalyticsView,
    PlatformAnalyticsView,
    EngagementChartView,
    EngagementDistributionAPIView,
    RecentPostsAPIView
)

urlpatterns = [
    path("", AnalyticsListView.as_view()),
    path("overview/", AnalyticsOverviewView.as_view()),
    path("top-posts/", TopPostsAnalyticsView.as_view()),
    path("platform-performance/", PlatformAnalyticsView.as_view()),
    path("engagement-chart/", EngagementChartView.as_view()),
    path("engagement-distribution/", EngagementDistributionAPIView.as_view()),
    path("recent-posts/", RecentPostsAPIView.as_view()),
]
