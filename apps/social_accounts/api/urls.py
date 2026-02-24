from django.urls import path
from .views import( MetaConnectView, MetaCallbackView,
                   LinkedInCallbackView,LinkedInConnectView,
                   SocialAccountListView)

urlpatterns = [
    
    path("", SocialAccountListView.as_view()),
    path("meta/connect/", MetaConnectView.as_view()),
    path("meta/callback/", MetaCallbackView.as_view()),
    path("linkedin/connect/", LinkedInConnectView.as_view()),
    path("linkedin/callback/", LinkedInCallbackView.as_view()),
]