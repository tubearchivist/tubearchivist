"""custom migration to copy CustomPeriodicTask to new task app"""

from django.db import migrations

def copy_data(apps, schema_editor):
    """copy between apps"""

    OldCustomPeriodicTask = apps.get_model("home", "CustomPeriodicTask")
    NewCustomPeriodicTask = apps.get_model("task", "CustomPeriodicTask")

    for old_instance in OldCustomPeriodicTask.objects.all():
        field_data = {
            field.name: getattr(old_instance, field.name)
            for field in OldCustomPeriodicTask._meta.fields
        }
        field_data.pop("id", None)
        new_instance = NewCustomPeriodicTask(**field_data)
        new_instance.save()


class Migration(migrations.Migration):
    """migration"""

    dependencies = [
        ("task", "0001_initial"),
        ("home", "0002_customperiodictask"),
    ]

    operations = [
        migrations.RunPython(copy_data),
    ]
