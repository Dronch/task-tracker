from __future__ import annotations

from typing import TYPE_CHECKING, Self

from django.db import models, transaction

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser


class SoftDeleteQuerySet(models.QuerySet):
    def active(self) -> Self:
        return self.filter(removed_at__isnull=True)

    def removed(self) -> Self:
        return self.filter(removed_at__isnull=False)

    def soft_delete(self, *, history_user: AbstractBaseUser | None = None) -> int:
        deleted_count = 0

        with transaction.atomic(using=self.db):
            queryset = self.select_for_update()
            for instance in queryset.iterator():
                deleted_count += instance.soft_delete(
                    using=self.db,
                    history_user=history_user,
                )

        return deleted_count

    def delete(self) -> tuple[int, dict[str, int]]:
        deleted_count = self.soft_delete()
        return deleted_count, {self.model._meta.label: deleted_count}
