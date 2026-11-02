"""Publica a versão 3 do template (PMBOK 8 X3 + 4.2) e instala referências PMBOK 8 separadas do COBIT.

A v2 é descontinuada para novos projetos; projetos existentes permanecem na versão em que foram criados.
"""

from django.db import migrations


def forwards(apps, schema_editor):
    from apps.governance import catalog, catalog_pmbok
    from apps.lifecycle import default_template as dt

    dt.install(apps, number=3, stages=dt.stages_v3(), source_reference=dt.SOURCE_REFERENCE_V3,
               notes="Inclui avaliação de uso responsável de IA (PMBOK 8 X3.3) no gate da fase 6 e F1-R6.")
    Version = apps.get_model("lifecycle", "LifecycleTemplateVersion")
    Version.objects.filter(template__organization__isnull=True, template__code=dt.TEMPLATE_CODE,
                           number__in=[1, 2]).update(status="retired")
    catalog.install(apps)  # mapeia COBIT também para os requisitos novos da v3
    catalog_pmbok.install(apps)


class Migration(migrations.Migration):
    dependencies = [("governance", "0003_frameworkreference_frameworkmapping_and_more"), ("lifecycle", "0005_stageinstance_requires_responsible_ai_and_more"), ("projects", "0002_project_ai_adoption_strategy_and_more")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
