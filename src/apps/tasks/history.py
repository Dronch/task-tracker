from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from simple_history.models import HistoricalChanges

from apps.users.models import User

if TYPE_CHECKING:
    from apps.tasks.models import Task

TaskHistoryEvent = Literal[
    "created",
    "changed",
    "completed",
    "reopened",
    "removed",
]


class TaskHistoryChange(TypedDict):
    field: str
    old: Any
    new: Any


class TaskHistoryEntry(TypedDict):
    occurred_at: datetime
    actor: User | None
    event: TaskHistoryEvent
    changes: list[TaskHistoryChange]


def get_task_history(task: Task) -> list[TaskHistoryEntry]:
    return build_task_history(list(task.history.for_events()))


def build_task_history(
    records: Sequence[HistoricalChanges],
) -> list[TaskHistoryEntry]:
    entries: list[TaskHistoryEntry] = []

    for index, record in enumerate(records):
        older_record = records[index + 1] if index + 1 < len(records) else None
        changes = get_history_changes(record, older_record)
        entries.append(
            {
                "occurred_at": record.history_date,
                "actor": record.history_user,
                "event": get_history_event(record, older_record, changes),
                "changes": changes,
            }
        )

    return entries


def get_history_changes(
    record: HistoricalChanges,
    older_record: HistoricalChanges | None,
) -> list[TaskHistoryChange]:
    if older_record is None:
        return []

    delta = record.diff_against(
        older_record,
        excluded_fields=("updated_at",),
    )
    return [
        {
            "field": change.field,
            "old": change.old,
            "new": change.new,
        }
        for change in delta.changes
    ]


def get_history_event(
    record: HistoricalChanges,
    older_record: HistoricalChanges | None,
    changes: list[TaskHistoryChange],
) -> TaskHistoryEvent:
    if older_record is None or record.history_type == "+":
        return "created"
    if record.history_type == "-":
        return "removed"

    changes_by_field = {change["field"]: change for change in changes}
    removed_at_change = changes_by_field.get("removed_at")
    if removed_at_change is not None and removed_at_change["new"] is not None:
        return "removed"

    completed_at_change = changes_by_field.get("completed_at")
    if completed_at_change is not None:
        was_completed = completed_at_change["old"] is not None
        is_completed = completed_at_change["new"] is not None
        if not was_completed and is_completed:
            return "completed"
        if was_completed and not is_completed:
            return "reopened"

    return "changed"
