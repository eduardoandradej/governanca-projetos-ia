"""Publica a versão 4 do template: ajustes orientados pela 1ª rodada da pesquisa com profissionais.

A v3 é descontinuada para novos projetos; projetos existentes permanecem na versão em que foram criados (T-027).
"""

from django.db import migrations


def forwards(apps, schema_editor):
    from apps.governance import catalog, catalog_pmbok
    from apps.lifecycle import default_template as dt

    dt.install(apps, number=4, stages=dt.stages_v4(), source_reference=dt.SOURCE_REFERENCE_V4,
               notes="Pesquisa rodada 1: F1-R1 (alternativas sem IA), F2-R1 (financiamento da infraestrutura), "
                     "F2-R6 (avaliação preliminar de uso responsável).")
    Version = apps.get_model("lifecycle", "LifecycleTemplateVersion")
    Version.objects.filter(template__organization__isnull=True, template__code=dt.TEMPLATE_CODE,
                           number__in=[1, 2, 3]).update(status="retired")
    catalog.install(apps)
    catalog_pmbok.install(apps)


class Migration(migrations.Migration):
    dependencies = [("governance", "0004_pmbok_catalog_and_template_v3")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
