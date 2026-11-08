from typing import Any

from rest_framework import serializers

from apps.users.api.v1.serializers import UserSummarySerializer
from apps.users.models import User


class ActiveUserRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("queryset", User.objects.filter(is_active=True))
        kwargs.setdefault("allow_null", True)
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def use_pk_only_optimization(self) -> bool:
        return False

    def to_representation(self, value: User) -> dict[str, Any]:
        return UserSummarySerializer(value).data
