from django.urls import path
from .views import CreateOrganizationView

urlpatterns = [
    path('create/',CreateOrganizationView.as_view()),
]
