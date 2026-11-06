from django.db import models

from .querysets import SoftDeleteQuerySet


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self) -> SoftDeleteQuerySet:
        return super().get_queryset().active()


class AllObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass
