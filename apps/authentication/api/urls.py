from django.urls import path
from .views import (RequestEmailOTPView,
                    RegisterUserView,
                    VerifyEmailOTPView,
                    LoginView,
                    CustomTokenRefreshView,
                    LogoutView
    )
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('request-email-verification-otp/',RequestEmailOTPView.as_view()),
    path('verify-email-otp/',VerifyEmailOTPView.as_view()),
    
    path('register/',RegisterUserView.as_view()),
    path('login/',LoginView.as_view()),
    path('token/refresh/',CustomTokenRefreshView.as_view(),name="token_refresh"),
    path('logout/', LogoutView.as_view(), name="logout"),
    # path("test-dashboard/", TestDashboardView.as_view()),
]
