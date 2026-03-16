from django.urls import path
from .views import AITestView,GeneratePostView

urlpatterns = [
    path('test/',AITestView.as_view()),
    path('generate-post/',GeneratePostView.as_view()),
]
