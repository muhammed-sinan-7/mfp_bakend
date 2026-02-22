from django.urls import path
from .views import (RequestEmailVerificationOTPView,
                    RegisterUserView,
                    VerifyEmailOTPView,
                    LoginView,
                    TestDashboardView,CustomTokenRefreshView)
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('request-email-verification-otp/',RequestEmailVerificationOTPView.as_view()),
    path('verify-email-otp/',VerifyEmailOTPView.as_view()),
    path('register/',RegisterUserView.as_view()),
    path('login/',LoginView.as_view()),
    path('token/refresh/',CustomTokenRefreshView.as_view(),name="token_refresh"),
    path("test-dashboard/", TestDashboardView.as_view()),
]
