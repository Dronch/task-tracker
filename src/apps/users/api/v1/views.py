from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.users.api.v1.serializers import LogoutSerializer, UserSummarySerializer
from apps.users.models import User


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LogoutSerializer

    @extend_schema(
        summary="Log out",
        description="Blacklists the authenticated user's refresh token.",
        request=LogoutSerializer,
        responses={
            204: None,
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Invalid refresh token.",
                examples=[
                    OpenApiExample(
                        "Invalid refresh token",
                        value={"refresh": ["Invalid or expired refresh token."]},
                        response_only=True,
                        status_codes=["400"],
                    ),
                ],
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(summary="List active users"),
    retrieve=extend_schema(summary="Retrieve an active user"),
)
class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True).order_by("username")
    serializer_class = UserSummarySerializer
