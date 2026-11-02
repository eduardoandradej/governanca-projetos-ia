from django.db import models

from apps.core.models import BaseModel


class IntegrationEndpoint(BaseModel):
    """Configuração FUTURA de integração. Sempre desativada no MVP; não armazena segredos (apenas a referência
    ao nome da variável/cofre onde a credencial ficará)."""

    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="+")
    kind = models.CharField(max_length=20, choices=[
        ("cicd", "GitLab/GitHub"), ("automation", "Ansible/AAP"), ("deployment", "Kubernetes/OpenShift"),
        ("observability", "Observabilidade"), ("storage", "S3/MinIO"),
    ])
    name = models.CharField(max_length=120)
    base_url = models.URLField(blank=True)
    credential_ref = models.CharField("referência da credencial (cofre/variável)", max_length=120, blank=True)
    read_only = models.BooleanField(default=True)
    enabled = models.BooleanField(default=False, editable=False)

    class Meta:
        verbose_name = "endpoint de integração (futuro)"
        constraints = [models.CheckConstraint(condition=models.Q(enabled=False), name="integration_disabled_in_mvp")]
