from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import QuerySet

from apps.tasks.models import Task
from apps.tasks.search import TASK_SEARCH_CONFIG, TASK_SEARCH_VECTOR


def search_tasks(queryset: QuerySet[Task], value: str) -> QuerySet[Task]:
    search_query = SearchQuery(
        value,
        config=TASK_SEARCH_CONFIG,
        search_type="plain",
    )
    return (
        queryset.annotate(
            search_vector=TASK_SEARCH_VECTOR,
            search_rank=SearchRank(TASK_SEARCH_VECTOR, search_query),
        )
        .filter(search_vector=search_query)
        .order_by("-search_rank", "-created_at")
    )
