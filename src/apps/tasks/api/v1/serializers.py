from rest_framework import serializers

from apps.tasks.models import Comment, Task
from apps.users.api.v1.fields import ActiveUserRelatedField
from apps.users.api.v1.serializers import UserSummarySerializer


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
