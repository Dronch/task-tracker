from typing import Any

from rest_framework import serializers

from apps.tasks.models import Comment, Task
from apps.users.api.v1.fields import ActiveUserRelatedField
from apps.users.api.v1.serializers import UserSummarySerializer


class TaskHistoryChangeSerializer(serializers.Serializer):
    field = serializers.CharField()
    old = serializers.JSONField(allow_null=True)
    new = serializers.JSONField(allow_null=True)


class TaskHistoryEntrySerializer(serializers.Serializer):
    occurred_at = serializers.DateTimeField()
    actor = UserSummarySerializer(allow_null=True)
    event = serializers.ChoiceField(
        choices=("created", "changed", "completed", "reopened", "removed"),
    )
    changes = TaskHistoryChangeSerializer(many=True)


class TaskSerializer(serializers.ModelSerializer):
    creator = UserSummarySerializer(read_only=True)
    assignee = ActiveUserRelatedField()
    completed_by = UserSummarySerializer(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "status",
            "priority",
            "creator",
            "assignee",
            "due_date",
            "completed_at",
            "completed_by",
            "created_at",
            "updated_at",
            "removed_at",
        )
        read_only_fields = (
            "id",
            "creator",
            "completed_at",
            "completed_by",
            "created_at",
            "updated_at",
            "removed_at",
        )

    def validate_title(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def create(self, validated_data: dict[str, Any]) -> Task:
        history_user = validated_data.pop("_history_user", None)
        task = Task(**validated_data)
        task._history_user = history_user
        task.save()
        return task

    def update(self, instance: Task, validated_data: dict[str, Any]) -> Task:
        instance._history_user = validated_data.pop("_history_user", None)
        return super().update(instance, validated_data)


class CommentSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(read_only=True)
    author = UserSummarySerializer(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "task",
            "author",
            "body",
            "created_at",
            "updated_at",
            "removed_at",
        )
        read_only_fields = (
            "id",
            "task",
            "author",
            "created_at",
            "updated_at",
            "removed_at",
        )

    def validate_body(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Comment body cannot be blank.")
        return value

    def create(self, validated_data: dict[str, Any]) -> Comment:
        history_user = validated_data.pop("_history_user", None)
        comment = Comment(**validated_data)
        comment._history_user = history_user
        comment.save()
        return comment

    def update(self, instance: Comment, validated_data: dict[str, Any]) -> Comment:
        instance._history_user = validated_data.pop("_history_user", None)
        return super().update(instance, validated_data)
