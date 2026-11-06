from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import migrations

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor

READ_ONLY_GROUP_NAME = "read_only"


def create_read_only_group(
    apps: Apps,
    schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    group = apps.get_model("auth", "Group")
    group.objects.get_or_create(name=READ_ONLY_GROUP_NAME)


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(
            create_read_only_group,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
