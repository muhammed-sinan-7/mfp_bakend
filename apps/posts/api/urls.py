from django.urls import path
from .views import PostCreateAPIView,PostDeleteView,PostRestoreView,PostDetailView,PostListView,RecycleBinListView,PostUpdateView

urlpatterns = [
    path("", PostListView.as_view()),
    path("create/", PostCreateAPIView.as_view()),
    path("<uuid:pk>/delete/", PostDeleteView.as_view()),
    path("<uuid:pk>/", PostDetailView.as_view()), 
    path("<uuid:pk>/edit/", PostUpdateView.as_view()),
    path("<uuid:pk>/restore/", PostRestoreView.as_view()),
    path("recycle-bin/", RecycleBinListView.as_view()),
]