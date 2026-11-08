from simple_history.manager import HistoryManager

from apps.common.managers import AllObjectsManager, SoftDeleteManager
from apps.tasks.querysets import TaskHistoricalQuerySet, TaskQuerySet


class TaskManager(SoftDeleteManager.from_queryset(TaskQuerySet)):
    pass


class AllTasksManager(AllObjectsManager.from_queryset(TaskQuerySet)):
    pass


class TaskHistoryManager(HistoryManager):
    def for_events(self) -> TaskHistoricalQuerySet:
        return self.get_queryset().for_events()
