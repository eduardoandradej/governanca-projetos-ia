from django.db import migrations


def forwards(apps, schema_editor):
    from apps.lifecycle import default_template

    default_template.install(apps)


class Migration(migrations.Migration):
    dependencies = [("lifecycle", "0002_initial")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
