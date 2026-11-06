from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.permissions import SAFE_METHODS, BasePermission

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView

READ_ONLY_GROUP_NAME = "read_only"


class IsAuthenticatedAndWritable(BasePermission):
    message = "Users in the read_only group cannot modify resources."

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user

        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS or user.is_superuser:
            return True

        return not user.groups.filter(name=READ_ONLY_GROUP_NAME).exists()
