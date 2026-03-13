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

from .instagram_views import *
from .linkedin_views import *
from .youtube_views import *
urlpatterns = [
    path("", AnalyticsListView.as_view()),
    path("overview/", AnalyticsOverviewView.as_view()),
    path("engagement-chart/", EngagementChartView.as_view()),
    path("engagement-distribution/", EngagementDistributionAPIView.as_view()),
    path("recent-posts/", RecentPostsAPIView.as_view()),
    
     path("instagram/overview/", InstagramOverviewView.as_view()),
    path("instagram/growth/", InstagramGrowthChartView.as_view()),
    path("instagram/top-posts/", InstagramTopPostsView.as_view()),
    # path("analytics/instagram/gallery/", InstagramMediaGalleryView.as_view()),
    path("instagram/performance/", InstagramPostPerformanceView.as_view()),
    
    path("linkedin/overview/", LinkedInOverviewView.as_view()),
    path("linkedin/growth/", LinkedInGrowthChartView.as_view()),
    path("linkedin/posts/", LinkedInPostAnalyticsView.as_view()),
    
    path("youtube/overview/", YouTubeOverviewView.as_view()),
    path("youtube/growth/", YouTubeGrowthChartView.as_view()),
    path("youtube/videos/", YouTubeVideoAnalyticsView.as_view()),
    path("youtube/traffic-sources/", YouTubeTrafficSourcesView.as_view()),
    
    
]
