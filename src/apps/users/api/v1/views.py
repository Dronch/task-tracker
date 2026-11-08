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

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True).order_by("username")
    serializer_class = UserSummarySerializer
