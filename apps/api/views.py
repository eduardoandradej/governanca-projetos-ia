"""API REST v1 (somente leitura + escrita seletiva). Mesma política de autorização do painel web (RN-002, T-023).

Autenticação: sessão Django (mesma origem). Escrita via API passa pelos MESMOS serviços de domínio, que validam
papel, escopo e segregação no servidor — a API nunca manipula regras críticas diretamente (T-026).
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from apps.analytics import metrics
from apps.analytics.services import scoped_projects
from apps.core.http import get_project_or_404
from apps.lifecycle.models import StageInstance
from apps.projects.models import Project
from apps.risks import services as risk_services
from apps.risks.models import DecisionRecord, Risk


class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StageInstance
        fields = ["id", "order", "code", "name", "status", "cobit_refs", "started_at", "approved_at",
                  "requires_responsible_ai"]


class ProjectSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source="organization.name")
    current_stage = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ["id", "code", "name", "organization", "status", "platform_type", "deployment_approach",
                  "development_approach", "ai_adoption_strategy", "priority", "criticality", "data_classification",
                  "start_date", "due_date", "current_stage", "updated_at"]

    def get_current_stage(self, obj):
        st = obj.current_stage
        return {"order": st.order, "name": st.name, "status": st.status} if st else None


class RiskSerializer(serializers.ModelSerializer):
    project = serializers.CharField(source="project.code")

    class Meta:
        model = Risk
        fields = ["id", "code", "project", "title", "category", "ai_category", "probability", "impact", "score",
                  "level", "status", "review_date"]


class DecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionRecord
        fields = ["id", "code", "version", "topic", "agenda", "alternatives", "decision", "rationale", "status",
                  "decided_at"]
        read_only_fields = ["id", "code", "version", "status", "decided_at"]


def _translate(exc):
    if isinstance(exc, PermissionDenied):
        raise DRFPermissionDenied(str(exc))
    if isinstance(exc, ValidationError):
        raise DRFValidationError(getattr(exc, "messages", [str(exc)]))
    if isinstance(exc, Http404):
        raise NotFound()
    raise exc


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        qs = scoped_projects(self.request.user).select_related("organization").order_by("code")
        for param, field in (("status", "status"), ("implantacao", "deployment_approach"),
                             ("plataforma", "platform_type")):
            if self.request.query_params.get(param):
                qs = qs.filter(**{field: self.request.query_params[param]})
        ordering = self.request.query_params.get("ordering")
        if ordering in ("code", "-code", "due_date", "-due_date", "updated_at", "-updated_at"):
            qs = qs.order_by(ordering)
        return qs

    @action(detail=True)
    def stages(self, request, pk=None):
        project = self.get_object()
        return Response(StageSerializer(project.stages.order_by("order"), many=True).data)

    @action(detail=True, methods=["get", "post"])
    def decisions(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            return Response(DecisionSerializer(project.decisions.all(), many=True).data)
        ser = DecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            rec = risk_services.propose_decision(actor=request.user, project=project, **ser.validated_data)
        except (PermissionDenied, ValidationError) as exc:
            _translate(exc)
        return Response(DecisionSerializer(rec).data, status=status.HTTP_201_CREATED)


class RiskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RiskSerializer

    def get_queryset(self):
        qs = Risk.objects.filter(project__in=scoped_projects(self.request.user)).select_related("project")
        if self.request.query_params.get("nivel"):
            qs = qs.filter(level=self.request.query_params["nivel"])
        return qs.order_by("-score", "code")


class DecisionViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = DecisionSerializer

    def get_queryset(self):
        return DecisionRecord.objects.filter(project__in=scoped_projects(self.request.user))

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        rec = self.get_object()
        try:
            rec = risk_services.decide(rec.pk, actor=request.user, approve=bool(request.data.get("approve")),
                                       note=str(request.data.get("note", "")))
        except (PermissionDenied, ValidationError) as exc:
            _translate(exc)
        return Response(DecisionSerializer(rec).data)


@api_view(["GET"])
def metrics_view(request):
    """Indicadores no escopo do usuário. Filtros: organizacao, projeto (validados contra o escopo)."""
    org_id = request.query_params.get("organizacao") or None
    project_id = request.query_params.get("projeto") or None
    if project_id:
        try:
            get_project_or_404(request.user, project_id)
        except Http404:
            raise NotFound() from None
    projects = scoped_projects(request.user, organization_id=org_id, project_id=project_id)
    data = []
    for code, r in metrics.compute_all(projects).items():
        d = metrics.DEFINITIONS_BY_CODE[code]
        data.append({"code": code, "name": d["name"], "unit": d["unit"], "indicator_type": d["indicator_type"],
                     "value": None if r.value is None else str(r.value),
                     "numerator": None if r.numerator is None else str(r.numerator),
                     "denominator": None if r.denominator is None else str(r.denominator),
                     "details": r.details, "lineage": r.lineage})
    return Response({"scope": {"projects": projects.count(), "organizacao": org_id, "projeto": project_id},
                     "metrics": data})
