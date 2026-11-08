from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.users.api.v1.views import LogoutView, UserViewSet

app_name = "users"

router = SimpleRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    *router.urls,
]
