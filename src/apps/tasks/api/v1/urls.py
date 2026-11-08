from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.tasks.api.v1.views import CommentViewSet, TaskViewSet

app_name = "tasks"

router = SimpleRouter()
router.register("tasks", TaskViewSet, basename="task")

comment_list = CommentViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)
comment_detail = CommentViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)

urlpatterns = [
    path(
        "tasks/<int:task_id>/comments/",
        comment_list,
        name="comment-list",
    ),
    path(
        "tasks/<int:task_id>/comments/<int:pk>/",
        comment_detail,
        name="comment-detail",
    ),
    *router.urls,
]
