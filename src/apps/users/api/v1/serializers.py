from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def validate_refresh(self, value: str) -> str:
        try:
            token = RefreshToken(value)
        except TokenError as error:
            raise serializers.ValidationError(
                "Invalid or expired refresh token."
            ) from error

        request = self.context["request"]
        token_user_id = token.get(api_settings.USER_ID_CLAIM)
        request_user_id = getattr(request.user, api_settings.USER_ID_FIELD)

        if token_user_id is None or str(token_user_id) != str(request_user_id):
            raise serializers.ValidationError(
                "Refresh token does not belong to the authenticated user."
            )

        return value

    def blacklist(self) -> None:
        refresh = self.validated_data["refresh"]
        token = RefreshToken(refresh)
        token.blacklist()
