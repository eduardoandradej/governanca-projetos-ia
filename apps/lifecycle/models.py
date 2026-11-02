"""Ciclo de vida de sete fases com templates versionados, requisitos, tarefas e equipes (F02/F03).

Templates são versionados: um projeto é instanciado a partir de uma versão PUBLICADA, e as fases e
requisitos são COPIADOS (snapshot) para as instâncias. Assim, novas versões de template não alteram
retroativamente projetos já iniciados (T-027).
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel


class LifecycleTemplate(BaseModel):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT, null=True, blank=True, related_name="lifecycle_templates",
        help_text="Vazio = template padrão do sistema, disponível a todas as organizações.",
    )
    code = models.SlugField("código", max_length=60)
    name = models.CharField("nome", max_length=150)
    description = models.TextField("descrição", blank=True)

    class Meta:
        verbose_name = "template de ciclo de vida"
        verbose_name_plural = "templates de ciclo de vida"
        constraints = [
            models.UniqueConstraint(fields=["organization", "code"], name="uniq_lifecycle_template_org_code"),
            models.UniqueConstraint(
                fields=["code"], condition=Q(organization__isnull=True), name="uniq_lifecycle_template_system_code"
            ),
        ]

    def __str__(self):
        return self.name


class TemplateVersionStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    PUBLISHED = "published", "Publicada"
    RETIRED = "retired", "Descontinuada"


class LifecycleTemplateVersion(BaseModel):
    template = models.ForeignKey(LifecycleTemplate, on_delete=models.PROTECT, related_name="versions")
    number = models.PositiveIntegerField("versão")
    status = models.CharField(max_length=12, choices=TemplateVersionStatus.choices, default=TemplateVersionStatus.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    source_reference = models.CharField(
        "fonte bibliográfica", max_length=255, blank=True,
        help_text="Ex.: ISACA COBIT 2019; PMI PMBOK 8ª ed. Associação = interpretação da equipe, não certificação.",
    )
    notes = models.TextField("notas da versão", blank=True)

    class Meta:
        ordering = ["template", "-number"]
        verbose_name = "versão de template de ciclo de vida"
        verbose_name_plural = "versões de template de ciclo de vida"
        constraints = [models.UniqueConstraint(fields=["template", "number"], name="uniq_template_version_number")]

    def __str__(self):
        return f"{self.template.name} v{self.number}"


class StageTemplate(models.Model):
    template_version = models.ForeignKey(LifecycleTemplateVersion, on_delete=models.PROTECT, related_name="stages")
    order = models.PositiveSmallIntegerField("ordem")
    code = models.SlugField("código", max_length=40)
    name = models.CharField("nome", max_length=150)
    objective = models.TextField("objetivo")
    description = models.TextField("descrição", blank=True)
    cobit_refs = models.CharField("objetivos COBIT 2019 (interpretação)", max_length=120, blank=True)
    pmbok_refs = models.CharField("referências PMBOK (interpretação)", max_length=200, blank=True)
    requires_segregation = models.BooleanField("exige segregação solicitante ≠ aprovador", default=True)
    block_on_critical_risk = models.BooleanField("bloqueia gate com risco crítico não tratado", default=True)
    has_exit_gate = models.BooleanField("possui gate de saída", default=True)

    class Meta:
        ordering = ["template_version", "order"]
        verbose_name = "template de fase"
        verbose_name_plural = "templates de fase"
        constraints = [
            models.UniqueConstraint(fields=["template_version", "order"], name="uniq_stage_template_order"),
            models.UniqueConstraint(fields=["template_version", "code"], name="uniq_stage_template_code"),
        ]

    def __str__(self):
        return f"{self.order}. {self.name}"


class EvidenceKind(models.TextChoices):
    BUSINESS_CASE = "business_case", "Caso de negócio"
    PLAN = "plan", "Plano"
    ARCHITECTURE = "architecture", "Arquitetura"
    ACCEPTANCE = "acceptance", "Termo de aceite"
    RISK_ANALYSIS = "risk_analysis", "Análise de risco"
    TEST = "test", "Teste"
    SECURITY_REPORT = "security_report", "Relatório de segurança"
    DATA_VALIDATION = "data_validation", "Validação de dados"
    BACKUP_RECOVERY = "backup_recovery", "Backup/recuperação"
    APPROVAL = "approval", "Aprovação"
    OTHER = "other", "Outro"


class RequirementTemplate(models.Model):
    stage_template = models.ForeignKey(StageTemplate, on_delete=models.PROTECT, related_name="requirements")
    order = models.PositiveSmallIntegerField("ordem", default=0)
    code = models.CharField("código", max_length=30)
    title = models.CharField("requisito", max_length=200)
    description = models.TextField("critério de aceite", blank=True)
    mandatory = models.BooleanField("obrigatório", default=True)
    requires_evidence = models.BooleanField("exige evidência aprovada", default=False)
    evidence_kind = models.CharField(max_length=20, choices=EvidenceKind.choices, blank=True)
    requires_validation = models.BooleanField("exige validação humana", default=True)
    is_legal = models.BooleanField(
        "requisito legal (não admite exceção)", default=False,
        help_text="Exceções formais NUNCA dispensam requisitos legais obrigatórios.",
    )
    cobit_ref = models.CharField("objetivo COBIT relacionado", max_length=20, blank=True)

    class Meta:
        ordering = ["stage_template", "order"]
        verbose_name = "template de requisito"
        verbose_name_plural = "templates de requisito"
        constraints = [models.UniqueConstraint(fields=["stage_template", "code"], name="uniq_requirement_template_code")]

    def __str__(self):
        return f"{self.code} {self.title}"


class StageStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Não iniciada"
    IN_PROGRESS = "in_progress", "Em andamento"
    SUBMITTED = "submitted", "Submetida à revisão"
    RETURNED = "returned", "Devolvida"
    APPROVED = "approved", "Aprovada"
    COMPLETED = "completed", "Concluída"


# Máquina de estados das fases (transições válidas).
STAGE_TRANSITIONS: dict[str, set[str]] = {
    StageStatus.NOT_STARTED: {StageStatus.IN_PROGRESS},
    StageStatus.IN_PROGRESS: {StageStatus.SUBMITTED, StageStatus.COMPLETED},
    StageStatus.SUBMITTED: {StageStatus.APPROVED, StageStatus.RETURNED, StageStatus.IN_PROGRESS},
    StageStatus.RETURNED: {StageStatus.IN_PROGRESS, StageStatus.SUBMITTED},
    StageStatus.APPROVED: {StageStatus.COMPLETED},
    StageStatus.COMPLETED: set(),
}


class StageInstance(BaseModel):
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="stages")
    stage_template = models.ForeignKey(StageTemplate, on_delete=models.PROTECT, related_name="instances")
    # Snapshot dos atributos do template no momento da instanciação (T-027).
    order = models.PositiveSmallIntegerField("ordem")
    code = models.SlugField(max_length=40)
    name = models.CharField("fase", max_length=150)
    objective = models.TextField("objetivo")
    cobit_refs = models.CharField(max_length=120, blank=True)
    requires_segregation = models.BooleanField(default=True)
    block_on_critical_risk = models.BooleanField(default=True)
    has_exit_gate = models.BooleanField(default=True)
    status = models.CharField(max_length=12, choices=StageStatus.choices, default=StageStatus.NOT_STARTED)
    planned_start = models.DateField("início planejado", null=True, blank=True)
    planned_end = models.DateField("término planejado", null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["project", "order"]
        verbose_name = "fase do projeto"
        verbose_name_plural = "fases do projeto"
        constraints = [
            models.UniqueConstraint(fields=["project", "order"], name="uniq_stage_project_order"),
            models.CheckConstraint(condition=Q(order__gte=1), name="stage_order_positive"),
        ]

    def __str__(self):
        return f"{self.order}. {self.name}"


class StageStatusHistory(models.Model):
    stage = models.ForeignKey(StageInstance, on_delete=models.PROTECT, related_name="history")
    created_at = models.DateTimeField(auto_now_add=True)
    from_status = models.CharField(max_length=12, choices=StageStatus.choices, blank=True)
    to_status = models.CharField(max_length=12, choices=StageStatus.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+")
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]


class RequirementStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    FULFILLED = "fulfilled", "Atendido (aguarda validação)"
    VALIDATED = "validated", "Validado"
    REJECTED = "rejected", "Recusado na validação"


class RequirementInstance(BaseModel):
    stage = models.ForeignKey(StageInstance, on_delete=models.PROTECT, related_name="requirements")
    template = models.ForeignKey(RequirementTemplate, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    order = models.PositiveSmallIntegerField(default=0)
    code = models.CharField(max_length=30)
    title = models.CharField("requisito", max_length=200)
    description = models.TextField("critério de aceite", blank=True)
    mandatory = models.BooleanField(default=True)
    requires_evidence = models.BooleanField(default=False)
    evidence_kind = models.CharField(max_length=20, choices=EvidenceKind.choices, blank=True)
    requires_validation = models.BooleanField(default=True)
    is_legal = models.BooleanField(default=False)
    cobit_ref = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=12, choices=RequirementStatus.choices, default=RequirementStatus.PENDING)
    fulfillment_note = models.TextField("registro de atendimento", blank=True)
    fulfilled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["stage", "order"]
        verbose_name = "requisito da fase"
        verbose_name_plural = "requisitos da fase"
        constraints = [models.UniqueConstraint(fields=["stage", "code"], name="uniq_requirement_stage_code")]

    def __str__(self):
        return f"{self.code} {self.title}"


class ValidationDecision(models.TextChoices):
    APPROVED = "approved", "Validado"
    REJECTED = "rejected", "Recusado"


class RequirementValidation(models.Model):
    requirement = models.ForeignKey(RequirementInstance, on_delete=models.PROTECT, related_name="validations")
    created_at = models.DateTimeField(auto_now_add=True)
    validator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    decision = models.CharField(max_length=10, choices=ValidationDecision.choices)
    comment = models.TextField("parecer")
    requirement_version = models.PositiveIntegerField()

    class Meta:
        ordering = ["-created_at"]


class Team(BaseModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="teams")
    name = models.CharField("equipe", max_length=120)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="teams")

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["organization", "name"], name="uniq_team_org_name")]

    def __str__(self):
        return self.name


class TaskStatus(models.TextChoices):
    TODO = "todo", "A fazer"
    DOING = "doing", "Em andamento"
    BLOCKED = "blocked", "Bloqueada"
    DONE = "done", "Concluída"


class Task(BaseModel):
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="tasks")
    stage = models.ForeignKey(StageInstance, on_delete=models.PROTECT, related_name="tasks")
    team = models.ForeignKey(
        Team, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks", verbose_name="equipe"
    )
    title = models.CharField("tarefa", max_length=200)
    description = models.TextField("descrição", blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="tasks",
        verbose_name="responsável",
    )
    due_date = models.DateField("prazo", null=True, blank=True)
    priority = models.CharField(
        "prioridade", max_length=10,
        choices=[("low", "Baixa"), ("medium", "Média"), ("high", "Alta"), ("critical", "Crítica")], default="medium",
    )
    status = models.CharField(max_length=10, choices=TaskStatus.choices, default=TaskStatus.TODO)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["stage__order", "due_date", "title"]
        verbose_name = "tarefa"
        verbose_name_plural = "tarefas"
        indexes = [models.Index(fields=["project", "status"]), models.Index(fields=["due_date"])]

    def __str__(self):
        return self.title


class TaskDependency(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="dependencies")
    depends_on = models.ForeignKey(Task, on_delete=models.PROTECT, related_name="dependents")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "depends_on"], name="uniq_task_dependency"),
            models.CheckConstraint(condition=~Q(task=models.F("depends_on")), name="task_dependency_not_self"),
        ]


class RaciRole(models.TextChoices):
    RESPONSIBLE = "R", "Responsável"
    ACCOUNTABLE = "A", "Aprovador"
    CONSULTED = "C", "Consultado"
    INFORMED = "I", "Informado"


class RaciAssignment(models.Model):
    """Matriz RACI por entregável (requisito da fase). Não concede permissão de sistema."""

    requirement = models.ForeignKey(RequirementInstance, on_delete=models.CASCADE, related_name="raci")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    raci = models.CharField(max_length=1, choices=RaciRole.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["requirement", "user", "raci"], name="uniq_raci"),
            models.UniqueConstraint(
                fields=["requirement"], condition=Q(raci="A"), name="uniq_raci_single_accountable"
            ),
        ]
