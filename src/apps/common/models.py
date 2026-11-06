from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from django.db import models
from django.utils import timezone

from .managers import AllObjectsManager, SoftDeleteManager

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser


class TimeStampedSoftDeleteModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    removed_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        base_manager_name = "all_objects"
        default_manager_name = "objects"
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=("removed_at",),
                name="%(app_label)s_%(class)s_rm_idx",
            ),
        ]

    def soft_delete(
        self,
        *,
        using: str | None = None,
        history_user: AbstractBaseUser | None = None,
    ) -> bool:
        if self.removed_at is not None:
            return False

        self.removed_at = timezone.now()
        if history_user is not None:
            self._history_user = history_user
        self.save(using=using, update_fields=("removed_at", "updated_at"))
        return True

    def delete(
        self,
        using: str | None = None,
        keep_parents: bool = False,
    ) -> tuple[int, dict[str, int]]:
        deleted = self.soft_delete(using=using)
        deleted_count = int(deleted)
        return deleted_count, {self._meta.label: deleted_count}
