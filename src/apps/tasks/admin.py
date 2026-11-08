from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from simple_history.admin import SimpleHistoryAdmin

from .models import Comment, Task


class SoftDeleteHistoryAdmin(SimpleHistoryAdmin):
    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return self.model.all_objects.all()


@admin.register(Task)
class TaskAdmin(SoftDeleteHistoryAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "priority",
        "assignee",
        "completed_at",
        "removed_at",
    )
    list_filter = ("status", "priority", "completed_at", "removed_at")
    search_fields = ("title", "description")
    autocomplete_fields = ("creator", "assignee", "completed_by")
    readonly_fields = ("created_at", "updated_at", "removed_at")


@admin.register(Comment)
class CommentAdmin(SoftDeleteHistoryAdmin):
    list_display = ("id", "task", "author", "created_at", "removed_at")
    list_filter = ("created_at", "removed_at")
    search_fields = ("body",)
    autocomplete_fields = ("task", "author")
    readonly_fields = ("created_at", "updated_at", "removed_at")
