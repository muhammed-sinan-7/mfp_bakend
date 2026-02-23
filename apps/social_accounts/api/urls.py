from django.urls import path
from .views import MetaConnectView, MetaCallbackView

urlpatterns = [
    path("meta/connect/", MetaConnectView.as_view(), name="meta-connect"),
    path("meta/callback/", MetaCallbackView.as_view(), name="meta-callback"),
]