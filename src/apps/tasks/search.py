from django.contrib.postgres.search import SearchVector

TASK_SEARCH_CONFIG = "simple"
TASK_SEARCH_VECTOR = SearchVector(
    "title",
    config=TASK_SEARCH_CONFIG,
    weight="A",
) + SearchVector(
    "description",
    config=TASK_SEARCH_CONFIG,
    weight="B",
)
