"""Instala o catálogo COBIT (com base em ISACA 2025) e publica a versão 2 do template de 7 fases.

A versão 1 é marcada como descontinuada para NOVOS projetos; projetos existentes permanecem na v1 (T-027).
"""

from django.db import migrations


def forwards(apps, schema_editor):
    from apps.governance import catalog
    from apps.lifecycle import default_template as dt

    dt.install(
        apps, number=2, stages=dt.stages_v2(), source_reference=dt.SOURCE_REFERENCE_V2,
        notes="Inclui requisitos derivados do white paper ISACA (2025) sobre governança de sistemas de IA.",
    )
    Version = apps.get_model("lifecycle", "LifecycleTemplateVersion")
    Version.objects.filter(template__organization__isnull=True, template__code=dt.TEMPLATE_CODE, number=1).update(
        status="retired"
    )
    catalog.install(apps)


class Migration(migrations.Migration):
    dependencies = [("governance", "0001_initial"), ("lifecycle", "0004_task_team_label")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
