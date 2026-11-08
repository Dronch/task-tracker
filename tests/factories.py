import factory
from django.contrib.auth.hashers import make_password
from factory.django import DjangoModelFactory

from apps.tasks.models import Comment, Task
from apps.users.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda number: f"user-{number}")
    password = factory.LazyFunction(lambda: make_password("password"))


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda number: f"Task {number}")
    description = "Task description"
    creator = factory.SubFactory(UserFactory)
    assignee = None


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    task = factory.SubFactory(TaskFactory)
    author = factory.SubFactory(UserFactory)
    body = factory.Sequence(lambda number: f"Comment {number}")
