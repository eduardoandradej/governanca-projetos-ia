from django.db import migrations


def forwards(apps, schema_editor):
    from apps.analytics import metrics

    MetricDefinition = apps.get_model("analytics", "MetricDefinition")
    for d in metrics.DEFINITIONS:
        MetricDefinition.objects.update_or_create(code=d["code"], defaults={k: v for k, v in d.items() if k != "code"})


class Migration(migrations.Migration):
    dependencies = [("analytics", "0001_initial")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
