from typing import Self

from django.contrib.postgres.search import SearchQuery, SearchRank
from simple_history.manager import HistoricalQuerySet

from apps.common.querysets import SoftDeleteQuerySet
from apps.tasks.search import TASK_SEARCH_CONFIG, TASK_SEARCH_VECTOR


class TaskQuerySet(SoftDeleteQuerySet):
    def search(self, value: str) -> Self:
        search_query = SearchQuery(
            value,
            config=TASK_SEARCH_CONFIG,
            search_type="plain",
        )
        return (
            self.annotate(
                search_vector=TASK_SEARCH_VECTOR,
                search_rank=SearchRank(TASK_SEARCH_VECTOR, search_query),
            )
            .filter(search_vector=search_query)
            .order_by("-search_rank", "-created_at")
        )


class TaskHistoricalQuerySet(HistoricalQuerySet):
    def for_events(self) -> Self:
        return self.select_related("history_user").order_by(
            "-history_date",
            "-history_id",
        )
